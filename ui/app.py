"""AutoAffiliate AI - Enterprise Admin Panel.
Complete Admin Panel Model featuring:
1. Executive Dashboard (KPIs, active channels, editable revenue & click tracker table)
2. Channel Accounts Manager (In-table editor for all accounts + 1-click presets & cards)
3. Niche & Account Mapping (In-table editable matrix of Niche -> Keywords -> Mapped Account)
4. E-Commerce Platforms (In-table editable platforms registry + live universal URL scraper)
5. Autonomous Autopilot (In-table bulk account activation + dynamic jitter timing)
6. Live Product Sandbox (100% Humanoid copy, zero icons/emojis, 4-slide carousels, AI vertical reels)
7. Content & Asset Library (In-table post status editor + visual card gallery)
8. Grok AI Command Console (Natural language employee bot dispatch)
9. Global Settings & Compliance (Target profit ₹X, Amazon tag, EarnKaro, disclosures)
10. Page Setup & Launch Playbook (Step-by-step Meta & Affiliate guides)
"""

import streamlit as st
import os
import sys
import time
import random
import yaml
from datetime import datetime, date
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
    log_daily_revenue,
    set_daily_revenue_row,
    bulk_save_daily_revenue,
    bulk_update_posts
)

# Page Configuration
st.set_page_config(
    page_title="AutoAffiliate AI | Admin Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Orchestrator & Daemon in Session State
if "orchestrator" not in st.session_state or not hasattr(st.session_state.orchestrator, "tested_product_ids"):
    st.session_state.orchestrator = AgentOrchestrator()

daemon = get_auto_daemon()

# Load saved theme preference
cfg_all = st.session_state.orchestrator._load_config()
default_theme = cfg_all.get("app", {}).get("theme_mode", "Light")

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = default_theme

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "agent": "Orchestrator",
            "content": "AutoAffiliate AI Enterprise Admin Console initialized. All bot agents are online. Use the sidebar to navigate between Accounts, Niches, Platforms, Autopilot, and the Live Product Sandbox."
        }
    ]

if "last_test_result" not in st.session_state:
    st.session_state.last_test_result = None

# ==============================================================================
# THEME STYLING INJECTION (LIGHT & DARK TEMPLATE SUPPORT)
# ==============================================================================
is_light = (st.session_state.theme_mode == "Light")
is_auto = (st.session_state.theme_mode == "Auto")

if is_light:
    st.markdown("""
    <style>
        /* Light Template (Modern Enterprise SaaS) */
        .stApp {
            background-color: #f8fafc !important;
            color: #0f172a !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        header[data-testid="stHeader"] {
            background-color: #f8fafc !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        .admin-brand {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #0284c7 0%, #4f46e5 50%, #9333ea 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2px;
        }
        .admin-badge {
            background: #e0e7ff;
            color: #3730a3;
            font-size: 0.72rem;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            border: 1px solid #c7d2fe;
            display: inline-block;
            margin-bottom: 12px;
        }
        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.08);
        }
        .kpi-title {
            color: #64748b;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            color: #0f172a;
            font-size: 1.85rem;
            font-weight: 800;
            margin: 4px 0;
        }
        .kpi-sub {
            color: #059669;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .account-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }
        .status-pill-active {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 9999px;
            font-weight: 700;
        }
        .status-pill-standby {
            background: #f1f5f9;
            color: #64748b;
            border: 1px solid #cbd5e1;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 9999px;
            font-weight: 600;
        }
        .table-hint {
            color: #0284c7;
            font-weight: 600;
            font-size: 0.85rem;
        }
    </style>
    """, unsafe_allow_html=True)
elif not is_auto:
    st.markdown("""
    <style>
        /* Dark Template (Modern Slate) */
        .stApp {
            background-color: #0b0f19 !important;
            color: #e2e8f0 !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        header[data-testid="stHeader"] {
            background-color: #0b0f19 !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b !important;
        }
        .admin-brand {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2px;
        }
        .admin-badge {
            background: #1e1b4b;
            color: #a5b4fc;
            font-size: 0.72rem;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 600;
            border: 1px solid #4338ca;
            display: inline-block;
            margin-bottom: 12px;
        }
        .kpi-card {
            background: #131b2e;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        .kpi-title {
            color: #94a3b8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            color: #f8fafc;
            font-size: 1.8rem;
            font-weight: 700;
            margin: 4px 0;
        }
        .kpi-sub {
            color: #34d399;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .account-card {
            background: #151d30;
            border: 1px solid #243048;
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .status-pill-active {
            background: #065f46;
            color: #34d399;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 9999px;
            font-weight: 600;
        }
        .status-pill-standby {
            background: #334155;
            color: #94a3b8;
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 9999px;
            font-weight: 600;
        }
        .table-hint {
            color: #38bdf8;
            font-weight: 600;
            font-size: 0.85rem;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # Auto / System Default mode
    st.markdown("""
    <style>
        .admin-brand {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2px;
        }
        .admin-badge {
            background: rgba(99, 102, 241, 0.2);
            color: inherit;
            font-size: 0.72rem;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 12px;
        }
        .kpi-card {
            background: var(--secondary-background-color);
            border-radius: 12px;
            padding: 16px;
        }
        .kpi-title {
            opacity: 0.8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin: 4px 0;
        }
        .table-hint {
            font-weight: 600;
            font-size: 0.85rem;
        }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR ADMIN NAVIGATION & CONTROLS
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="admin-brand">AutoAffiliate AI</div>', unsafe_allow_html=True)
    st.markdown('<span class="admin-badge">ENTERPRISE ADMIN v2.0</span>', unsafe_allow_html=True)

    # 1. Theme Template Selector
    st.caption("APPEARANCE THEME")
    theme_opts = ["☀️ Light Template", "🌑 Dark Template", "🔄 System Auto"]
    current_idx = 0 if st.session_state.theme_mode == "Light" else (1 if st.session_state.theme_mode == "Dark" else 2)
    selected_theme_label = st.radio(
        "Theme Template",
        theme_opts,
        index=current_idx,
        label_visibility="collapsed"
    )
    new_theme = "Light" if "Light" in selected_theme_label else ("Dark" if "Dark" in selected_theme_label else "Auto")
    if new_theme != st.session_state.theme_mode:
        st.session_state.theme_mode = new_theme
        cfg = st.session_state.orchestrator._load_config()
        if "app" not in cfg:
            cfg["app"] = {}
        cfg["app"]["theme_mode"] = new_theme
        try:
            from core.orchestrator import CONFIG_PATH
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
        except Exception:
            pass
        st.rerun()

    st.markdown("---")

    # Autopilot status pill in sidebar
    if daemon.is_running:
        st.markdown("<span style='color:#15803d if is_light else #34d399; font-weight:700;'>🟢 24/7 AUTOPILOT ACTIVE</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#64748b if is_light else #94a3b8; font-weight:600;'>⚪ AUTOPILOT STANDBY</span>", unsafe_allow_html=True)

    st.caption("ADMIN NAVIGATION")
    nav_selection = st.radio(
        "Navigation Menu",
        [
            "📊 Executive Dashboard",
            "🏢 Channel Accounts Manager",
            "🎯 Niche & Account Mapping",
            "🌐 E-Commerce Platforms",
            "🤖 Autonomous Autopilot",
            "⚡ Live Product Sandbox",
            "📱 Content & Media Library",
            "💬 Grok Command Console",
            "⚙️ Global Settings & Compliance",
            "🏷️ Page Setup & Launch Guide"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Quick Goal Tracker in Sidebar
    current_target = st.session_state.orchestrator.daily_target_inr
    rev_history = get_revenue_history(days=1)
    today_earned = rev_history[0]["estimated_earnings_inr"] if rev_history else 0.0
    progress_ratio = min(1.0, today_earned / max(1.0, current_target))

    st.caption("DAILY PROFIT TARGET")
    st.progress(progress_ratio)
    st.write(f"Today: **₹{today_earned:,.0f}** / Goal: **₹{current_target:,.0f}** ({int(progress_ratio*100)}%)")

    st.markdown("---")
    st.caption("QUICK SHORTCUT")
    if daemon.is_running:
        if st.button("⏸️ Pause Autopilot", use_container_width=True):
            daemon.stop_background_loop()
            st.rerun()
    else:
        if st.button("🚀 Start 24/7 Autopilot", use_container_width=True):
            daemon.start_background_loop()
            st.rerun()


# ==============================================================================
# TOP BREADCRUMB & CONSOLE HEADER
# ==============================================================================
header_c1, header_c2 = st.columns([3, 1.4])
with header_c1:
    st.markdown(f"### {nav_selection}")
with header_c2:
    all_prof = st.session_state.orchestrator.get_channel_profiles()
    en_prof = st.session_state.orchestrator.get_enabled_autopilot_profiles()
    header_color = "#0284c7" if is_light else "#38bdf8"
    st.markdown(f"<div style='text-align:right; margin-top:8px;'><span style='color:{header_color}; font-weight:700;'>{len(en_prof)} of {len(all_prof)} Accounts Active in Autopilot</span></div>", unsafe_allow_html=True)

st.divider()


# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_selection == "📊 Executive Dashboard":
    # 1. KPI Cards Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_rev = sum(h.get("estimated_earnings_inr", 0) for h in get_revenue_history(days=30))
    total_clicks = sum(h.get("clicks", 0) for h in get_revenue_history(days=30))
    total_orders = sum(h.get("orders", 0) for h in get_revenue_history(days=30))

    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Daily Revenue Target (X)</div>
            <div class="kpi-value">₹{current_target:,.0f}</div>
            <div class="kpi-sub">Configurable in Global Settings</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Estimated Logged</div>
            <div class="kpi-value">₹{total_rev:,.2f}</div>
            <div class="kpi-sub">Across All Channels</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Referral Clicks</div>
            <div class="kpi-value">{total_clicks}</div>
            <div class="kpi-sub">Amazon & Multi-Platform</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Orders Converted</div>
            <div class="kpi-value">{total_orders}</div>
            <div class="kpi-sub">Qualifying Purchases</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. IN-TABLE EDITABLE REVENUE & METRICS TRACKER
    st.subheader("📈 Daily Revenue & Performance Tracker (In-Table Editable)")
    st.markdown("<span class='table-hint'>✏️ Edit clicks, orders, earnings, or notes directly in the table below. Click 'Save Table Changes' to persist.</span>", unsafe_allow_html=True)

    rev_rows = get_revenue_history(days=14)
    if not rev_rows:
        # Default placeholder row for today if empty
        rev_rows = [{
            "log_date": date.today().isoformat(),
            "target_inr": float(current_target),
            "estimated_earnings_inr": 0.0,
            "clicks": 0,
            "orders": 0,
            "notes": "First autonomous cycle launched"
        }]

    df_rev = pd.DataFrame(rev_rows)
    # Ensure expected columns
    for col, default_val in [("log_date", date.today().isoformat()), ("target_inr", 500.0), ("estimated_earnings_inr", 0.0), ("clicks", 0), ("orders", 0), ("notes", "")]:
        if col not in df_rev.columns:
            df_rev[col] = default_val

    df_rev = df_rev[["log_date", "target_inr", "estimated_earnings_inr", "clicks", "orders", "notes"]]

    edited_rev_df = st.data_editor(
        df_rev,
        column_config={
            "log_date": st.column_config.TextColumn("Date (YYYY-MM-DD)", required=True),
            "target_inr": st.column_config.NumberColumn("Target (INR ₹)", min_value=0.0, step=100.0),
            "estimated_earnings_inr": st.column_config.NumberColumn("Earnings (INR ₹)", min_value=0.0, step=10.0),
            "clicks": st.column_config.NumberColumn("Total Clicks", min_value=0, step=1),
            "orders": st.column_config.NumberColumn("Orders", min_value=0, step=1),
            "notes": st.column_config.TextColumn("Notes / Channels")
        },
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_revenue"
    )

    col_rv_save, col_rv_info = st.columns([1.5, 3])
    with col_rv_save:
        if st.button("💾 Save Revenue Table Changes", use_container_width=True, key="btn_save_revenue_table"):
            bulk_save_daily_revenue(edited_rev_df.to_dict("records"))
            st.success("Revenue log saved successfully!")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Channel Matrix Overview
    st.subheader("🏢 Connected Social Media Accounts & Niche Matrix")
    profiles = st.session_state.orchestrator.get_channel_profiles()

    prof_data = []
    for p in profiles:
        prof_data.append({
            "Account Name": p.get("name"),
            "Dedicated Niche": p.get("focus_niche", "all").upper(),
            "Instagram Handle": p.get("instagram_username") or "Not configured",
            "Facebook Page ID": p.get("facebook_page_id") or "Not configured",
            "Autopilot Status": "🟢 ACTIVE (Independent)" if p.get("enabled_for_autopilot") else "⚪ STANDBY"
        })
    st.dataframe(pd.DataFrame(prof_data), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Recent Real-Time Bot Operations
    st.subheader("🔍 Operational Audit Trail (Live Bot Actions)")
    logs = get_recent_logs(limit=10)
    if logs:
        df_logs = pd.DataFrame(logs)[["created_at", "agent_name", "action", "status", "details"]]
        df_logs.columns = ["Timestamp", "Agent", "Action Description", "Status", "Technical Details"]
        st.dataframe(df_logs, use_container_width=True)


# ==============================================================================
# VIEW 2: CHANNEL ACCOUNTS MANAGER
# ==============================================================================
elif nav_selection == "🏢 Channel Accounts Manager":
    st.markdown("""
    Manage all your social media business accounts.
    **Each account operates 100% independently:**
    - Ladies Fashion posts exclusively to Ladies Fashion FB & Insta.
    - Men's Fashion posts exclusively to Men's Fashion FB & Insta.
    - Electronics posts exclusively to Electronics FB & Insta.
    """)

    # 1. IN-TABLE EDITABLE ACCOUNTS TABLE
    st.subheader("📋 Registered Accounts (In-Table Editable)")
    st.markdown("<span class='table-hint'>✏️ Edit account names, handles, assigned niches, and autopilot checkboxes directly inside this table. Click 'Save All Account Changes' to update.</span>", unsafe_allow_html=True)

    profiles = st.session_state.orchestrator.get_channel_profiles()
    df_acc = pd.DataFrame(profiles)
    for col, def_val in [("id", "channel"), ("name", "New Account"), ("focus_niche", "fashion"), ("instagram_username", ""), ("facebook_page_id", ""), ("telegram_channel_id", ""), ("enabled_for_autopilot", True)]:
        if col not in df_acc.columns:
            df_acc[col] = def_val

    df_acc_view = df_acc[["id", "name", "focus_niche", "instagram_username", "facebook_page_id", "telegram_channel_id", "enabled_for_autopilot"]]

    niche_options = ["fashion", "mens_fashion", "mobiles", "electronics", "toys", "kitchen", "beauty", "home_decor", "fitness", "general", "all"]

    edited_acc_df = st.data_editor(
        df_acc_view,
        column_config={
            "id": st.column_config.TextColumn("Account Key / ID", required=True),
            "name": st.column_config.TextColumn("Display Name", required=True),
            "focus_niche": st.column_config.SelectboxColumn("Assigned Niche", options=niche_options, required=True),
            "instagram_username": st.column_config.TextColumn("Instagram Handle"),
            "facebook_page_id": st.column_config.TextColumn("Facebook Page ID"),
            "telegram_channel_id": st.column_config.TextColumn("Telegram Channel"),
            "enabled_for_autopilot": st.column_config.CheckboxColumn("Autopilot Enabled", default=True)
        },
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_accounts"
    )

    col_acc_save, col_acc_act = st.columns([1.5, 3])
    with col_acc_save:
        if st.button("💾 Save All Account Changes", use_container_width=True, key="btn_save_accounts_table"):
            st.session_state.orchestrator.bulk_save_channel_profiles(edited_acc_df.to_dict("records"))
            st.success("Channel accounts saved successfully!")
            st.rerun()

    st.markdown("---")

    # 2. Quick Presets Bar
    st.markdown("#### ⚡ 1-Click Presets & Quick Focus:")
    col_p1, col_p2, col_p3 = st.columns(3)
    has_mens = any(p["id"] == "mens_fashion" for p in profiles)

    with col_p1:
        if not has_mens:
            if st.button("👔 1-Click Add Men's Fashion (`UrbanGent India`)", use_container_width=True):
                st.session_state.orchestrator.save_channel_profile({
                    "id": "mens_fashion",
                    "name": "UrbanGent India (Men's Fashion)",
                    "focus_niche": "mens_fashion",
                    "description": "Exclusively Men's Formal & Casual Shirts, Jeans, Sneakers and Grooming",
                    "instagram_username": "@urbangent.in",
                    "facebook_page_id": "",
                    "telegram_channel_id": "",
                    "enabled_for_autopilot": True
                })
                st.success("UrbanGent India added successfully!")
                st.rerun()
        else:
            st.info("✓ Men's Fashion (`UrbanGent India`) is registered.")

    with col_p2:
        if st.button("👗 Focus Active View on Ladies Fashion", use_container_width=True):
            st.session_state.orchestrator.set_active_profile("fashion")
            st.rerun()

    with col_p3:
        if st.button("⚡ Focus Active View on Electronics", use_container_width=True):
            st.session_state.orchestrator.set_active_profile("electronics")
            st.rerun()

    st.markdown("---")

    # 3. Existing Connected Accounts Visual Cards
    st.markdown("### 📱 Active Profiles Overview")
    curr_active = st.session_state.orchestrator.get_active_profile()

    for prof in profiles:
        pid = prof.get("id")
        is_act = (pid == curr_active.get("id"))
        is_ap_enabled = prof.get("enabled_for_autopilot", False)

        with st.container():
            col_a1, col_a2, col_a3 = st.columns([2.8, 2.2, 1.4])
            with col_a1:
                st.markdown(f"#### {prof.get('name')}")
                st.caption(prof.get("description", ""))
                st.markdown(f"**Target Niche:** `{prof.get('focus_niche', 'all').upper()}`")
            with col_a2:
                st.markdown(f"• **Instagram:** `{prof.get('instagram_username') or 'Not configured'}`")
                st.markdown(f"• **Facebook Page ID:** `{prof.get('facebook_page_id') or 'Not configured'}`")
                st.markdown(f"• **Telegram Channel:** `{prof.get('telegram_channel_id') or 'Not configured'}`")
            with col_a3:
                if not is_act:
                    if st.button("Set as Active Focus", key=f"btn_set_act_{pid}", use_container_width=True):
                        st.session_state.orchestrator.set_active_profile(pid)
                        st.rerun()
                else:
                    active_color = "#15803d" if is_light else "#34d399"
                    st.markdown(f"<span style='color:{active_color}; font-weight:700;'>🟢 ACTIVE FOCUS</span>", unsafe_allow_html=True)
            st.divider()


# ==============================================================================
# VIEW 3: NICHE & ACCOUNT MAPPING
# ==============================================================================
elif nav_selection == "🎯 Niche & Account Mapping":
    st.markdown("""
    ### 🎯 Niche-to-Account Mapping Matrix
    Configure which product niches and keywords route to which social media accounts.
    """)

    st.info("""
    **How Niche Mapping Works:**
    1. **Niche & Keywords:** Tells the Scout Bot what exact products to search on Amazon, Flipkart, Myntra, etc.
    2. **Mapped Account:** Tells the Marketer Bot which Facebook Page and Instagram Account should publish the deal.
    3. **Autopilot Routing:** When Autopilot triggers for an account, it looks up its mapped niche and keywords, finds fresh deals, generates 100% humanoid copy, and publishes exclusively to that account.
    """)

    # 1. IN-TABLE EDITABLE NICHE MAPPING MATRIX
    st.subheader("📋 Niche Mapping Matrix (In-Table Editable)")
    st.markdown("<span class='table-hint'>✏️ Edit Niche Names, Keywords, Mapped Accounts, and Commission Rates directly in the table. Add or delete rows as needed!</span>", unsafe_allow_html=True)

    mappings = st.session_state.orchestrator.get_niche_mappings()
    profiles = st.session_state.orchestrator.get_channel_profiles()
    profile_ids = [p["id"] for p in profiles]

    df_map = pd.DataFrame(mappings)
    for col, def_val in [("id", "niche"), ("name", "New Niche"), ("keywords", "query1, query2"), ("mapped_account_id", profile_ids[0] if profile_ids else "fashion"), ("commission_rate", "6% - 9%")]:
        if col not in df_map.columns:
            df_map[col] = def_val

    df_map_view = df_map[["id", "name", "keywords", "mapped_account_id", "commission_rate"]]

    edited_map_df = st.data_editor(
        df_map_view,
        column_config={
            "id": st.column_config.TextColumn("Niche ID / Slug", required=True),
            "name": st.column_config.TextColumn("Niche Display Name", required=True),
            "keywords": st.column_config.TextColumn("Target Search Keywords (Comma-separated)", required=True),
            "mapped_account_id": st.column_config.SelectboxColumn("Mapped Account Profile", options=profile_ids, required=True),
            "commission_rate": st.column_config.TextColumn("Commission Rate (e.g. 7% - 10%)")
        },
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_niche_mapping"
    )

    col_map_save, col_map_hint = st.columns([1.5, 3])
    with col_map_save:
        if st.button("💾 Save Niche Mapping Table", use_container_width=True, key="btn_save_niche_map_table"):
            st.session_state.orchestrator.bulk_save_niche_mappings(edited_map_df.to_dict("records"))
            st.success("Niche mapping matrix saved successfully!")
            st.rerun()

    st.markdown("---")

    # 2. Add New Niche & Map to Account Form
    st.subheader("➕ Quick Add Niche & Route to Account")
    with st.form("form_add_niche_map"):
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            n_name = st.text_input("Niche Name", placeholder="e.g. Men's Casual & Formal Shirts")
            n_id = st.text_input("Niche Identifier", placeholder="e.g. mens_shirts")
            n_keywords = st.text_input("Target Search Keywords (Comma-separated)", placeholder="e.g. men linen shirts, casual slim fit shirt, formal office shirts")
        with c_m2:
            n_target_acc = st.selectbox(
                "Map to Social Media Account",
                [p["id"] for p in profiles],
                format_func=lambda pid: next((p["name"] for p in profiles if p["id"] == pid), pid),
                help="Deals found for this niche will automatically be posted to this account"
            )
            n_comm = st.text_input("Expected Commission Rate", value="6% - 10%")

        if st.form_submit_button("Save Niche Mapping"):
            if n_name and n_keywords:
                clean_id = (n_id or n_name).lower().replace(" ", "_")
                st.session_state.orchestrator.save_niche_mapping({
                    "id": clean_id,
                    "name": n_name,
                    "keywords": n_keywords,
                    "mapped_account_id": n_target_acc,
                    "commission_rate": n_comm
                })
                st.success(f"Niche '{n_name}' mapped to '{n_target_acc}' successfully!")
                st.rerun()


# ==============================================================================
# VIEW 4: E-COMMERCE PLATFORMS
# ==============================================================================
elif nav_selection == "🌐 E-Commerce Platforms":
    st.markdown("""
    ### 🌐 E-Commerce Platforms & Affiliate Rewriter Registry
    Configure your affiliate partnerships. AutoAffiliate AI supports direct tagging and aggregator deep-linking for **Amazon, Flipkart, Myntra, Nykaa, Ajio, Meesho, Croma**, and any custom e-commerce site.
    """)

    # 1. IN-TABLE EDITABLE PLATFORMS REGISTRY
    st.subheader("🛍️ Active E-Commerce Networks (In-Table Editable)")
    st.markdown("<span class='table-hint'>✏️ Edit tracking tags, affiliate parameters, and domains directly in the table. Add any new store row at the bottom!</span>", unsafe_allow_html=True)

    platforms = st.session_state.orchestrator.scout.tagger.platforms

    plat_rows = []
    for pk, pv in platforms.items():
        plat_rows.append({
            "key": pk,
            "name": pv.get("name", pk.capitalize()),
            "domain": pv.get("domains", [""])[0],
            "param": pv.get("param", "tag"),
            "id": pv.get("id", "affiliate")
        })

    df_plat = pd.DataFrame(plat_rows)

    edited_plat_df = st.data_editor(
        df_plat,
        column_config={
            "key": st.column_config.TextColumn("Platform Key", required=True),
            "name": st.column_config.TextColumn("Network Name", required=True),
            "domain": st.column_config.TextColumn("Primary Domain (e.g. myntra.com)", required=True),
            "param": st.column_config.TextColumn("Affiliate Parameter (e.g. tag, affid, utm_source)", required=True),
            "id": st.column_config.TextColumn("Your Tracking Tag / ID", required=True)
        },
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor_platforms"
    )

    col_plat_save, col_plat_hint = st.columns([1.5, 3])
    with col_plat_save:
        if st.button("💾 Save Platform Table Changes", use_container_width=True, key="btn_save_platforms_table"):
            st.session_state.orchestrator.bulk_save_platforms(edited_plat_df.to_dict("records"))
            st.success("E-commerce platforms saved successfully!")
            st.rerun()

    st.markdown("---")

    col_plat1, col_plat2 = st.columns(2)

    # 2. Add New Platform Form
    with col_plat1:
        st.subheader("➕ Quick Register Store")
        with st.form("form_reg_platform"):
            np_name = st.text_input("Platform Name", placeholder="e.g. Nykaa, Bewakoof, Purplle")
            np_domain = st.text_input("Domain Name", placeholder="e.g. nykaa.com, purplle.com")
            np_param = st.text_input("Affiliate URL Parameter", value="utm_source", placeholder="e.g. tag, affid, utm_source")
            np_id = st.text_input("Your Affiliate ID / Publisher Tag", placeholder="e.g. mypartner_tag")
            if st.form_submit_button("Register Platform"):
                if np_name and np_domain:
                    st.session_state.orchestrator.scout.tagger.add_platform(
                        key=np_name.lower().replace(" ", "_"),
                        name=np_name,
                        domain=np_domain,
                        param=np_param or "tag",
                        affiliate_id=np_id or "affiliate"
                    )
                    st.success(f"Platform '{np_name}' registered successfully!")
                    st.rerun()

    # 3. Universal URL Importer & Test Scraper
    with col_plat2:
        st.subheader("🔍 Universal Link Tester & Importer")
        st.caption("Paste ANY live product URL from Amazon, Flipkart, Myntra, Nykaa, Ajio, Meesho, Croma, etc.")
        imp_url = st.text_input("Product URL", placeholder="https://www.myntra.com/shirts/brand/123456...")
        if st.button("Extract Data & Convert to Affiliate Link"):
            if imp_url:
                with st.spinner("Scraping metadata, pricing, and images..."):
                    item = st.session_state.orchestrator.scout.import_product_from_url(
                        imp_url,
                        target_profit=current_target
                    )
                    if item:
                        st.success(f"✓ Extracted from {item.get('platform')}: {item.get('title')[:45]}!")
                        st.write(f"• **Deal Price:** ₹{int(item.get('deal_price', 0)):,} (MRP: ₹{int(item.get('original_price', 0)):,})")
                        aff_link = item.get('affiliate_url', '')
                        if 'tinyurl.com' in aff_link or item.get('is_cloaked'):
                            st.write(f"• **Customer Deal Link (Cloaked):** `{aff_link}` 🛡️ *(EarnKaro hidden from followers)*")
                            if item.get("raw_affiliate_url"):
                                with st.expander("🔍 View Underlying EarnKaro Tracking URL (Publisher Verification)"):
                                    st.code(item['raw_affiliate_url'])
                        else:
                            st.write(f"• **Auto-Tagged Link:** `{aff_link}`")
                        if item.get("image_url"):
                            st.image(item["image_url"], width=200)

    st.markdown("---")

    # 4. The EarnKaro Master Aggregator Method
    st.subheader("💎 The 1-Click Multi-Store Method (EarnKaro)")
    st.info("""
    **How to earn from 150+ Indian platforms with zero approvals needed:**
    - If you do not have direct affiliate accounts with Myntra, Nykaa, or Ajio, you can use **EarnKaro** ([earnkaro.com](https://earnkaro.com)).
    - EarnKaro has pre-approved partnerships with Flipkart, Myntra, Ajio, Nykaa, Mamaearth, Croma, Samsung, and Tata 1mg.
    - Simply paste your EarnKaro API Key or Publisher ID in **Global Settings**, and AutoAffiliate will automatically route those product links through your EarnKaro account!
    """)


# ==============================================================================
# VIEW 5: AUTONOMOUS AUTOPILOT
# ==============================================================================
elif nav_selection == "🤖 Autonomous Autopilot":
    st.markdown("""
    ### 🤖 Autonomous Multi-Channel Dispatcher
    Run 24/7 autonomous cycles with **independent channel execution** and **dynamic jitter timing**.
    """)

    all_profiles = st.session_state.orchestrator.get_channel_profiles()
    enabled_profiles = st.session_state.orchestrator.get_enabled_autopilot_profiles()

    # 1. IN-TABLE EDITABLE AUTOPILOT ACTIVATION
    st.subheader("📋 Channel Autopilot Activation Table (In-Table Editable)")
    st.markdown("<span class='table-hint'>✏️ Toggle the checkbox for accounts you want active in the 24/7 autonomous loop, then click 'Save Autopilot Selection'.</span>", unsafe_allow_html=True)

    ap_rows = []
    for p in all_profiles:
        ap_rows.append({
            "id": p["id"],
            "name": p["name"],
            "focus_niche": p.get("focus_niche", "all").upper(),
            "enabled_for_autopilot": bool(p.get("enabled_for_autopilot", False))
        })

    df_ap = pd.DataFrame(ap_rows)
    edited_ap_df = st.data_editor(
        df_ap,
        column_config={
            "id": st.column_config.TextColumn("Account Key", disabled=True),
            "name": st.column_config.TextColumn("Channel Account Name", disabled=True),
            "focus_niche": st.column_config.TextColumn("Dedicated Niche", disabled=True),
            "enabled_for_autopilot": st.column_config.CheckboxColumn("Run in 24/7 Autopilot", default=True)
        },
        use_container_width=True,
        key="data_editor_autopilot_channels"
    )

    col_ap_btn1, col_ap_btn2, col_ap_btn3 = st.columns([1.5, 1.5, 1.5])
    with col_ap_btn1:
        if st.button("💾 Save Autopilot Selection", use_container_width=True, key="btn_save_ap_table"):
            for row in edited_ap_df.to_dict("records"):
                st.session_state.orchestrator.set_profile_autopilot_enabled(row["id"], bool(row["enabled_for_autopilot"]))
            st.success("Autopilot preferences saved!")
            st.rerun()

    with col_ap_btn2:
        if daemon.is_running:
            if st.button("⏸️ PAUSE AUTOPILOT", use_container_width=True, key="ap_btn_stop"):
                daemon.stop_background_loop()
                st.rerun()
        else:
            if st.button("🚀 START 24/7 AUTOPILOT", use_container_width=True, key="ap_btn_start"):
                daemon.start_background_loop()
                st.rerun()

    with col_ap_btn3:
        if st.button("⚡ Run 1 Cycle Now (All Selected)", use_container_width=True, key="ap_btn_run_now"):
            with st.spinner("Executing independent cycles across selected accounts..."):
                cycle_results = daemon.run_one_autonomous_cycle()
                st.session_state["last_cycle_results"] = cycle_results
                st.success("Autonomous cycle complete!")
                st.rerun()

    # Dynamic Timing Banner
    last_str = daemon.last_run_time.strftime("%I:%M %p") if daemon.last_run_time else "None yet"
    next_str = daemon.next_run_time.strftime("%I:%M %p") if daemon.next_run_time else "Calculated dynamically on launch"
    en_names = [p["name"] for p in enabled_profiles]

    banner_bg = "#ecfdf5" if is_light else "#064e3b"
    banner_border = "#6ee7b7" if is_light else "#059669"
    banner_text = "#064e3b" if is_light else "#e2e8f0"
    banner_badge_bg = "#a7f3d0" if is_light else "#047857"
    banner_badge_text = "#065f46" if is_light else "#a7f3d0"

    st.markdown(f"""
    <div style="background:{banner_bg}; border:1px solid {banner_border}; border-radius:10px; padding:16px; margin: 16px 0; color:{banner_text};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:1.1rem;">{'🟢 AUTOPILOT ENGINE RUNNING' if daemon.is_running else '⚪ AUTOPILOT ENGINE STANDBY'}</strong>
            <span style="color:{banner_badge_text}; background:{banner_badge_bg}; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">🛡️ Anti-Spam Jitter Pacing Active</span>
        </div>
        <div style="font-size:0.92rem; margin-top:8px; line-height:1.6;">
            • <b>Active Independent Accounts:</b> {', '.join(en_names) if en_names else 'None selected'}<br>
            • <b>Dynamic Timing:</b> No fixed schedule (static 12:30/18:30 removed). Next run dynamically picked between 90m to 210m with random jitter.<br>
            • <b>Humanoid Content:</b> 100% clean copy with ZERO emojis and ZERO special characters.<br>
            • <b>Organic Growth:</b> Finds new people daily, likes recent posts, leaves authentic comments, and invites high-intent users.<br>
            • <b>Telemetry:</b> Completed Cycle #{daemon.cycle_count} • Last run: {last_str} • Next dynamic window: {next_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "last_cycle_results" in st.session_state and st.session_state["last_cycle_results"]:
        l_res = st.session_state["last_cycle_results"]
        with st.expander("📋 Last Execution Cycle Report", expanded=True):
            st.write(f"**Accounts Processed:** {l_res.get('channels_processed', 0)}")
            for d in l_res.get("details", []):
                st.success(f"✓ **[{d['channel']}]** ({d['niche'].upper()}): Discovered '{d['product']}', published Post #{d['post_id']} to FB & Instagram, and executed {d['growth_actions']} organic growth actions.")


# ==============================================================================
# VIEW 6: LIVE PRODUCT TEST SANDBOX
# ==============================================================================
elif nav_selection == "⚡ Live Product Sandbox":
    st.subheader("⚡ Instant Live Product Test Sandbox")
    st.markdown("""
    Test the entire autonomous pipeline on demand:
    1. Scrapes the **next real live product** from Amazon India & Flipkart (no hardcoded data).
    2. Generates **100% Humanoid Copy** (Zero icons, zero emojis, zero decorative special characters).
    3. Downloads multiple gallery pictures & generates a 4-slide Instagram Carousel.
    4. Compiles a 15-second vertical AI Reel video with neural voiceover.
    """)

    t_plat, t_cat_col, t_query_col, t_btn_col = st.columns([1.5, 1.8, 1.8, 1.4])
    with t_plat:
        test_platform = st.selectbox(
            "Platform Source",
            ["auto", "amazon", "flipkart"],
            format_func=lambda x: {"auto": "⚡ Auto (Amazon + Flipkart)", "amazon": "📦 Amazon India", "flipkart": "🛍️ Flipkart"}.get(x, x)
        )
    with t_cat_col:
        test_cat = st.selectbox(
            "Category",
            ["fashion", "mens_fashion", "mobiles", "electronics", "toys", "kitchen", "beauty", "all"],
            format_func=lambda x: {
                "fashion": "👗 Ladies Fashion & Dresses",
                "mens_fashion": "👔 Men's Fashion & Shirts",
                "mobiles": "📱 High-Ticket Mobiles & iPhones",
                "electronics": "💻 Electronics & Tech",
                "toys": "🧸 Kids Toys & Games",
                "kitchen": "🍳 Home & Kitchen Finds",
                "beauty": "💄 Beauty & Personal Care",
                "all": "⚡ General Deals & Bestsellers"
            }.get(x, x)
        )
    with t_query_col:
        test_query = st.text_input("Or Custom Search Query", placeholder="e.g. iPhone 16, Men linen shirt, Anarkali kurti")
    with t_btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("⚡ Test Next Product Now", use_container_width=True)

    if run_btn:
        with st.spinner(f"Scout & Creative bots fetching next deal in '{test_query or test_cat}'..."):
            res = st.session_state.orchestrator.test_next_product(
                category=test_cat,
                query=test_query if test_query else None,
                platform=test_platform
            )
            if res.get("success"):
                st.session_state.last_test_result = res
                st.toast(f"✅ Fetched fresh live deal from {res.get('platform')}!", icon="⚡")
                st.rerun()
            else:
                st.error(res.get("error", "Failed to retrieve product."))

    if st.session_state.last_test_result:
        res = st.session_state.last_test_result
        p = res["product"]
        pst = res["post"]
        t_num = res.get("test_number", 1)

        st.divider()
        hl_color = "#0284c7" if is_light else "#38bdf8"
        chk_color = "#15803d" if is_light else "#34d399"
        st.markdown(f"### 🔍 Live Test Results — <span style='color:{hl_color};'>[{p.get('platform')}] {p['title'][:50]}</span> (Test #{t_num})", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{chk_color}; font-weight:600;'>✓ 100% Humanoid Copy Verified: Zero emojis & Zero special characters</span>", unsafe_allow_html=True)

        r_img_col, r_info_col = st.columns([1.5, 2.5])
        with r_img_col:
            v_path = pst.get("video_path")
            if v_path and os.path.exists(v_path):
                st.video(v_path)
                st.caption("🎬 9:16 AI Reel (With Neural Voiceover)")

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
                st.image(p["image_url"], use_container_width=True)

            st.metric("Deal Price", f"₹{int(p['deal_price']):,}", f"-{int(p['discount_pct'])}% OFF")
            st.metric("Est. Commission", f"₹{p.get('est_comm_per_sale', 0)} / sale", f"~{p.get('units_to_goal', 1)} sales to hit ₹{current_target:,.0f}")

        with r_info_col:
            aff_link = p.get('affiliate_url', '')
            if 'tinyurl.com' in aff_link or p.get('is_cloaked') or 'earnkaro.com' in p.get('raw_affiliate_url', ''):
                st.markdown(f"🔗 **Customer Deal Link (Cloaked):** `{aff_link}` 🛡️ *(EarnKaro hidden from followers)*")
                if p.get("raw_affiliate_url"):
                    with st.expander("🔍 View Underlying EarnKaro Tracking URL (Publisher Verification)"):
                        st.code(p['raw_affiliate_url'])
            else:
                st.markdown(f"🔗 **Live Affiliate URL:** `{aff_link}`")
            st.markdown(f"**Headline Hook:** *{pst['headline']}*")

            with st.expander("📝 View Humanoid Caption (Zero Icons/Emojis)", expanded=True):
                st.text_area("Caption", pst["caption"], height=160)
                st.caption(f"**Hashtags:** {pst['hashtags']}")

            with st.expander("🎬 15-Second Viral Reel Script"):
                st.code(pst.get('reel_script', ''), language="markdown")

            target_account = st.session_state.orchestrator.get_active_profile()
            if st.button(f"🚀 Publish Test Post to [{target_account.get('name')}]", use_container_width=True):
                with st.spinner("Publishing across Meta & Telegram..."):
                    pub_res = st.session_state.orchestrator.marketer.publish_approved_post(pst, channel_profile=target_account)
                    st.success("Test post published successfully!")


# ==============================================================================
# VIEW 7: CONTENT & MEDIA LIBRARY
# ==============================================================================
elif nav_selection == "📱 Content & Media Library":
    st.subheader("📱 Content & Media Asset Deck")

    tab_lib1, tab_lib2 = st.tabs(["📋 In-Table Post Manager", "🗂️ Visual Cards & Media Player"])

    posts = get_posts(limit=30)

    with tab_lib1:
        st.markdown("<span class='table-hint'>✏️ Fast Bulk Management: Edit headline hooks and post statuses (draft, approved, published) directly in this table! Click 'Save Post Table Changes'.</span>", unsafe_allow_html=True)
        if not posts:
            st.info("No posts created yet. Go to 'Live Product Sandbox' to generate your first post.")
        else:
            df_posts = pd.DataFrame(posts)
            for col, def_val in [("id", 1), ("headline", ""), ("platform", "instagram"), ("status", "draft"), ("created_at", "")]:
                if col not in df_posts.columns:
                    df_posts[col] = def_val

            df_posts_view = df_posts[["id", "headline", "platform", "status", "created_at"]]

            status_opts = ["draft", "approved", "published", "archived"]

            edited_posts_df = st.data_editor(
                df_posts_view,
                column_config={
                    "id": st.column_config.NumberColumn("Post ID", disabled=True),
                    "headline": st.column_config.TextColumn("Headline Hook", required=True),
                    "platform": st.column_config.SelectboxColumn("Target Platform", options=["instagram", "facebook", "telegram", "meta_all"]),
                    "status": st.column_config.SelectboxColumn("Post Status", options=status_opts, required=True),
                    "created_at": st.column_config.TextColumn("Created At", disabled=True)
                },
                use_container_width=True,
                key="data_editor_posts"
            )

            if st.button("💾 Save Post Table Changes", key="btn_save_posts_table"):
                bulk_update_posts(edited_posts_df.to_dict("records"))
                st.success("Post updates saved successfully!")
                st.rerun()

    with tab_lib2:
        if not posts:
            st.info("No posts created yet.")
        else:
            for post in posts:
                with st.container():
                    cp_col1, cp_col2 = st.columns([1.5, 2.5])
                    with cp_col1:
                        st.markdown(f"#### Post #{post['id']}")
                        vp = post.get("video_path")
                        if vp and os.path.exists(vp):
                            st.video(vp)
                        media = post.get("media_paths", [])
                        if media and os.path.exists(media[0]):
                            st.image(media[0], use_container_width=True)

                        status_color = "#15803d" if (is_light and post["status"] == "published") else ("#34d399" if post["status"] == "published" else "#f59e0b")
                        st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:bold;'>{post['status'].upper()}</span>", unsafe_allow_html=True)
                        if post["status"] != "published":
                            target_account = st.session_state.orchestrator.get_active_profile()
                            if st.button(f"🚀 Approve & Publish", key=f"lib_pub_{post['id']}", use_container_width=True):
                                with st.spinner("Publishing..."):
                                    res = st.session_state.orchestrator.marketer.publish_approved_post(post, channel_profile=target_account)
                                    st.success("Post successfully published!")
                                    st.rerun()

                    with cp_col2:
                        st.markdown(f"**Headline Hook:** {post.get('headline', '')}")
                        with st.expander("📝 Full Caption & Hashtags", expanded=True):
                            st.text_area("Caption", post.get("caption", ""), height=150, key=f"cap_lib_{post['id']}")
                            st.caption(f"**Hashtags:** {post.get('hashtags', '')}")
                        with st.expander("🎬 15-Second Reel Script"):
                            st.code(post.get("reel_script", ""), language="markdown")
                    st.divider()


# ==============================================================================
# VIEW 8: GROK AI COMMAND CONSOLE
# ==============================================================================
elif nav_selection == "💬 Grok Command Console":
    st.subheader("⚡ Grok Agent Command Console")
    st.caption("You have full admin rights. Command your bot employees in natural language.")

    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="⚡"):
                st.markdown(f"**[{msg.get('agent', 'Orchestrator')}]:**\n\n{msg['content']}")

    if user_prompt := st.chat_input("Command your team (e.g. 'Test next iPhone', 'Set target to 2000', 'Run full autopilot cycle')..."):
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


# ==============================================================================
# VIEW 9: GLOBAL SETTINGS & COMPLIANCE
# ==============================================================================
elif nav_selection == "⚙️ Global Settings & Compliance":
    st.subheader("⚙️ Global Settings, Anti-Bot Safety & Legal Disclosures")
    glob_cfg = st.session_state.orchestrator._load_config()
    dyn_cfg = glob_cfg.get("dynamic_schedule", {})

    with st.form("form_all_global_settings"):
        st.markdown("#### 1. Revenue & Affiliate Settings")
        c_gs1, c_gs2 = st.columns(2)
        with c_gs1:
            g_target = st.number_input("Daily Revenue Target (INR)", min_value=100.0, max_value=100000.0, value=float(st.session_state.orchestrator.daily_target_inr), step=100.0)
            g_tag = st.text_input("Global Amazon Associate Tag", value=glob_cfg.get("affiliate", {}).get("amazon_associate_tag", "autoaffil-21"))
        with c_gs2:
            g_earnkaro = st.text_input("EarnKaro API Key / Publisher ID", value=glob_cfg.get("affiliate", {}).get("earnkaro_api_key", ""), placeholder="For Myntra, Nykaa, Ajio 150+ brands")
            g_disc = st.text_input("Default Legal Disclosure (Humanoid, Zero Emojis)", value=glob_cfg.get("affiliate", {}).get("default_disclosure_text", "Disclosure: This post contains affiliate links. As an associate I earn from qualifying purchases."))

        st.markdown("---")
        st.markdown("#### 2. Dynamic Timing & Anti-Bot Protection")
        c_ts1, c_ts2, c_ts3 = st.columns(3)
        with c_ts1:
            s_min = st.number_input("Min Interval (Minutes)", min_value=30, max_value=360, value=int(dyn_cfg.get("min_interval_minutes", 90)), step=15)
        with c_ts2:
            s_max = st.number_input("Max Interval (Minutes)", min_value=60, max_value=720, value=int(dyn_cfg.get("max_interval_minutes", 210)), step=15)
        with c_ts3:
            s_jit = st.number_input("Human Simulation Jitter (Seconds)", min_value=10, max_value=180, value=int(dyn_cfg.get("human_jitter_sec_max", 90)), step=5)

        if st.form_submit_button("Save All Settings"):
            if "affiliate" not in glob_cfg:
                glob_cfg["affiliate"] = {}
            glob_cfg["affiliate"]["amazon_associate_tag"] = g_tag
            glob_cfg["affiliate"]["default_disclosure_text"] = g_disc
            glob_cfg["affiliate"]["earnkaro_api_key"] = g_earnkaro
            if "dynamic_schedule" not in glob_cfg:
                glob_cfg["dynamic_schedule"] = {}
            glob_cfg["dynamic_schedule"]["min_interval_minutes"] = int(s_min)
            glob_cfg["dynamic_schedule"]["max_interval_minutes"] = int(s_max)
            glob_cfg["dynamic_schedule"]["human_jitter_sec_max"] = int(s_jit)
            daemon.min_interval_minutes = int(s_min)
            daemon.max_interval_minutes = int(s_max)

            if "app" not in glob_cfg:
                glob_cfg["app"] = {}
            glob_cfg["app"]["daily_revenue_target_inr"] = float(g_target)
            st.session_state.orchestrator.set_daily_target(float(g_target))

            from core.orchestrator import CONFIG_PATH
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(glob_cfg, f, default_flow_style=False)
            st.success("Global settings saved successfully!")
            st.rerun()


# ==============================================================================
# VIEW 10: PAGE SETUP & LAUNCH GUIDE
# ==============================================================================
elif nav_selection == "🏷️ Page Setup & Launch Guide":
    st.subheader("🏷️ Social Media Setup, Affiliate Approval & High-Profit Playbook")

    sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs([
        "📱 Step-by-Step Meta Setup",
        "🖥️ Portal Setup & Navigation Guide",
        "💳 Amazon & EarnKaro Setup",
        "💰 High-Profit Niches Playbook"
    ])

    with sub_t1:
        st.markdown("""
        ### Step-by-Step Meta (Instagram + Facebook) Page & Token Setup for Elena's World

        Follow these exact steps to connect your pages so AutoAffiliate can post automatically without needing passwords:

        ---

        #### 1. Create Instagram & Facebook Page:
        - **Create Instagram Account**:
          - Open Instagram app → Create account: `@elenasworld.official` (or your chosen brand handle).
          - Switch account type to **Creator** or **Business** in Instagram Settings → **Account Type and Tools** → **Switch to Professional Account**.
        - **Create Facebook Page**:
          - Go to [facebook.com/pages/create](https://www.facebook.com/pages/create) → Name: **Elena's World**.
          - Category: **Women's Clothing Store** or **Fashion Model / Beauty**.
          - Click **Create Page**.

        ---

        #### 2. Link Them in Meta Business Suite:
        - Open [business.facebook.com](https://business.facebook.com/)
        - Go to **Settings** → **Linked Accounts** → **Instagram** → Click **Connect Account**.
        - Log in with `@elenasworld.official` and confirm.
        - *Result:* Now any post published to Facebook automatically cross-posts to Instagram Reels and Feed!

        ---

        #### 3. Get a Page Access Token (Safe, Official & Never Flagged as Bot):
        *(Never give username and password! Meta's security firewalls will block automated password logins. The official API Token is 100% safe, ban-proof, and official).*

        - Go to [developers.facebook.com](https://developers.facebook.com/) and log in with your Facebook account.
        - Click **My Apps** (top right) → **Create App** → Select **"Business"** (or Other → Business) → App Name: `AutoAffiliate App`.
        - In the top navigation menu, go to **Tools** → **Graph API Explorer**:
          1. Under **User or Page**, click the dropdown and select your Page: **Elena's World** *(Do NOT leave it on User Token)*.
          2. Under **Permissions**, add these 4 required permissions:
             - `pages_manage_posts` (allows publishing photos/posts to your page)
             - `pages_read_engagement` (allows reading engagement & comments)
             - `instagram_basic` (allows accessing connected Instagram account)
             - `instagram_content_publish` (allows publishing reels & carousels to Instagram)
          3. Click **Generate Access Token** and approve the Facebook confirmation pop-up.
          4. Copy the Token string (starts with `EAAG...`) and copy your **Facebook Page ID**.

        ---

        #### 4. Paste Token into AutoAffiliate:
        - Open **🏢 Channel Accounts Manager** in the left menu.
        - Under **Elena's World**, paste your **Facebook Page ID** and **Meta Graph API Access Token**.
        - (Or paste directly into `config/settings.yaml` under `channel_profiles.elenas_world`).
        - Click **Save**. Done! The bot will now publish live posts and vertical reels directly to your page!
        """)

    with sub_t2:
        st.markdown("""
        ### 🖥️ Portal Quick-Start & Navigation Guide (De-Mystifying the Left Menu)

        Are you feeling confused by all the options in the left menu? Here is the simple breakdown.

        ---

        #### ⚡ The 3-Step Setup (Do This Once and You Are Done!)
        1. **Step 1: Verify EarnKaro ID**: Your EarnKaro ID **`5736594`** is already configured! All Flipkart, Myntra, Nykaa links automatically earn you money.
        2. **Step 2: Plug in your Page ID & Token**: Go to **🏢 Channel Accounts Manager** → paste your Page ID and Access Token for Elena's World.
        3. **Step 3: Start Autopilot**: Go to **🤖 Autonomous Autopilot** → make sure Elena's World is checked → click **🚀 START 24/7 AUTOPILOT**.

        That is literally all! The bot will now run in the background 24/7 finding sarees, watches, and beauty items, generating Elena's branded photos and videos, and posting them with your EarnKaro link!

        ---

        #### 🧭 What Each Left Menu Option Actually Does (Plain English Map)

        | Left Menu Section | What It Is For | How Often You Use It |
        | :--- | :--- | :--- |
        | **📊 Executive Dashboard** | **Your Scorecard**: View daily profit pacing vs target (₹5,000), total clicks, orders, and real-time bot audit logs. | **Daily** (Takes 10 seconds to check) |
        | **🤖 Autonomous Autopilot** | **The Engine Switch**: Turn on/off 24/7 hands-free posting. Toggle which accounts run independently. | **Daily** (Start or Pause anytime) |
        | **⚡ Live Product Sandbox** | **Instant Test-Drive**: Want to test a specific saree, kurta, watch, or beauty cream right now? Pick a category or type "silk saree" and click Test Now to see the photos, video, and copy in 15 seconds! | **Whenever you want to test on demand** |
        | **📱 Content & Media Library** | **Your Post Deck**: View all drafts and published posts. Watch generated AI reels and view 4-slide carousels. | **Weekly or when reviewing posts** |
        | **💬 Grok Command Console** | **Chat With Your Bots**: Talk to your digital employees in natural English (*"Test next saree"*, *"Set daily target to 2000"*). | **Optional** |
        | **🏢 Channel Accounts Manager** | **Your Social Accounts List**: Where `Elena's World`, `StyleDrop`, and `UrbanGent` accounts are configured. | **One-Time Setup** (When adding or editing accounts) |
        | **🎯 Niche & Account Mapping** | **Traffic Routing**: Connects product categories (Sarees/Kurtas/Watches) to specific accounts (`Elena's World`). | **One-Time Setup** |
        | **🌐 E-Commerce Platforms** | **Your Partner Stores**: Amazon, Flipkart, Myntra, Nykaa registry with your affiliate tags. | **One-Time Setup** |
        | **⚙️ Global Settings & Compliance** | **Rules & Safety**: Set daily profit target ₹X, anti-bot delays (90 to 210 mins), and your EarnKaro ID. | **One-Time Setup** |
        | **🏷️ Page Setup & Launch Guide** | **Help & Tutorials**: This exact guide with step-by-step instructions! | **Whenever you need help** |

        ---

        #### 🔄 Your Simple 10-Second Daily Routine
        ```mermaid
        graph LR
            A[1. Open Dashboard] --> B[2. Check Today's Earnings]
            B --> C[3. Ensure Autopilot is Green 🟢]
            C --> D[4. Close tab & let bot make money!]
        ```
        """)

    with sub_t3:
        st.markdown("""
        ### 💳 Affiliate Setup & Approval Guide (India)

        #### 1. EarnKaro (Your Active ID: `5736594`)
        - **Status:** **Active & Verified in AutoAffiliate AI**
        - **Stores Covered:** Flipkart, Myntra, Ajio, Nykaa, Mamaearth, Croma, Samsung, Tata 1mg, and 150+ brands.
        - **Approval:** Instant with mobile OTP (zero waiting period and zero minimum follower requirement).
        - **Payout Threshold:** Minimum **₹10** directly transferred to your Indian bank account via NEFT.
        - **🛡️ Automatic Cloaking:** **Followers NEVER see `earnkaro.com` directly.** AutoAffiliate automatically cloaks and shortens all EarnKaro links into clean, high-converting deal links so your posts and DMs look 100% professional and authentic.

        #### 2. Amazon Associates India
        - **Website:** [affiliate-program.amazon.in](https://affiliate-program.amazon.in)
        - **Sign Up:** Use your regular Amazon.in shopping account. When asked for your website, paste your Facebook Page (`facebook.com/ElenasWorld`) or Instagram profile (`instagram.com/elenasworld.official`).
        - **Tag:** Paste your Amazon Associate tag in **⚙️ Global Settings**.
        - **180-Day Rule:** You need 3 qualifying orders within 180 days for permanent approval. The bot's automated reels easily achieve this within the first 2 weeks.
        """)

    with sub_t4:
        st.markdown("""
        ### 💰 Most Profitable Categories for Elena's World

        | Category | Typical Commission | Average Price | Your Profit per Sale | Conversion Rate |
        | :--- | :--- | :--- | :--- | :--- |
        | **👗 Sarees & Ethnic Kurtas** | 7.0% - 10.0% | ₹899 - ₹2,499 | **₹70 - ₹250** | **Extreme (High virality reels)** |
        | **💄 Skincare & Beauty Serums** | 8.0% - 12.0% | ₹499 - ₹1,299 | **₹45 - ₹150** | **Very High (Daily repeat buyers)** |
        | **⌚ Ladies Analog & Smart Watches** | 8.0% - 11.0% | ₹1,299 - ₹3,499 | **₹110 - ₹380** | **High (Gifting & self-purchase)** |
        | **💎 Ethnic Jewellery & Jhumkas** | 9.0% - 14.0% | ₹399 - ₹999 | **₹40 - ₹140** | **Extreme (Impulse purchases)** |
        """)
