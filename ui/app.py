"""Grok-Style Command Console and Multi-Agent Dashboard for AutoAffiliate AI.
Zero hardcoding: dynamic live web scraping, configurable profit target X,
extensible multi-platform affiliate manager, and live test product sandbox.
"""

import streamlit as st
import os
import sys
import time
from datetime import datetime
import pandas as pd

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.orchestrator import AgentOrchestrator
from core.auto_daemon import get_auto_daemon
from core.db import (
    get_products,
    get_posts,
    get_revenue_history,
    get_recent_logs,
    get_engagement_tasks,
    update_post_status,
    log_daily_revenue
)

# Page Configuration
st.set_page_config(
    page_title="AutoAffiliate AI | Multi-Agent Operations Deck",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Grok Dark Theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .brand-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .agent-card {
        background: #151c2e;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .status-badge-active {
        background: #065f46;
        color: #34d399;
        font-size: 0.75rem;
        padding: 3px 8px;
        border-radius: 9999px;
        font-weight: 600;
    }
    .stButton>button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 6px 14px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        box-shadow: 0 0 12px rgba(37, 99, 235, 0.5);
    }
</style>
""", unsafe_allow_html=True)


# Initialize Orchestrator in Session State
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator()

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "agent": "Grok Orchestrator",
            "content": "⚡ **AutoAffiliate AI Operations Deck is Online.** Zero hardcoded items: I scout live real-time Amazon India & Flipkart deals across high-ticket Mobiles (iPhones), Fashion/Dresses, Toys, and seasonal trends. You have full admin control."
        }
    ]

if "last_test_result" not in st.session_state:
    st.session_state.last_test_result = None


# ==============================================================================
# SIDEBAR: Profit Target X, Bot Roster & Multi-Platform Manager
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="brand-title">AutoAffiliate AI</div>', unsafe_allow_html=True)
    st.caption("Autonomous Referral Business Engine")
    st.divider()

    # 1. Configurable Daily Profit Target (X)
    st.subheader("🎯 Daily Target Profit (₹X)")
    current_target = st.session_state.orchestrator.daily_target_inr

    new_target = st.number_input(
        "Set Daily Target (INR)",
        min_value=100.0,
        max_value=100000.0,
        value=float(current_target),
        step=100.0,
        help="Change anytime. All bot commission projections update immediately."
    )
    if new_target != current_target:
        st.session_state.orchestrator.set_daily_target(new_target)
        st.success(f"Target updated to ₹{new_target:,.0f}!")
        st.rerun()

    rev_history = get_revenue_history(days=1)
    today_earned = rev_history[0]["estimated_earnings_inr"] if rev_history else 0.0
    progress_ratio = min(1.0, today_earned / max(1.0, new_target))

    st.progress(progress_ratio)
    col_a, col_b = st.columns(2)
    col_a.metric("Today's Est.", f"₹{today_earned:,.0f}")
    col_b.metric("Target Goal", f"₹{new_target:,.0f}", f"{int(progress_ratio*100)}%")

    st.divider()

    # 2. Employee Bot Roster Status
    st.subheader("👥 Employee Bot Roster")
    st.markdown("""
    <div class="agent-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>🔍 Scout Bot</strong>
            <span class="status-badge-active">LIVE SCRAPING</span>
        </div>
        <small style="color:#94a3b8;">Amazon & Flipkart Real-Time Scout</small>
    </div>
    
    <div class="agent-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>🎨 Creative Bot</strong>
            <span class="status-badge-active">READY</span>
        </div>
        <small style="color:#94a3b8;">Visual Banners & Viral Reel Scripts</small>
    </div>
    
    <div class="agent-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong>🚀 Marketer Bot</strong>
            <span class="status-badge-active">READY</span>
        </div>
        <small style="color:#94a3b8;">Instagram, FB & Telegram Publisher</small>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 3. Dynamic Multi-Platform Affiliate Manager
    with st.expander("🌐 Add / Manage Affiliate Websites"):
        st.write("**Registered Platforms:**")
        platforms = st.session_state.orchestrator.scout.tagger.platforms
        for pk, pv in platforms.items():
            st.caption(f"• **{pv['name']}** (`{pv.get('domains', [''])[0]}`) $\\rightarrow$ ID: `{pv.get('id', 'Not set')}`")

        st.markdown("---")
        st.write("**➕ Add New Website:**")
        p_name = st.text_input("Platform Name", placeholder="e.g. Croma, Tata Cliq")
        p_domain = st.text_input("Domain", placeholder="e.g. croma.com")
        p_param = st.text_input("URL Param", value="affid", placeholder="e.g. tag, affid, utm_source")
        p_id = st.text_input("Your Affiliate ID", placeholder="e.g. mytag_123")
        if st.button("Register Website"):
            if p_name and p_domain and p_id:
                st.session_state.orchestrator.scout.tagger.add_platform(
                    key=p_name.lower().replace(" ", "_"),
                    name=p_name,
                    domain=p_domain,
                    param=p_param or "tag",
                    affiliate_id=p_id
                )
                st.success(f"Added {p_name}! Links from this site will now be auto-tagged.")
                st.rerun()


# ==============================================================================
# 24/7 AUTONOMOUS AGENTIC AUTOPILOT DECK
# ==============================================================================
daemon = get_auto_daemon()

ap_col1, ap_col2, ap_col3 = st.columns([2.5, 1.2, 1.3])
with ap_col1:
    if daemon.is_running:
        last_str = daemon.last_run_time.strftime("%I:%M %p") if daemon.last_run_time else "Just started"
        next_str = daemon.next_run_time.strftime("%I:%M %p") if daemon.next_run_time else "Calculating..."
        st.markdown(f"""
        <div style="background:#064e3b; border:1px solid #059669; border-radius:10px; padding:12px;">
            <strong style="color:#34d399; font-size:1.05rem;">🟢 24/7 AUTONOMOUS AUTOPILOT ACTIVE (Zero Clicks Needed)</strong><br>
            <small style="color:#d1fae5;">Cycle #{daemon.cycle_count} running • Last posted: {last_str} • Next scheduled post: {next_str}</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#1e1b4b; border:1px solid #4338ca; border-radius:10px; padding:12px;">
            <strong style="color:#a5b4fc; font-size:1.05rem;">⏸️ AUTOPILOT STANDBY (Manual Supervised Mode)</strong><br>
            <small style="color:#c7d2fe;">Turn on to let the agents find deals, design graphics, and post 100% autonomously.</small>
        </div>
        """, unsafe_allow_html=True)

with ap_col2:
    interval_hrs = st.selectbox(
        "Posting Interval",
        [1.0, 2.0, 3.0, 4.0, 6.0],
        index=1,
        format_func=lambda x: f"Every {int(x)} Hours",
        disabled=daemon.is_running,
        key="sel_interval"
    )

with ap_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if daemon.is_running:
        if st.button("⏸️ PAUSE AUTOPILOT", use_container_width=True, key="btn_stop_ap"):
            daemon.stop_background_loop()
            st.rerun()
    else:
        if st.button("🚀 START 24/7 AUTOPILOT", use_container_width=True, key="btn_start_ap"):
            daemon.interval_seconds = int(interval_hrs * 3600)
            daemon.start_background_loop()
            st.rerun()

st.divider()

# ==============================================================================
# MAIN TABS
# ==============================================================================
tab_test, tab_chat, tab_deals, tab_posts, tab_pages, tab_analytics = st.tabs([
    "⚡ Test Next Product (Live)",
    "💬 Grok Command Deck",
    "🛍️ Scouted Deals",
    "📱 Posts & Visual Assets",
    "🏷️ Suggested Page Names & Setup",
    "📈 Revenue Tracker"
])


# ------------------------------------------------------------------------------
# TAB 1: Test Next Product (Live Sandbox requested by user)
# ------------------------------------------------------------------------------
with tab_test:
    st.subheader("⚡ Instant Live Product Test Sandbox")
    st.markdown("""
    Test the entire autonomous pipeline on demand:
    1. Scrapes the **next real live product** from Amazon India (no hardcoded data).
    2. Downloads real image & generates a 1080x1080 promotional banner.
    3. Writes a 15s viral Reel script, high-converting caption, and hashtags.
    4. Auto-tags with your affiliate link and calculates commission towards your **₹{:,.0f}** goal.
    """.format(new_target))

    t_col1, t_col2, t_col3 = st.columns([2, 2, 1.5])
    with t_col1:
        test_cat = st.selectbox(
            "Select Live Category to Test",
            ["mobiles", "electronics", "fashion", "toys", "kitchen", "beauty", "all"],
            format_func=lambda x: {
                "mobiles": "📱 High-Ticket Mobiles & iPhones",
                "electronics": "💻 Electronics & Tech",
                "fashion": "👗 Fashion & Trending Dresses",
                "toys": "🧸 Kids Toys & Games",
                "kitchen": "🍳 Home & Kitchen Finds",
                "beauty": "💄 Beauty & Personal Care",
                "all": "⚡ All Amazon Bestsellers"
            }.get(x, x)
        )
    with t_col2:
        custom_query = st.text_input("Or Search Live Keyword (Optional)", placeholder="e.g. iPhone 16, Diwali Lehenga, Drone")
    with t_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_test_btn = st.button("⚡ Test Next Product Now", use_container_width=True)

    if run_test_btn:
        with st.spinner(f"Scout & Creative bots testing live product in '{custom_query or test_cat}'..."):
            res = st.session_state.orchestrator.test_next_product(category=test_cat, query=custom_query if custom_query else None)
            if res.get("success"):
                st.session_state.last_test_result = res
                st.success("Test product successfully fetched and created!")
            else:
                st.error(res.get("error", "Failed to retrieve live product."))

    # Show Last Test Result
    if st.session_state.last_test_result:
        res = st.session_state.last_test_result
        p = res["product"]
        pst = res["post"]

        st.divider()
        st.markdown("### 🔍 Live Test Results")

        res_col_img, res_col_info = st.columns([1.5, 2.5])
        with res_col_img:
            v_path = pst.get("video_path")
            if v_path and os.path.exists(v_path):
                st.video(v_path)
                st.caption("🎬 Generated 9:16 AI Reel (With Neural Voiceover)")

            media = pst.get("media_paths", [])
            if media:
                if len(media) == 1 and os.path.exists(media[0]):
                    st.image(media[0], caption="Generated 1080x1080 Banner", use_container_width=True)
                else:
                    st.write(f"📸 **Multi-Image Carousel ({len(media)} Angles):**")
                    cols = st.columns(min(len(media), 4))
                    for idx, (m_path, col) in enumerate(zip(media, cols)):
                        if os.path.exists(m_path):
                            col.image(m_path, caption=f"Slide {idx+1}", use_container_width=True)
            elif p.get("image_url"):
                st.image(p["image_url"], caption="Live Product Photo", use_container_width=True)

            st.metric("Deal Price", f"₹{int(p['deal_price']):,}", f"-{int(p['discount_pct'])}% OFF")
            st.metric("Est. Commission", f"₹{p.get('est_comm_per_sale', 0)} / sale", f"~{p.get('units_to_goal', 1)} sales to hit ₹{new_target:,.0f}")

        with res_col_info:
            st.markdown(f"#### {p['title']}")
            st.markdown(f"**Live Affiliate URL:** `{p['affiliate_url']}`")
            st.markdown(f"**Headline Hook:** *{pst['headline']}*")

            with st.expander("📝 View Generated Instagram Caption", expanded=True):
                st.text_area("Caption", pst["caption"], height=160)
                st.caption(f"**Hashtags:** {pst['hashtags']}")

            with st.expander("🎬 15-Second Viral Reel Script & Audio Hook"):
                st.markdown(f"```\n{pst.get('reel_script', '')}\n```")

            c_pub1, c_pub2 = st.columns(2)
            with c_pub1:
                if st.button("🚀 Publish This Test Post", key="pub_test_post", use_container_width=True):
                    with st.spinner("Publishing across channels..."):
                        pub_res = st.session_state.orchestrator.marketer.publish_approved_post(pst)
                        st.success("Test post published successfully!")


# ------------------------------------------------------------------------------
# TAB 2: Grok Command Deck
# ------------------------------------------------------------------------------
with tab_chat:
    st.subheader("⚡ Grok Agent Command Console")
    st.caption("You have full admin rights. Command your bot employees in natural language.")

    # Quick Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🚀 Run Full Autopilot", key="btn_ap", use_container_width=True):
            with st.spinner("Executing end-to-end autonomous business cycle..."):
                res = st.session_state.orchestrator.process_chat_command("run full autopilot cycle")
                st.session_state.chat_messages.append({"role": "user", "content": "Run full autopilot cycle"})
                st.session_state.chat_messages.append({"role": "assistant", "agent": res["agent"], "content": res["response"]})
                st.rerun()

    with col2:
        if st.button("🔍 Scout Mobiles & iPhones", key="btn_mob", use_container_width=True):
            with st.spinner("Scouting live mobile bestsellers..."):
                res = st.session_state.orchestrator.process_chat_command("find trending mobiles")
                st.session_state.chat_messages.append({"role": "user", "content": "Find trending mobiles"})
                st.session_state.chat_messages.append({"role": "assistant", "agent": res["agent"], "content": res["response"]})
                st.rerun()

    with col3:
        if st.button("👗 Scout Fashion & Dresses", key="btn_fash", use_container_width=True):
            with st.spinner("Scouting live fashion bestsellers..."):
                res = st.session_state.orchestrator.process_chat_command("find fashion dresses")
                st.session_state.chat_messages.append({"role": "user", "content": "Find fashion dresses"})
                st.session_state.chat_messages.append({"role": "assistant", "agent": res["agent"], "content": res["response"]})
                st.rerun()

    with col4:
        if st.button("🧸 Scout Viral Toys", key="btn_toys", use_container_width=True):
            with st.spinner("Scouting live toy bestsellers..."):
                res = st.session_state.orchestrator.process_chat_command("find toys")
                st.session_state.chat_messages.append({"role": "user", "content": "Find toys"})
                st.session_state.chat_messages.append({"role": "assistant", "agent": res["agent"], "content": res["response"]})
                st.rerun()

    # Chat Transcript Container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant", avatar="⚡"):
                    st.markdown(f"**[{msg.get('agent', 'Grok Lead')}]:**\n\n{msg['content']}")

    if user_prompt := st.chat_input("Command your team (e.g. 'Test next iPhone', 'Set target to 2000', 'Scout fashion')..."):
        st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Bot team working..."):
                result = st.session_state.orchestrator.process_chat_command(user_prompt)
                st.markdown(f"**[{result['agent']}]:**\n\n{result['response']}")
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "agent": result["agent"],
                    "content": result["response"]
                })


# ------------------------------------------------------------------------------
# TAB 3: Scouted Deals Pipeline
# ------------------------------------------------------------------------------
with tab_deals:
    st.subheader("🛍️ Discovered Real Live Products")
    st.caption("Live Amazon India and Flipkart products scouted dynamically. No arbitrary price caps.")

    # Manual Import
    with st.expander("➕ Import Any Live Product URL (Amazon, Flipkart, Myntra, etc.)"):
        c_url, c_btn = st.columns([4, 1])
        with c_url:
            custom_url = st.text_input("Product URL", placeholder="https://www.amazon.in/dp/B0XXXXXXXX...", label_visibility="collapsed")
        with c_btn:
            if st.button("Import & Tag", key="import_btn"):
                if custom_url:
                    item = st.session_state.orchestrator.scout.import_product_from_url(custom_url, target_profit=new_target)
                    if item:
                        st.success(f"Imported: {item['title'][:40]}!")
                        st.rerun()

    products = get_products(limit=25)
    if not products:
        st.info("No products scouted yet. Click 'Test Next Product' or run a Scout command!")
    else:
        for p in products:
            with st.container():
                col_img, col_info, col_act = st.columns([1.2, 3, 1.2])
                with col_img:
                    if p.get("image_url"):
                        st.image(p["image_url"], use_container_width=True)
                with col_info:
                    st.markdown(f"### {p['title']}")
                    st.markdown(f"**Category:** `{p['category']}` | **Platform:** {p['platform']}")
                    p_col1, p_col2, p_col3 = st.columns(3)
                    p_col1.metric("Deal Price", f"₹{int(p['deal_price']):,}", f"-{int(p['discount_pct'])}% OFF")
                    p_col2.metric("Original MRP", f"₹{int(p['original_price']):,}")
                    p_col3.metric("Rating", f"★ {p['rating']}")
                    st.caption(f"**Affiliate Link:** `{p['affiliate_url']}`")
                with col_act:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(f"🎨 Generate Post", key=f"gen_{p['id']}", use_container_width=True):
                        with st.spinner("Creative bot generating assets..."):
                            post = st.session_state.orchestrator.creative.generate_content_for_product(p)
                            st.success(f"Post #{post['id']} generated!")
                            st.rerun()
                st.divider()


# ------------------------------------------------------------------------------
# TAB 4: Posts & Visual Assets Review Deck
# ------------------------------------------------------------------------------
with tab_posts:
    st.subheader("📱 Social Media Posts & Visual Assets")
    posts = get_posts(limit=20)
    if not posts:
        st.info("No posts created yet. Go to 'Test Next Product' tab to generate one instantly.")
    else:
        for post in posts:
            with st.container():
                col_prev, col_body = st.columns([1.5, 2.5])
                with col_prev:
                    st.markdown(f"#### Post #{post['id']}")
                    vid_p = post.get("video_path")
                    if vid_p and os.path.exists(vid_p):
                        st.video(vid_p)
                        st.caption("🎬 AI Reel Video (With Neural Voiceover)")

                    media_paths = post.get("media_paths", [])
                    if media_paths:
                        if len(media_paths) == 1 and os.path.exists(media_paths[0]):
                            st.image(media_paths[0], caption="Generated 1080x1080 Graphic Banner", use_container_width=True)
                        else:
                            st.write(f"📸 **Multi-Image Carousel ({len(media_paths)} Angles):**")
                            c_imgs = st.columns(min(len(media_paths), 4))
                            for idx, (m_p, c_i) in enumerate(zip(media_paths, c_imgs)):
                                if os.path.exists(m_p):
                                    c_i.image(m_p, caption=f"Slide {idx+1}", use_container_width=True)
                    elif post.get("product_image"):
                        st.image(post["product_image"], use_container_width=True)

                    status_color = "#34d399" if post["status"] == "published" else "#f59e0b"
                    st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{post['status'].upper()}</span>", unsafe_allow_html=True)

                    if post["status"] != "published":
                        if st.button(f"🚀 Approve & Publish", key=f"pub_{post['id']}", use_container_width=True):
                            with st.spinner("Publishing..."):
                                res = st.session_state.orchestrator.marketer.publish_approved_post(post)
                                st.success("Post successfully published!")
                                st.rerun()

                with col_body:
                    st.markdown(f"**Headline Hook:** {post.get('headline', '')}")
                    with st.expander("📝 Full Caption & Hashtags", expanded=True):
                        st.text_area("Caption", post.get("caption", ""), height=180, key=f"cap_{post['id']}")
                        st.caption(f"**Hashtags:** {post.get('hashtags', '')}")

                    with st.expander("🎬 15-Second Viral Reel Script"):
                        st.markdown(f"```\n{post.get('reel_script', 'Reel script ready for recording.')}\n```")
                st.divider()


# ------------------------------------------------------------------------------
# TAB 5: Suggested Page Names & Setup Guide (Requirement #2)
# ------------------------------------------------------------------------------
with tab_pages:
    st.subheader("🏷️ Suggested Social Media Page Names & Setup Steps")
    st.markdown("""
    Here are high-converting, brandable names for your new Instagram and Facebook pages:
    """)

    col_names1, col_names2 = st.columns(2)
    with col_names1:
        st.markdown("""
        #### 🔥 Option A: All-Round Loot Deals & Tech (Recommended)
        - **`@DealPulse.India`** / **DealPulse India**
        - **`@LootBazaar.AI`** / **Loot Bazaar India**
        - **`@DesiDropDeals`** / **Desi Drop Deals**
        - **`@TrendingFinds.in`** / **Trending Finds Bharat**

        **Instagram Bio Template:**
        ```text
        ⚡ Finding the Internet's Best Deals & Hidden Finds
        📱 Mobiles • Fashion • Smart Gadgets • Loot Offers
        🔥 Daily Price Drops on Amazon & Flipkart
        👇 Tap link below for today's exclusive discounts!
        [Your Linktree / Deals Hub Link]
        ```
        """)

    with col_names2:
        st.markdown("""
        #### 👗 Option B: Lifestyle & Fashion Deals
        - **`@StyleDropIndia`** / **Style Drop India**
        - **`@FestiveFinds.in`** / **Festive Finds India**
        - **`@BudgetChicBharat`** / **Budget Chic Bharat**

        **Facebook Page Category:**
        - Select: **E-commerce Website** or **Retail Company** or **Shopping & Retail**.
        """)

    st.divider()
    st.markdown("### 📋 Step-by-Step Page Setup Instructions")
    st.markdown("""
    1. **Create Instagram Account**: Open Instagram app $\\rightarrow$ Create new account with your chosen name (e.g. `dealpulse.india`).
    2. **Switch to Professional / Creator Account**:
       - Go to Settings $\\rightarrow$ Account Type $\\rightarrow$ Switch to **Creator Account**.
       - Choose category: **Digital Creator** or **Shopping & Retail**.
    3. **Create Facebook Page**:
       - Open Facebook $\\rightarrow$ Pages $\\rightarrow$ Create New Page with matching name.
       - Connect your Instagram account in Facebook Page Settings $\\rightarrow$ **Linked Accounts**.
    4. **Link in Bio**:
       - Create a free landing page using Linktree or Beacons (e.g., `linktr.ee/yourpagename`).
       - Put your top product links and your Telegram channel link here.
    """)


# ------------------------------------------------------------------------------
# TAB 6: Revenue Analytics Tracker
# ------------------------------------------------------------------------------
with tab_analytics:
    st.subheader("📈 Affiliate Income & Progress Tracker")
    history = get_revenue_history(days=14)
    total_est_rev = sum(h.get("estimated_earnings_inr", 0) for h in history)
    total_clicks_all = sum(h.get("clicks", 0) for h in history)
    total_orders_all = sum(h.get("orders", 0) for h in history)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Daily Target (X)", f"₹{new_target:,.0f} / Day")
    m2.metric("Total Logged Est.", f"₹{total_est_rev:,.2f}")
    m3.metric("Total Link Clicks", f"{total_clicks_all}")
    m4.metric("Orders Converted", f"{total_orders_all}")

    st.divider()

    st.subheader("🔍 Operational Logs")
    logs = get_recent_logs(limit=20)
    if logs:
        df_logs = pd.DataFrame(logs)[["created_at", "agent_name", "action", "status", "details"]]
        st.dataframe(df_logs, use_container_width=True)
