"""Storage Janitor Agent ('Cleaner').
Automatically purges generated post images, carousel slides, and video files
after they have been published and are older than 24 hours (1 day).
Maintains database records, metrics, and captions while strictly reclaiming disk space.
"""

import os
import glob
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import yaml

from core.db import (
    get_published_posts_for_cleanup,
    mark_post_media_purged,
    log_agent_action
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.yaml")
GENERATED_IMG_DIR = os.path.join(BASE_DIR, "data", "generated_images")
GENERATED_VID_DIR = os.path.join(BASE_DIR, "data", "generated_videos")
ASSETS_DIR = os.path.join(BASE_DIR, "data", "assets")


class CleanerAgent:
    def __init__(self, default_retention_hours: int = 24):
        self.name = "Storage Janitor (Media Cleanup Bot)"
        self.default_retention_hours = default_retention_hours

    def _load_retention_hours(self) -> int:
        """Loads configured retention hours from settings.yaml (defaults to 24 hours)."""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    return int(cfg.get("storage_cleanup", {}).get("retention_hours", self.default_retention_hours))
            except Exception:
                pass
        return self.default_retention_hours

    def _is_safe_to_delete(self, file_path: str) -> bool:
        """
        Safety guard: Ensures file is inside generated media directories
        and NEVER inside protected assets (e.g. Elena avatar).
        """
        if not file_path or not os.path.exists(file_path):
            return False
        
        norm_path = os.path.abspath(file_path).lower()
        norm_assets = os.path.abspath(ASSETS_DIR).lower()
        norm_img_dir = os.path.abspath(GENERATED_IMG_DIR).lower()
        norm_vid_dir = os.path.abspath(GENERATED_VID_DIR).lower()

        # Strict protection: Never delete brand assets or gitkeep markers!
        if norm_path.startswith(norm_assets) or "elena_avatar" in norm_path or norm_path.endswith(".gitkeep"):
            return False

        # Only delete files inside generated_images or generated_videos
        return norm_path.startswith(norm_img_dir) or norm_path.startswith(norm_vid_dir)

    def clean_expired_published_media(self, retention_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Finds all published posts older than retention_hours (default 24h = 1 day),
        deletes their local carousel slides and video files from disk,
        and marks the posts as media_purged in SQLite.
        """
        hours = retention_hours if retention_hours is not None else self._load_retention_hours()
        expired_posts = get_published_posts_for_cleanup(hours=hours)

        deleted_files = 0
        freed_bytes = 0
        cleaned_post_ids = []

        for post in expired_posts:
            post_id = post["id"]
            media_paths = post.get("media_paths", [])
            video_path = post.get("video_path")

            # 1. Delete generated carousel slides
            for m_path in media_paths:
                if self._is_safe_to_delete(m_path):
                    try:
                        sz = os.path.getsize(m_path)
                        os.remove(m_path)
                        freed_bytes += sz
                        deleted_files += 1
                    except Exception as e:
                        print(f"Janitor cleanup note for {m_path}: {e}")

            # 2. Delete generated video reel
            if video_path and self._is_safe_to_delete(video_path):
                try:
                    sz = os.path.getsize(video_path)
                    os.remove(video_path)
                    freed_bytes += sz
                    deleted_files += 1
                except Exception as e:
                    print(f"Janitor cleanup note for {video_path}: {e}")

            # 3. Mark in DB so it won't be reprocessed
            mark_post_media_purged(post_id)
            cleaned_post_ids.append(post_id)

        # 4. Clean orphan files in generated_videos and generated_images older than retention_hours
        orphan_cutoff = time.time() - (hours * 3600)
        for folder in [GENERATED_IMG_DIR, GENERATED_VID_DIR]:
            if not os.path.exists(folder):
                continue
            for fname in os.listdir(folder):
                full_p = os.path.join(folder, fname)
                if not os.path.isfile(full_p):
                    continue
                # Never delete elena avatar
                if "elena" in fname.lower() or not self._is_safe_to_delete(full_p):
                    continue
                # If temporary video/audio or orphan file is older than 24h
                try:
                    if os.path.getmtime(full_p) < orphan_cutoff:
                        sz = os.path.getsize(full_p)
                        os.remove(full_p)
                        freed_bytes += sz
                        deleted_files += 1
                except Exception:
                    pass

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        summary = (
            f"Janitor Bot completed 1-day media purge: Deleted {deleted_files} files "
            f"({freed_mb} MB freed) across {len(cleaned_post_ids)} published posts."
        )

        if deleted_files > 0 or len(cleaned_post_ids) > 0:
            log_agent_action(self.name, summary, "completed")

        return {
            "success": True,
            "retention_hours": hours,
            "posts_cleaned": len(cleaned_post_ids),
            "files_deleted": deleted_files,
            "freed_mb": freed_mb
        }

    def get_storage_stats(self) -> Dict[str, Any]:
        """Calculates current storage footprint of generated media."""
        total_files = 0
        total_bytes = 0

        for folder in [GENERATED_IMG_DIR, GENERATED_VID_DIR]:
            if os.path.exists(folder):
                for fname in os.listdir(folder):
                    f_path = os.path.join(folder, fname)
                    if os.path.isfile(f_path):
                        total_files += 1
                        total_bytes += os.path.getsize(f_path)

        return {
            "total_files": total_files,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
            "retention_hours": self._load_retention_hours(),
            "auto_delete_active": True
        }
