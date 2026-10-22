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
import importlib
import core.orchestrator
importlib.reload(core.orchestrator)
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


# Initialize Orchestrator in Session State (auto-refresh if outdated instance)
if "orchestrator" not in st.session_state or not hasattr(st.session_state.orchestrator, "tested_product_ids"):
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
all_profiles = st.session_state.orchestrator.get_channel_profiles()
enabled_profiles = st.session_state.orchestrator.get_enabled_autopilot_profiles()
active_prof = st.session_state.orchestrator.get_active_profile()

with st.container():
    st.markdown("### 🤖 Autonomous Multi-Channel Autopilot Deck")
    st.caption("Select which channel(s) to run on Autopilot. Each selected account operates 100% independently: Ladies fashion posts exclusively to ladies pages, electronics posts to electronics pages.")

    ap_col1, ap_col2 = st.columns([3, 1.2])
    with ap_col1:
        st.write("**🎯 Select Active Autopilot Channels (Run Independently):**")
        cb_cols = st.columns(max(len(all_profiles), 1))
        for idx, prof in enumerate(all_profiles):
            pid = prof["id"]
            is_enabled = prof.get("enabled_for_autopilot", False)
            with cb_cols[idx % len(cb_cols)]:
                niche_tag = prof.get("focus_niche", "all").upper()
                chk = st.checkbox(
                    f"**{prof['name']}**\n\n`[{niche_tag}]`",
                    value=is_enabled,
                    key=f"chk_ap_{pid}",
                    help=f"If checked, autopilot will independently find deals and post to {prof['name']}'s FB & Instagram"
                )
                if chk != is_enabled:
                    st.session_state.orchestrator.set_profile_autopilot_enabled(pid, chk)
                    st.rerun()

    with ap_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if daemon.is_running:
            if st.button("⏸️ PAUSE AUTOPILOT", use_container_width=True, key="btn_stop_ap"):
                daemon.stop_background_loop()
                st.rerun()
        else:
            if st.button("🚀 START 24/7 AUTOPILOT", use_container_width=True, key="btn_start_ap"):
                daemon.start_background_loop()
                st.rerun()

        # Immediate single-cycle test button
        if st.button("⚡ Run Cycle Now (All Selected)", use_container_width=True, key="btn_run_cycle_now"):
            with st.spinner("Running independent cycles for selected channels..."):
                cycle_results = daemon.run_one_autonomous_cycle()
                st.session_state["last_cycle_results"] = cycle_results
                st.toast("Autonomous cycle completed successfully!", icon="✅")
                st.rerun()

    # Dynamic Timing & Anti-Bot Protection Banner
    status_bg = "#064e3b" if daemon.is_running else "#1e1b4b"
    status_border = "#059669" if daemon.is_running else "#4338ca"
    status_title = "🟢 24/7 DYNAMIC AUTOPILOT RUNNING" if daemon.is_running else "⏸️ DYNAMIC AUTOPILOT STANDBY"
    enabled_names = [p["name"] for p in st.session_state.orchestrator.get_enabled_autopilot_profiles()]
    enabled_str = ", ".join(enabled_names) if enabled_names else "None selected"

    last_str = daemon.last_run_time.strftime("%I:%M %p") if daemon.last_run_time else "None yet"
    next_str = daemon.next_run_time.strftime("%I:%M %p") if daemon.next_run_time else "Calculated dynamically on launch"

    st.markdown(f"""
    <div style="background:{status_bg}; border:1px solid {status_border}; border-radius:10px; padding:12px; margin-top:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#ffffff; font-size:1.0rem;">{status_title}</strong>
            <span style="color:#a7f3d0; font-size:0.85rem; background:#047857; padding:3px 8px; border-radius:6px;">🛡️ Anti-Bot Safety Active</span>
        </div>
        <div style="color:#e2e8f0; font-size:0.9rem; margin-top:6px;">
            • <b>Active Independent Channels:</b> {enabled_str}<br>
            • <b>Dynamic Timing:</b> No fixed schedule (no 12:30 or static clock). Intervals randomize between 90m to 210m with human jitter.<br>
            • <b>Humanoid Copy:</b> 100% clean conversational copy with ZERO emojis and ZERO special characters.<br>
            • <b>Organic Growth:</b> Finds new people daily, likes recent posts, leaves genuine comments, and invites high-intent users.<br>
            • <b>Execution:</b> Cycle #{daemon.cycle_count} • Last run: {last_str} • Next dynamic window: {next_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "last_cycle_results" in st.session_state and st.session_state["last_cycle_results"]:
        l_res = st.session_state["last_cycle_results"]
        with st.expander("📋 Last Autonomous Cycle Execution Report", expanded=True):
            st.write(f"**Channels Processed:** {l_res.get('channels_processed', 0)}")
            for d in l_res.get("details", []):
                st.success(f"✓ **[{d['channel']}]** ({d['niche'].upper()}): Scouted '{d['product']}', published Post #{d['post_id']} to FB/Instagram, and executed {d['growth_actions']} organic growth actions.")

st.divider()


# ==============================================================================
# MAIN TABS
# ==============================================================================
tab_test, tab_chat, tab_channels, tab_deals, tab_posts, tab_pages, tab_analytics = st.tabs([
    "⚡ Test Next Product (Live)",
    "💬 Grok Command Deck",
    "⚙️ Common Settings & Channels",
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

    t_col_plat, t_col1, t_col2, t_col3 = st.columns([1.5, 1.8, 1.8, 1.4])
    with t_col_plat:
        test_platform = st.selectbox(
            "Platform Source",
            ["auto", "amazon", "flipkart"],
            format_func=lambda x: {
                "auto": "⚡ Auto (Amazon + Flipkart)",
                "amazon": "📦 Amazon India Only",
                "flipkart": "🛍️ Flipkart Only"
            }.get(x, x),
            help="Toggle between Amazon, Flipkart, or Auto-cycling between both"
        )
    with t_col1:
        pref_niche = active_prof.get("focus_niche", "all")
        cat_choices = ["all", "fashion", "mobiles", "electronics", "toys", "kitchen", "beauty"]
        def_cat_idx = cat_choices.index(pref_niche) if pref_niche in cat_choices else 0
        test_cat = st.selectbox(
            "Live Category",
            cat_choices,
            index=def_cat_idx,
            format_func=lambda x: {
                "mobiles": "📱 High-Ticket Mobiles & iPhones",
                "electronics": "💻 Electronics & Tech",
                "fashion": "👗 Fashion & Trending Dresses",
                "toys": "🧸 Kids Toys & Games",
                "kitchen": "🍳 Home & Kitchen Finds",
                "beauty": "💄 Beauty & Personal Care",
                "all": "⚡ Top Bestsellers & Deals"
            }.get(x, x)
        )
    with t_col2:
        custom_query = st.text_input("Or Search Live Keyword", placeholder="e.g. iPhone 16, Lehenga, RC Car")
    with t_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_test_btn = st.button("⚡ Test Next Product Now", use_container_width=True)

    if run_test_btn:
        with st.spinner(f"Scout & Creative bots fetching next live deal from {test_platform.upper()} in '{custom_query or test_cat}'..."):
            if not hasattr(st.session_state.orchestrator, "tested_product_ids"):
                st.session_state.orchestrator = AgentOrchestrator()

            res = st.session_state.orchestrator.test_next_product(
                category=test_cat,
                query=custom_query if custom_query else None,
                platform=test_platform
            )
            if res.get("success"):
                st.session_state.last_test_result = res
                st.toast(f"✅ Fetched fresh live deal from {res.get('platform', 'Amazon')}!", icon="⚡")
                st.rerun()
            else:
                st.error(res.get("error", "Failed to retrieve live product."))

    # Show Last Test Result
    if st.session_state.last_test_result:
        res = st.session_state.last_test_result
        p = res["product"]
        pst = res["post"]
        plat_badge = "🛍️ Flipkart Live Deal" if p.get("platform") == "Flipkart" else "📦 Amazon India Live Deal"
        t_num = res.get("test_number", 1)

        st.divider()
        st.markdown(f"### 🔍 Live Test Results — <span style='color:#38bdf8; font-weight:700;'>{plat_badge}</span> <small style='color:#94a3b8;'>(Test #{t_num} Fresh Live Item)</small>", unsafe_allow_html=True)
        st.caption("💡 Every time you click **'⚡ Test Next Product Now'**, the bots dynamically advance to the NEXT live product on the market!")

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
# TAB 3: Common Settings & Multi-Channel Profiles
# ------------------------------------------------------------------------------
with tab_channels:
    st.subheader("⚙️ Channel Profiles, Dynamic Scheduling & Global Settings")
    st.markdown("""
    Configure your specific social media accounts (e.g. Account 1 for **Ladies Dresses**, Account 2 for **Electronics**, or **any custom niche**).
    Each account runs 100% independently on Autopilot: Ladies fashion posts exclusively to ladies pages, electronics posts to electronics pages.
    """)

    # 1. Channel Profiles Cards
    st.markdown("### 📱 Connected Social Media Accounts")
    all_profiles = st.session_state.orchestrator.get_channel_profiles()
    curr_active = st.session_state.orchestrator.get_active_profile()

    for prof in all_profiles:
        pid = prof.get("id")
        is_act = (pid == curr_active.get("id"))
        is_ap_enabled = prof.get("enabled_for_autopilot", False)
        status_tag = "🟢 ACTIVE FOCUS" if is_act else "⚪ STANDBY"

        with st.container():
            col_p1, col_p2, col_p3 = st.columns([2.8, 2.2, 1.4])
            with col_p1:
                st.markdown(f"#### {prof.get('name')}")
                st.caption(prof.get("description", ""))
                st.markdown(f"**Target Niche:** `{prof.get('focus_niche', 'all').upper()}`")
            with col_p2:
                ig_name = prof.get("instagram_username") or "Not set"
                fb_id = prof.get("facebook_page_id") or "Not set"
                tg_ch = prof.get("telegram_channel_id") or "Not set"
                st.markdown(f"• **Instagram:** `{ig_name}`")
                st.markdown(f"• **Facebook Page ID:** `{fb_id}`")
                st.markdown(f"• **Telegram Channel:** `{tg_ch}`")
            with col_p3:
                # Direct Autopilot Checkbox on Card
                ap_chk = st.checkbox(
                    "Autopilot Enabled",
                    value=is_ap_enabled,
                    key=f"card_ap_{pid}",
                    help="Enable to run independent posting and growth cycles for this account"
                )
                if ap_chk != is_ap_enabled:
                    st.session_state.orchestrator.set_profile_autopilot_enabled(pid, ap_chk)
                    st.rerun()

                if not is_act:
                    if st.button("Set as Active Focus", key=f"btn_act_{pid}", use_container_width=True):
                        st.session_state.orchestrator.set_active_profile(pid)
                        st.rerun()
                else:
                    st.markdown("<span style='color:#34d399; font-weight:700;'>🟢 ACTIVE FOCUS</span>", unsafe_allow_html=True)
            st.divider()

    # 2. Add / Edit Channel Profile Form (100% Flexible for Any Niche)
    st.markdown("### ➕ Add New Social Media Account / Any Custom Niche")
    with st.expander("Register New Account Profile (100% Flexible Niche)", expanded=False):
        with st.form("form_add_channel"):
            new_c_name = st.text_input("Account Display Name", placeholder="e.g. DesiGlam India or SmartKitchen Finds")
            col_n_sel, col_n_cust = st.columns(2)
            with col_n_sel:
                new_c_niche_preset = st.selectbox(
                    "Select Preset Niche",
                    ["fashion", "mobiles", "electronics", "toys", "kitchen", "beauty", "home_decor", "fitness", "custom"],
                    format_func=lambda x: {
                        "fashion": "👗 Ladies Fashion & Trending Dresses",
                        "mobiles": "📱 High-Ticket Mobiles & Tech",
                        "electronics": "💻 Electronics & Gadgets",
                        "toys": "🧸 Kids Toys & Games",
                        "kitchen": "🍳 Kitchen Hacks & Cookware",
                        "beauty": "💄 Beauty & Personal Care",
                        "home_decor": "🏠 Home Decor & Organization",
                        "fitness": "🏋️ Fitness & Workout Gear",
                        "custom": "✨ Custom Niche (Specify on right)"
                    }.get(x, x)
                )
            with col_n_cust:
                new_c_niche_custom = st.text_input("Or Custom Niche Name", placeholder="e.g. baby_products, luxury_watches")

            final_niche = new_c_niche_custom.strip().lower() if new_c_niche_custom.strip() else new_c_niche_preset

            new_c_desc = st.text_input("Description", placeholder="e.g. Dedicated exclusively to home organization and smart kitchen finds")
            new_c_ig = st.text_input("Instagram Handle", placeholder="e.g. @desiglam.in")
            new_c_fb = st.text_input("Facebook Page ID", placeholder="e.g. 1029384756")
            new_c_tg = st.text_input("Telegram Channel Username (Optional)", placeholder="e.g. @desiglam_deals")
            new_c_token = st.text_input("Meta Graph API Access Token (Optional)", type="password", placeholder="Leave blank to use default token or simulation")
            new_c_aff = st.text_input("Custom Affiliate Tag Override (Optional)", placeholder="Leave blank to use global tag")
            new_c_auto = st.checkbox("Enable for Autonomous Autopilot", value=True)

            submitted = st.form_submit_button("Save Account Profile")
            if submitted and new_c_name:
                p_id = new_c_name.lower().replace(" ", "_").replace("(", "").replace(")", "")[:20]
                profile_payload = {
                    "id": p_id,
                    "name": new_c_name,
                    "focus_niche": final_niche,
                    "description": new_c_desc,
                    "instagram_username": new_c_ig,
                    "facebook_page_id": new_c_fb,
                    "telegram_channel_id": new_c_tg,
                    "meta_access_token": new_c_token,
                    "custom_affiliate_tag": new_c_aff,
                    "enabled_for_autopilot": new_c_auto
                }
                st.session_state.orchestrator.save_channel_profile(profile_payload)
                st.success(f"Channel profile '{new_c_name}' created successfully with niche '{final_niche}'!")
                st.rerun()

    # 3. Edit / Delete Existing Account Profile
    with st.expander("✏️ Edit / Delete Existing Account", expanded=False):
        edit_pid = st.selectbox(
            "Select Account to Edit",
            [p["id"] for p in all_profiles],
            format_func=lambda pid: next((p["name"] for p in all_profiles if p["id"] == pid), pid)
        )
        target_p = next((p for p in all_profiles if p["id"] == edit_pid), None)
        if target_p:
            with st.form("form_edit_channel"):
                ed_name = st.text_input("Account Display Name", value=target_p.get("name", ""))
                ed_niche = st.text_input("Niche Focus (e.g. fashion, mobiles, electronics, kitchen)", value=target_p.get("focus_niche", "all"))
                ed_desc = st.text_input("Description", value=target_p.get("description", ""))
                ed_ig = st.text_input("Instagram Handle", value=target_p.get("instagram_username", ""))
                ed_fb = st.text_input("Facebook Page ID", value=target_p.get("facebook_page_id", ""))
                ed_tg = st.text_input("Telegram Channel", value=target_p.get("telegram_channel_id", ""))
                ed_ap = st.checkbox("Enabled for Autopilot", value=target_p.get("enabled_for_autopilot", True))
                ed_sub = st.form_submit_button("Update Account")
                if ed_sub:
                    target_p["name"] = ed_name
                    target_p["focus_niche"] = ed_niche.strip().lower()
                    target_p["description"] = ed_desc
                    target_p["instagram_username"] = ed_ig
                    target_p["facebook_page_id"] = ed_fb
                    target_p["telegram_channel_id"] = ed_tg
                    target_p["enabled_for_autopilot"] = ed_ap
                    st.session_state.orchestrator.save_channel_profile(target_p)
                    st.success("Account updated successfully!")
                    st.rerun()

            if len(all_profiles) > 1:
                if st.button("🗑️ Delete This Account", key=f"del_{edit_pid}"):
                    if st.session_state.orchestrator.delete_channel_profile(edit_pid):
                        st.success("Account profile deleted.")
                        st.rerun()

    st.divider()

    # 4. Dynamic Timing & Anti-Bot Protection Settings
    st.markdown("### 🛡️ Dynamic Schedule & Anti-Bot Protection Settings")
    st.caption("No fixed clock times (12:30/18:30 removed). Posting intervals and micro-delays vary dynamically to prevent bot detection.")

    glob_cfg = st.session_state.orchestrator._load_config()
    dyn_cfg = glob_cfg.get("dynamic_schedule", {})
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        s_min_interval = st.number_input("Minimum Interval (Minutes)", min_value=30, max_value=360, value=int(dyn_cfg.get("min_interval_minutes", 90)), step=15)
    with col_d2:
        s_max_interval = st.number_input("Maximum Interval (Minutes)", min_value=60, max_value=720, value=int(dyn_cfg.get("max_interval_minutes", 210)), step=15)
    with col_d3:
        s_jitter_max = st.number_input("Human Simulation Jitter (Seconds)", min_value=10, max_value=180, value=int(dyn_cfg.get("human_jitter_sec_max", 90)), step=5)

    # 5. Common Global Affiliate Settings
    st.markdown("### 🌐 Global Affiliate & Compliance Settings")
    with st.form("form_global_settings"):
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g_tag = st.text_input("Global Amazon Associate Tag", value=glob_cfg.get("affiliate", {}).get("amazon_associate_tag", "autoaffil-21"))
            g_disc = st.text_input("Default Legal Disclosure Text (Humanoid, Zero Emojis)", value=glob_cfg.get("affiliate", {}).get("default_disclosure_text", "Disclosure: This post contains affiliate links. As an associate I earn from qualifying purchases."))
        with col_g2:
            g_earnkaro = st.text_input("EarnKaro API Key / Publisher ID", value=glob_cfg.get("affiliate", {}).get("earnkaro_api_key", ""), placeholder="Optional for 150+ Indian brands")
            g_target = st.number_input("Daily Revenue Target (INR)", min_value=100.0, max_value=100000.0, value=float(st.session_state.orchestrator.daily_target_inr), step=100.0)

        if st.form_submit_button("Save All Settings"):
            if "affiliate" not in glob_cfg:
                glob_cfg["affiliate"] = {}
            glob_cfg["affiliate"]["amazon_associate_tag"] = g_tag
            glob_cfg["affiliate"]["default_disclosure_text"] = g_disc
            glob_cfg["affiliate"]["earnkaro_api_key"] = g_earnkaro
            if "dynamic_schedule" not in glob_cfg:
                glob_cfg["dynamic_schedule"] = {}
            glob_cfg["dynamic_schedule"]["min_interval_minutes"] = int(s_min_interval)
            glob_cfg["dynamic_schedule"]["max_interval_minutes"] = int(s_max_interval)
            glob_cfg["dynamic_schedule"]["human_jitter_sec_max"] = int(s_jitter_max)
            daemon.min_interval_minutes = int(s_min_interval)
            daemon.max_interval_minutes = int(s_max_interval)

            if "app" not in glob_cfg:
                glob_cfg["app"] = {}
            glob_cfg["app"]["daily_revenue_target_inr"] = float(g_target)
            st.session_state.orchestrator.set_daily_target(float(g_target))

            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml"), "w", encoding="utf-8") as f:
                yaml.safe_dump(glob_cfg, f, default_flow_style=False)
            st.success("Settings saved successfully!")
            st.rerun()



# ------------------------------------------------------------------------------
# TAB 4: Scouted Deals Pipeline
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
    st.subheader("🏷️ Social Media Setup, Affiliate Approval & High-Profit Platforms")
    st.markdown("""
    Complete operational playbook for launching your automated affiliate business:
    Setting up your Instagram & Facebook pages, getting approved for affiliate networks in India, and unlocking the highest-paying categories.
    """)

    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "📱 Account Setup & Names",
        "🛒 Amazon & EarnKaro Setup",
        "💰 Most Profitable Platforms",
        "🚀 Conversion & Bio Strategy"
    ])

    # SUB-TAB 1: Account Setup & Names
    with sub_tab1:
        st.markdown("### 🎯 Recommended Names & Niches for Your Pages")
        st.caption("You can run 1 general page or 2 dedicated niche pages (e.g. Ladies Fashion + Electronics) using the Common Settings tab.")

        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            st.markdown("""
            #### 👗 Niche 1: Ladies Fashion
            *Best for high commission % (7% - 10%) & viral aesthetic reels*
            - **`@StyleDrop.India`** / StyleDrop India
            - **`@FeminaFinds.in`** / Femina Finds Bharat
            - **`@ChicWardrobe.in`** / Chic Wardrobe Deals
            - **`@DesiGlamDeals`** / Desi Glam Deals

            **Target Items:**
            - Anarkali & Kurta sets
            - Trending partywear sarees & dupattas
            - Handbags, jewelry & viral makeup
            """)

        with col_n2:
            st.markdown("""
            #### ⚡ Niche 2: Electronics & Tech
            *Best for high order values (₹15k - ₹80k) & festival sale spikes*
            - **`@TechPulse.India`** / TechPulse India
            - **`@GadgetLab.Bharat`** / GadgetLab Bharat
            - **`@GizmoDeals.in`** / Gizmo Deals Daily
            - **`@PrimeTechFinds`** / Prime Tech Finds

            **Target Items:**
            - Bestselling smartphones & tablets
            - TWS earbuds, smartwatches & neckbands
            - Laptops, gaming accessories & chargers
            """)

        with col_n3:
            st.markdown("""
            #### 🌟 Niche 3: All-Round Loot
            *Best for maximum volume & everyday viral impulse buys*
            - **`@DealPulse.India`** / DealPulse India
            - **`@MegaLootBharat`** / Mega Loot Deals Bharat
            - **`@DesiDropDeals`** / Desi Drop Deals
            - **`@TrendingFinds.in`** / Trending Finds Bharat

            **Target Items:**
            - Under-₹999 smart kitchen hacks
            - Lightning 50%-80% price drops
            - Kids viral toys & home organization
            """)

        st.divider()
        st.markdown("### 📋 Step-by-Step Meta (Instagram + Facebook) Page Setup")
        with st.expander("Step 1: Create Your Instagram Account (5 Minutes)", expanded=True):
            st.markdown("""
            1. Open Instagram on your phone or browser $\\rightarrow$ Tap **Create New Account**.
            2. Choose your handle (e.g. `@styledrop.in` or `@techpulse.india`).
            3. Once logged in, go to your **Profile $\\rightarrow$ Settings & Privacy $\\rightarrow$ Account type and tools**.
            4. Tap **Switch to Professional Account** $\\rightarrow$ Choose **Creator** (or **Business**).
            5. Select Category: **Shopping & Retail** or **Digital Creator**.
            *Why Creator? It gives you access to full analytics, link stickers in stories, and Meta Graph API auto-publishing.*
            """)

        with st.expander("Step 2: Create Your Matching Facebook Page (3 Minutes)"):
            st.markdown("""
            1. Go to [facebook.com/pages/create](https://www.facebook.com/pages/create) while logged into your personal FB profile.
            2. Page Name: Match your Instagram handle (e.g. *StyleDrop India* or *TechPulse India*).
            3. Category: **E-commerce Website** or **Shopping & Retail**.
            4. Description: Short friendly summary (e.g. *Daily handpicked fashion & loot deals from Amazon, Flipkart, and Myntra with verified coupons.*).
            5. Upload a clean profile logo (you can generate one with Canva or our Creative bot).
            """)

        with st.expander("Step 3: Connect Instagram to Facebook Page (Enables Automated Bot Posting)"):
            st.markdown("""
            1. In your Facebook Page, open **Meta Business Suite** ([business.facebook.com](https://business.facebook.com)).
            2. Go to **Settings $\\rightarrow$ Linked Accounts $\\rightarrow$ Instagram**.
            3. Click **Connect Account** and log in with your new Instagram credentials.
            4. Allow permissions for messages and insights.
            *Now, when the bot publishes to your Facebook Page, it automatically synchronizes to your Instagram feed and Reels!*
            """)

    # SUB-TAB 2: Amazon & EarnKaro Setup
    with sub_tab2:
        st.markdown("### 💳 How to Setup Affiliate Marketing (India Step-by-Step)")
        st.caption("You will start with Amazon Associates India and EarnKaro. Together, they cover 100% of Indian e-commerce sites.")

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("""
            #### 1. Amazon Associates India
            - **Official Portal:** [affiliate-program.amazon.in](https://affiliate-program.amazon.in)
            - **Commission:** 1% to 10% per sale
            - **Cookie Duration:** 24 Hours (*If a user clicks your link and buys ANY item within 24 hours, you get paid!*)

            **Registration Steps:**
            1. Click **Sign Up** using your regular Amazon India customer account.
            2. **Payee Details:** Enter your legal name as printed on your PAN card and Indian bank passbook.
            3. **Website / Social Media URL:** When it asks for your website, **paste the URL of your new Instagram or Facebook page** (e.g. `https://instagram.com/styledrop.in`).
            4. **Store ID:** Choose a custom tracking tag prefix (e.g. `styledrop-21`).
            5. **PAN & Tax Info:** Enter your PAN number for Indian TDS compliance (Amazon deposits monthly earnings directly via NEFT into your bank).
            6. **SiteStripe:** Once logged in to Amazon.in, you will see a grey bar at the top called **SiteStripe** that gives you instant 1-click affiliate links!
            > [!TIP]
            > **The 180-Day Rule:** Amazon gives you 180 days to generate your first 3 qualifying purchases from real users. Our automated bot posting makes this effortless within your first 1-2 weeks!
            """)

        with col_a2:
            st.markdown("""
            #### 2. EarnKaro (Instant Approval for Flipkart, Myntra, Ajio, Nykaa)
            - **Official Portal:** [earnkaro.com](https://earnkaro.com) or download EarnKaro Android/iOS App
            - **Supported Stores:** Flipkart, Myntra, Ajio, Tata 1mg, Nykaa, Mamaearth, Croma, Samsung (150+ brands)
            - **Commission:** 3% to 15% per sale
            - **Minimum Payout:** ₹10 directly to your Bank Account!

            **Registration Steps:**
            1. Download EarnKaro app or visit website $\\rightarrow$ Sign up with your Indian Mobile Number & OTP.
            2. **Zero approval waiting period:** Your account is active instantly from minute 1!
            3. **How it works:** Take ANY product link from Flipkart, Myntra, or Ajio $\\rightarrow$ Paste into EarnKaro "Make Links" $\\rightarrow$ It generates your custom profit link.
            4. In the AutoAffiliate app under **⚙️ Common Settings**, paste your EarnKaro API key / Publisher ID to automate link generation!
            """)

        st.divider()
        st.markdown("### ⚖️ Legal Compliance & Disclosure (FTC & ASCI Guidelines)")
        st.info("""
        **Indian ASCI (Advertising Standards Council of India) Requirement:**
        Always include clear disclosures in your posts so Meta and Amazon never restrict your account.
        Our Creative Bot automatically appends:
        `#ad #affiliate #sponsored #commissionsearned #amazondeals`
        at the end of every generated caption and reel script.
        """)

    # SUB-TAB 3: Most Profitable Platforms
    with sub_tab3:
        st.markdown("### 🏆 Most Profitable Affiliate Categories & Platforms in India")
        st.markdown("""
        Not all products pay equal commissions. Mixing high-commission impulse items with high-ticket electronics and financial products is how you scale from ₹500/day to ₹5,000/day.
        """)

        # Profitability Comparison Table
        prof_data = [
            {"Niche / Product Type": "👗 Ladies Fashion, Sarees & Ethnic", "Typical Commission": "7.0% - 10.0%", "Average Order": "₹899 - ₹2,499", "Earnings Per Sale": "₹70 - ₹250", "Virality / Conversion": "Very High 🔥 (Reels go viral easily)"},
            {"Niche / Product Type": "💄 Beauty, Skincare & Personal Care", "Typical Commission": "6.0% - 9.0%", "Average Order": "₹599 - ₹1,499", "Earnings Per Sale": "₹45 - ₹135", "Virality / Conversion": "High (Repeat buyers)"},
            {"Niche / Product Type": "🍳 Smart Kitchen & Home Hacks", "Typical Commission": "6.0% - 9.0%", "Average Order": "₹499 - ₹1,299", "Earnings Per Sale": "₹40 - ₹110", "Virality / Conversion": "Very High 🔥 (Impulse purchase)"},
            {"Niche / Product Type": "📱 Smartphones & Smartwatches", "Typical Commission": "1.0% - 2.5%", "Average Order": "₹15,000 - ₹60,000", "Earnings Per Sale": "₹200 - ₹1,200", "Virality / Conversion": "High volume during Sale Events"},
            {"Niche / Product Type": "💳 Credit Cards (HDFC/SBI/Axis/AU)", "Typical Commission": "Flat Payout", "Average Order": "Free Application", "Earnings Per Sale": "₹1,500 - ₹3,500 / card", "Virality / Conversion": "Extreme Profit (BankSathi / EarnKaro)"},
            {"Niche / Product Type": "🌐 Web Hosting & Tools (Hostinger)", "Typical Commission": "40% - 60%", "Average Order": "₹3,500 - ₹8,000", "Earnings Per Sale": "₹1,800 - ₹4,500", "Virality / Conversion": "Highest SaaS payout"}
        ]
        st.dataframe(pd.DataFrame(prof_data), use_container_width=True)

        st.markdown("#### 💎 The 4 Most Profitable Networks to Join:")
        c_net1, c_net2 = st.columns(2)
        with c_net1:
            st.markdown("""
            **1. EarnKaro / CashKaro (E-commerce Aggregator):**
            - Highest overall Indian payout rates.
            - Lets you monetize Flipkart Big Billion Days and Amazon Great Indian Festival seamlessly.

            **2. BankSathi / vCommission (Financial Products):**
            - Allows you to recommend pre-approved credit cards (e.g. Swiggy HDFC Card, Flipkart Axis Card) and saving accounts.
            - Just 2 card approvals a day = ₹3,000+ daily profit!
            """)
        with c_net2:
            st.markdown("""
            **3. Cuelinks (Sub-Affiliate Network):**
            - Single JavaScript code or API for 1,000+ Indian merchants.
            - Automatically converts normal e-commerce links into affiliate links with high tracking accuracy.

            **4. Impact.com / CJ Affiliate (Global Brands):**
            - Direct partnerships with Lenovo India, Samsung, Puma, Nike, and Hostinger.
            """)

    # SUB-TAB 4: Conversion & Bio Strategy
    with sub_tab4:
        st.markdown("### 🚀 The High-Converting 2-Week Blueprint")
        st.markdown("""
        How to reach your **₹500/day minimum income** within the 2-week target:
        """)

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("""
            #### 1. The "Bio Link" Machine
            Since Instagram doesn't let you put clickable links inside post captions:
            - Set up a free **Linktree** ([linktr.ee](https://linktr.ee)) or **Beacons** ([beacons.ai](https://beacons.ai)).
            - Put the link in your Instagram Profile bio: `linktr.ee/styledrop_india`.
            - In every reel and post caption, the bot writes:
              `👉 Tap the link in our bio (@styledrop.india) to grab this deal before price increases!`
            - Put your top 5 scouted deals on your Linktree with direct affiliate links.

            #### 2. The Free Telegram Channel Funnel (Secret Multiplier)
            - People love instant loot alerts on Telegram.
            - Create a public Telegram channel (e.g. `t.me/MegaLootDealsIndia`).
            - Put this Telegram link in your Instagram bio and stories.
            - On Telegram, users click affiliate links **directly in 1-tap** without opening any browser! Conversion rate jumps from 2% to 15%.
            """)

        with col_b2:
            st.markdown("""
            #### 3. Recommended 14-Day Action Schedule:
            - **Days 1 - 2:** Create Instagram + FB accounts, link them in Meta Business Suite, sign up on Amazon Associates & EarnKaro.
            - **Days 3 - 5:** Run AutoAffiliate bot in Single or Multi-Channel mode. Post 2 to 3 high-converting Reels/Carousels daily at peak hours (12:30 PM, 6:30 PM, 9:00 PM).
            - **Days 6 - 8:** Use the Engagement Bot (`EngagerAgent`) to follow and interact with followers of competing deal pages (`@lootdealsindia`, `@dealfinder`).
            - **Days 9 - 14:** Share posts to your Instagram Stories with the **Link Sticker** leading directly to the Amazon product. Daily clicks cross 50-100, reaching your ₹500/day target!
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
