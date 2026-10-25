"""Database manager for AutoAffiliate AI.
Handles local SQLite storage for products, generated posts, engagement actions, revenue metrics, and agent activity logs.
"""

import sqlite3
import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "autoaffiliate.db")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

get_db = get_db_connection


def init_db():
    """Initializes all necessary tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE,
        platform TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT,
        original_price REAL,
        deal_price REAL,
        discount_pct REAL,
        rating REAL,
        reviews_count INTEGER,
        image_url TEXT,
        image_urls TEXT,
        source_url TEXT NOT NULL,
        affiliate_url TEXT NOT NULL,
        status TEXT DEFAULT 'scouted',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN image_urls TEXT")
    except Exception:
        pass

    # 2. Posts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        platform TEXT NOT NULL,
        post_type TEXT NOT NULL,
        headline TEXT,
        caption TEXT NOT NULL,
        hashtags TEXT,
        media_paths TEXT,
        video_path TEXT,
        status TEXT DEFAULT 'draft',
        scheduled_time TIMESTAMP,
        published_time TIMESTAMP,
        external_post_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """)

    # Column migration for existing databases
    try:
        cursor.execute("ALTER TABLE posts ADD COLUMN video_path TEXT")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE posts ADD COLUMN media_purged INTEGER DEFAULT 0")
    except Exception:
        pass

    # 3. Engagement Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS engagement_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_account TEXT,
        target_post_url TEXT,
        action_type TEXT NOT NULL,
        content TEXT,
        status TEXT DEFAULT 'pending',
        executed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Daily Revenue & Target Tracker
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_revenue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_date DATE UNIQUE NOT NULL,
        target_inr REAL DEFAULT 500.0,
        estimated_earnings_inr REAL DEFAULT 0.0,
        clicks INTEGER DEFAULT 0,
        orders INTEGER DEFAULT 0,
        notes TEXT
    );
    """)

    # 5. Agent Activity Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        action TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


# ---------------- PRODUCT REPO ----------------
def save_product(product: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    imgs = product.get("image_urls") or ([product.get("image_url")] if product.get("image_url") else [])
    imgs_json = json.dumps(imgs)

    cursor.execute("""
    INSERT OR REPLACE INTO products (
        product_id, platform, title, category, original_price, deal_price,
        discount_pct, rating, reviews_count, image_url, image_urls, source_url, affiliate_url, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product.get("product_id"),
        product.get("platform", "Amazon"),
        product.get("title"),
        product.get("category", "General"),
        product.get("original_price", 0.0),
        product.get("deal_price", 0.0),
        product.get("discount_pct", 0.0),
        product.get("rating", 4.0),
        product.get("reviews_count", 0),
        product.get("image_url", ""),
        imgs_json,
        product.get("source_url", ""),
        product.get("affiliate_url", ""),
        product.get("status", "scouted")
    ))
    conn.commit()
    pid = cursor.lastrowid
    conn.close()
    return pid


def get_products(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM products WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
    else:
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["image_urls"] = json.loads(d.get("image_urls") or "[]")
        except Exception:
            d["image_urls"] = [d.get("image_url")] if d.get("image_url") else []
        rows.append(d)
    conn.close()
    return rows


def update_product_status(product_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET status = ? WHERE id = ?", (status, product_id))
    conn.commit()
    conn.close()


def discard_product_in_db(product_id: str):
    """Marks a product as permanently discarded and cleans up any unapproved drafts/posts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET status = 'discarded' WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM posts WHERE product_id IN (SELECT id FROM products WHERE product_id = ?) AND status != 'published'", (product_id,))
    conn.commit()
    conn.close()


def get_discarded_product_ids() -> set:
    """Returns set of blacklisted/discarded product IDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM products WHERE status = 'discarded'")
    rows = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()
    return set(rows)


def clear_discarded_history():
    """Resets discarded blacklist if user chooses."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET status = 'scouted' WHERE status = 'discarded'")
    conn.commit()
    conn.close()


# ---------------- POSTS REPO ----------------
def save_post(post: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    media_json = json.dumps(post.get("media_paths", []))
    cursor.execute("""
    INSERT INTO posts (
        product_id, platform, post_type, headline, caption, hashtags, media_paths, video_path, status, scheduled_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        post.get("product_id"),
        post.get("platform", "instagram"),
        post.get("post_type", "carousel"),
        post.get("headline", ""),
        post.get("caption", ""),
        post.get("hashtags", ""),
        media_json,
        post.get("video_path", ""),
        post.get("status", "draft"),
        post.get("scheduled_time")
    ))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id


def get_posts(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.*, pr.title as product_title, pr.deal_price, pr.original_price, pr.affiliate_url, pr.image_url as product_image
    FROM posts p
    LEFT JOIN products pr ON p.product_id = pr.id
    """
    if status:
        query += " WHERE p.status = ? ORDER BY p.created_at DESC LIMIT ?"
        cursor.execute(query, (status, limit))
    else:
        query += " ORDER BY p.created_at DESC LIMIT ?"
        cursor.execute(query, (limit,))
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["media_paths"] = json.loads(d.get("media_paths") or "[]")
        except Exception:
            d["media_paths"] = []
        rows.append(d)
    conn.close()
    return rows


def update_post_status(post_id: int, status: str, external_id: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now() if status == "published" else None
    cursor.execute("""
    UPDATE posts SET status = ?, published_time = COALESCE(?, published_time), external_post_id = COALESCE(?, external_post_id)
    WHERE id = ?
    """, (status, now, external_id, post_id))
    conn.commit()
    conn.close()


def bulk_update_posts(posts_data: List[Dict[str, Any]]):
    """Updates headline, status, and platform for posts edited in table editor."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for p in posts_data:
        pid = p.get("id")
        if not pid:
            continue
        status = str(p.get("status", "draft"))
        headline = str(p.get("headline", ""))
        platform = str(p.get("platform", "instagram"))
        cursor.execute("""
        UPDATE posts SET headline = ?, status = ?, platform = ?
        WHERE id = ?
        """, (headline, status, platform, pid))
    conn.commit()
    conn.close()


def get_published_posts_for_cleanup(hours: int = 24) -> List[Dict[str, Any]]:
    """Returns published posts older than retention hours whose local media has not been purged."""
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    SELECT * FROM posts 
    WHERE status = 'published' 
      AND (media_purged IS NULL OR media_purged = 0)
      AND (
          (published_time IS NOT NULL AND published_time <= ?)
          OR (published_time IS NULL AND created_at <= ?)
      )
    """, (cutoff, cutoff))
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        try:
            d["media_paths"] = json.loads(d.get("media_paths") or "[]")
        except Exception:
            d["media_paths"] = []
        rows.append(d)
    conn.close()
    return rows


def mark_post_media_purged(post_id: int):
    """Marks a post's local media files as purged while preserving post metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE posts 
    SET media_purged = 1, media_paths = '[]', video_path = '' 
    WHERE id = ?
    """, (post_id,))
    conn.commit()
    conn.close()


# ---------------- ENGAGEMENT REPO ----------------
def save_engagement_task(task: Dict[str, Any]) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO engagement_tasks (target_account, target_post_url, action_type, content, status)
    VALUES (?, ?, ?, ?, ?)
    """, (
        task.get("target_account"),
        task.get("target_post_url"),
        task.get("action_type", "comment"),
        task.get("content"),
        task.get("status", "pending")
    ))
    conn.commit()
    tid = cursor.lastrowid
    conn.close()
    return tid


def get_engagement_tasks(status: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM engagement_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
    else:
        cursor.execute("SELECT * FROM engagement_tasks ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def update_engagement_task(task_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now() if status == "executed" else None
    cursor.execute("UPDATE engagement_tasks SET status = ?, executed_at = ? WHERE id = ?", (status, now, task_id))
    conn.commit()
    conn.close()


# ---------------- REVENUE REPO ----------------
def log_daily_revenue(log_date_str: str, target: float = 500.0, earnings: float = 0.0, clicks: int = 0, orders: int = 0, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO daily_revenue (log_date, target_inr, estimated_earnings_inr, clicks, orders, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(log_date) DO UPDATE SET
        estimated_earnings_inr = estimated_earnings_inr + excluded.estimated_earnings_inr,
        clicks = clicks + excluded.clicks,
        orders = orders + excluded.orders,
        notes = excluded.notes
    """, (log_date_str, target, earnings, clicks, orders, notes))
    conn.commit()
    conn.close()


def set_daily_revenue_row(log_date_str: str, target: float = 500.0, earnings: float = 0.0, clicks: int = 0, orders: int = 0, notes: str = ""):
    """Sets or replaces a specific row in daily_revenue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO daily_revenue (log_date, target_inr, estimated_earnings_inr, clicks, orders, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(log_date) DO UPDATE SET
        target_inr = excluded.target_inr,
        estimated_earnings_inr = excluded.estimated_earnings_inr,
        clicks = excluded.clicks,
        orders = excluded.orders,
        notes = excluded.notes
    """, (log_date_str, float(target), float(earnings), int(clicks), int(orders), str(notes or "")))
    conn.commit()
    conn.close()


def bulk_save_daily_revenue(rows: List[Dict[str, Any]]):
    """Saves multiple rows from the daily revenue table editor."""
    for r in rows:
        d_str = str(r.get("log_date") or date.today().isoformat())
        set_daily_revenue_row(
            log_date_str=d_str,
            target=float(r.get("target_inr") or 500.0),
            earnings=float(r.get("estimated_earnings_inr") or 0.0),
            clicks=int(r.get("clicks") or 0),
            orders=int(r.get("orders") or 0),
            notes=str(r.get("notes") or "")
        )


def get_revenue_history(days: int = 14) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM daily_revenue ORDER BY log_date DESC LIMIT ?
    """, (days,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------- LOGS REPO ----------------
def log_agent_action(agent: str, action: str, status: str, details: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO agent_logs (agent_name, action, status, details)
    VALUES (?, ?, ?, ?)
    """, (agent, action, status, details))
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# Auto-init on import
init_db()
