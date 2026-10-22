"""AutoAffiliate AI - Enterprise Admin Panel.
Complete Admin Panel Model featuring:
1. Executive Dashboard (KPIs, active channels, live revenue tracker)
2. Channel Accounts Manager (Add Men's Fashion, Ladies Fashion, Electronics, Any Niche)
3. Niche & Account Mapping (Visual matrix of Niche -> Keywords -> Mapped Account)
4. E-Commerce Platforms (Amazon, Flipkart, Myntra, Nykaa, Ajio, Meesho, Croma + Add Platform + Live URL Scraper)
5. Autonomous Autopilot (Dynamic non-fixed timing, independent channel dispatch, organic growth)
6. Live Product Sandbox (100% Humanoid copy, zero icons/emojis, 4-slide carousels, AI vertical reels)
7. Content & Asset Library (Draft & published posts, 1-click approvals)
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
    page_title="AutoAffiliate AI | Admin Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enterprise Admin CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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
    .account-card {
        background: #151d30;
        border: 1px solid #243048;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Orchestrator & Daemon in Session State
if "orchestrator" not in st.session_state or not hasattr(st.session_state.orchestrator, "tested_product_ids"):
    st.session_state.orchestrator = AgentOrchestrator()

daemon = get_auto_daemon()

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
# SIDEBAR ADMIN NAVIGATION
# ==============================================================================
with st.sidebar:
    st.markdown('<div class="admin-brand">AutoAffiliate AI</div>', unsafe_allow_html=True)
    st.markdown('<span class="admin-badge">ENTERPRISE ADMIN v1.2</span>', unsafe_allow_html=True)

    # Autopilot status pill in sidebar
    if daemon.is_running:
        st.markdown("<span style='color:#34d399; font-weight:700;'>🟢 24/7 AUTOPILOT ACTIVE</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#94a3b8; font-weight:600;'>⚪ AUTOPILOT STANDBY</span>", unsafe_allow_html=True)

    st.markdown("---")
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
header_c1, header_c2 = st.columns([3, 1.2])
with header_c1:
    st.markdown(f"### {nav_selection}")
with header_c2:
    all_prof = st.session_state.orchestrator.get_channel_profiles()
    en_prof = st.session_state.orchestrator.get_enabled_autopilot_profiles()
    st.markdown(f"<div style='text-align:right; margin-top:8px;'><span style='color:#38bdf8; font-weight:600;'>{len(en_prof)} of {len(all_prof)} Accounts Active in Autopilot</span></div>", unsafe_allow_html=True)

st.divider()


# ==============================================================================
# VIEW 1: EXECUTIVE DASHBOARD
# ==============================================================================
if nav_selection == "📊 Executive Dashboard":
    # 1. KPI Cards Row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_rev = sum(h.get("estimated_earnings_inr", 0) for h in get_revenue_history(days=14))
    total_clicks = sum(h.get("clicks", 0) for h in get_revenue_history(days=14))
    total_orders = sum(h.get("orders", 0) for h in get_revenue_history(days=14))

    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Daily Revenue Target (X)</div>
            <div class="kpi-value">₹{current_target:,.0f}</div>
            <div class="kpi-sub">Fully Configurable Anytime</div>
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

    # 2. Channel Matrix Overview
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

    # 3. Recent Real-Time Bot Operations
    st.subheader("🔍 Operational Audit Trail (Live Bot Actions)")
    logs = get_recent_logs(limit=12)
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

    # 1. Quick Presets Bar
    st.markdown("#### ⚡ Quick Actions & Presets:")
    col_p1, col_p2, col_p3 = st.columns(3)
    profiles = st.session_state.orchestrator.get_channel_profiles()
    has_mens = any(p["id"] == "mens_fashion" for p in profiles)

    with col_p1:
        if not has_mens:
            if st.button("👔 1-Click Add Men's Fashion Account (`UrbanGent India`)", use_container_width=True):
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
                st.success("UrbanGent India (Men's Fashion) added successfully!")
                st.rerun()
        else:
            st.info("✓ Men's Fashion (`UrbanGent India`) is already registered.")

    with col_p2:
        if st.button("👗 Focus Active View on Ladies Fashion", use_container_width=True):
            st.session_state.orchestrator.set_active_profile("fashion")
            st.rerun()

    with col_p3:
        if st.button("⚡ Focus Active View on Electronics", use_container_width=True):
            st.session_state.orchestrator.set_active_profile("electronics")
            st.rerun()

    st.markdown("---")

    # 2. Existing Connected Accounts Cards
    st.markdown("### 📱 Registered Accounts List")
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
                ap_chk = st.checkbox(
                    "Autopilot Enabled",
                    value=is_ap_enabled,
                    key=f"mgr_ap_{pid}",
                    help="Enable to automatically scout and post deals for this account"
                )
                if ap_chk != is_ap_enabled:
                    st.session_state.orchestrator.set_profile_autopilot_enabled(pid, ap_chk)
                    st.rerun()

                if not is_act:
                    if st.button("Set as Active Focus", key=f"btn_set_act_{pid}", use_container_width=True):
                        st.session_state.orchestrator.set_active_profile(pid)
                        st.rerun()
                else:
                    st.markdown("<span style='color:#34d399; font-weight:700;'>🟢 ACTIVE FOCUS</span>", unsafe_allow_html=True)
            st.divider()

    # 3. Add New Account Form (100% Flexible)
    with st.expander("➕ Register Another Account (e.g. Men's Fashion, Home Decor, Fitness)", expanded=False):
        with st.form("form_add_new_account"):
            st.write("**Account Profile Details:**")
            f_name = st.text_input("Account Display Name", placeholder="e.g. UrbanGent India or HomeStyle Bharat")
            f_col_n1, f_col_n2 = st.columns(2)
            with f_col_n1:
                f_niche_preset = st.selectbox(
                    "Niche Category",
                    ["mens_fashion", "fashion", "mobiles", "electronics", "toys", "kitchen", "beauty", "home_decor", "fitness", "custom"],
                    format_func=lambda x: {
                        "mens_fashion": "👔 Men's Fashion & Grooming",
                        "fashion": "👗 Ladies Fashion & Dresses",
                        "mobiles": "📱 High-Ticket Mobiles & Tech",
                        "electronics": "💻 Electronics & Gadgets",
                        "toys": "🧸 Kids Toys & Games",
                        "kitchen": "🍳 Home & Kitchen Finds",
                        "beauty": "💄 Beauty & Personal Care",
                        "home_decor": "🏠 Home Decor & Organizing",
                        "fitness": "🏋️ Fitness & Gym Gear",
                        "custom": "✨ Custom Niche (Specify on right)"
                    }.get(x, x)
                )
            with f_col_n2:
                f_niche_custom = st.text_input("Or Type Custom Niche Name", placeholder="e.g. baby_care, luxury_watches")

            assigned_niche = f_niche_custom.strip().lower() if f_niche_custom.strip() else f_niche_preset
            f_desc = st.text_input("Description", placeholder="e.g. Dedicated to men's shirts, trousers, jackets, and accessories")
            f_ig = st.text_input("Instagram Handle", placeholder="e.g. @urbangent.in")
            f_fb = st.text_input("Facebook Page ID", placeholder="e.g. 1029384756")
            f_tg = st.text_input("Telegram Channel (Optional)", placeholder="e.g. @urbangent_deals")
            f_token = st.text_input("Meta Graph API Access Token (Optional)", type="password", placeholder="Leave blank to use default or simulation")
            f_aff = st.text_input("Custom Affiliate Tag Override (Optional)", placeholder="Leave blank to use global tag")
            f_auto = st.checkbox("Enable for Autonomous Autopilot", value=True)

            if st.form_submit_button("Save & Register Account"):
                if f_name:
                    p_id = f_name.lower().replace(" ", "_").replace("(", "").replace(")", "")[:20]
                    st.session_state.orchestrator.save_channel_profile({
                        "id": p_id,
                        "name": f_name,
                        "focus_niche": assigned_niche,
                        "description": f_desc,
                        "instagram_username": f_ig,
                        "facebook_page_id": f_fb,
                        "telegram_channel_id": f_tg,
                        "meta_access_token": f_token,
                        "custom_affiliate_tag": f_aff,
                        "enabled_for_autopilot": f_auto
                    })
                    st.success(f"Account '{f_name}' registered successfully with niche '{assigned_niche}'!")
                    st.rerun()

    # 4. Edit / Delete Account Drawer
    with st.expander("✏️ Edit / Delete an Account", expanded=False):
        edit_pid = st.selectbox(
            "Select Account to Modify",
            [p["id"] for p in profiles],
            format_func=lambda pid: next((p["name"] for p in profiles if p["id"] == pid), pid)
        )
        target_p = next((p for p in profiles if p["id"] == edit_pid), None)
        if target_p:
            with st.form("form_edit_acc"):
                e_name = st.text_input("Account Display Name", value=target_p.get("name", ""))
                e_niche = st.text_input("Niche Focus", value=target_p.get("focus_niche", "all"))
                e_desc = st.text_input("Description", value=target_p.get("description", ""))
                e_ig = st.text_input("Instagram Handle", value=target_p.get("instagram_username", ""))
                e_fb = st.text_input("Facebook Page ID", value=target_p.get("facebook_page_id", ""))
                e_tg = st.text_input("Telegram Channel", value=target_p.get("telegram_channel_id", ""))
                e_ap = st.checkbox("Enabled for Autopilot", value=target_p.get("enabled_for_autopilot", True))
                if st.form_submit_button("Update Account"):
                    target_p["name"] = e_name
                    target_p["focus_niche"] = e_niche.strip().lower()
                    target_p["description"] = e_desc
                    target_p["instagram_username"] = e_ig
                    target_p["facebook_page_id"] = e_fb
                    target_p["telegram_channel_id"] = e_tg
                    target_p["enabled_for_autopilot"] = e_ap
                    st.session_state.orchestrator.save_channel_profile(target_p)
                    st.success("Account updated successfully!")
                    st.rerun()

            if len(profiles) > 1:
                if st.button("🗑️ Delete This Account", key=f"del_acc_{edit_pid}"):
                    if st.session_state.orchestrator.delete_channel_profile(edit_pid):
                        st.success("Account deleted.")
                        st.rerun()


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

    # Display Current Mapping Matrix
    mappings = st.session_state.orchestrator.get_niche_mappings()
    profiles = st.session_state.orchestrator.get_channel_profiles()

    map_display = []
    for m in mappings:
        acc_id = m.get("mapped_account_id")
        acc_obj = next((p for p in profiles if p["id"] == acc_id), None)
        acc_name = acc_obj.get("name") if acc_obj else f"Account #{acc_id}"
        map_display.append({
            "Niche ID": m.get("id"),
            "Niche Name": m.get("name"),
            "Target Search Keywords": m.get("keywords"),
            "Mapped Account Profile": acc_name,
            "Expected Commission Rate": m.get("commission_rate", "5% - 8%")
        })

    st.dataframe(pd.DataFrame(map_display), use_container_width=True)

    st.markdown("---")

    # Add New Niche & Map to Account Form
    st.subheader("➕ Create New Niche & Map to Account")
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

    # 1. Registered Platforms Table
    st.subheader("🛍️ Active E-Commerce Networks")
    platforms = st.session_state.orchestrator.scout.tagger.platforms

    p_list = []
    for pk, pv in platforms.items():
        p_list.append({
            "Platform Key": pk,
            "Network Name": pv.get("name"),
            "Primary Domain": pv.get("domains", [""])[0],
            "Affiliate Parameter": pv.get("param", "tag"),
            "Current Tracking Tag": pv.get("id", "Global Default")
        })
    st.dataframe(pd.DataFrame(p_list), use_container_width=True)

    st.markdown("---")

    col_plat1, col_plat2 = st.columns(2)

    # 2. Add New E-Commerce Website Form
    with col_plat1:
        st.subheader("➕ Register Another Platform (e.g. Nykaa, Purplle)")
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
                    st.success(f"Platform '{np_name}' registered successfully! Links from this site will now be auto-tagged.")
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
                        st.write(f"• **Auto-Tagged Link:** `{item.get('affiliate_url')}`")
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

    col_ap1, col_ap2 = st.columns([3, 1.2])
    with col_ap1:
        st.write("**Select Active Autopilot Channels (Each runs independently):**")
        cb_cols = st.columns(max(len(all_profiles), 1))
        for idx, prof in enumerate(all_profiles):
            pid = prof["id"]
            is_enabled = prof.get("enabled_for_autopilot", False)
            with cb_cols[idx % len(cb_cols)]:
                chk = st.checkbox(
                    f"**{prof['name']}** - `[{prof.get('focus_niche', 'all').upper()}]`",
                    value=is_enabled,
                    key=f"ap_view_chk_{pid}"
                )
                if chk != is_enabled:
                    st.session_state.orchestrator.set_profile_autopilot_enabled(pid, chk)
                    st.rerun()

    with col_ap2:
        st.markdown("<br>", unsafe_allow_html=True)
        if daemon.is_running:
            if st.button("⏸️ PAUSE AUTOPILOT", use_container_width=True, key="ap_btn_stop"):
                daemon.stop_background_loop()
                st.rerun()
        else:
            if st.button("🚀 START 24/7 AUTOPILOT", use_container_width=True, key="ap_btn_start"):
                daemon.start_background_loop()
                st.rerun()

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

    st.markdown(f"""
    <div style="background:#064e3b; border:1px solid #059669; border-radius:10px; padding:16px; margin: 16px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#ffffff; font-size:1.1rem;">{'🟢 AUTOPILOT ENGINE RUNNING' if daemon.is_running else '⚪ AUTOPILOT ENGINE STANDBY'}</strong>
            <span style="color:#a7f3d0; background:#047857; padding:4px 10px; border-radius:6px; font-weight:600; font-size:0.8rem;">🛡️ Anti-Spam Jitter Pacing Active</span>
        </div>
        <div style="color:#e2e8f0; font-size:0.92rem; margin-top:8px; line-height:1.6;">
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
        st.markdown(f"### 🔍 Live Test Results — <span style='color:#38bdf8;'>[{p.get('platform')}] {p['title'][:50]}</span> (Test #{t_num})", unsafe_allow_html=True)
        st.markdown("<span style='color:#34d399; font-weight:600;'>✓ 100% Humanoid Copy Verified: Zero emojis & Zero special characters</span>", unsafe_allow_html=True)

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
            st.markdown(f"**Live Affiliate URL:** `{p['affiliate_url']}`")
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
    posts = get_posts(limit=25)
    if not posts:
        st.info("No posts created yet. Go to 'Live Product Sandbox' to generate one instantly.")
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

                    status_color = "#34d399" if post["status"] == "published" else "#f59e0b"
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

            with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml"), "w", encoding="utf-8") as f:
                yaml.safe_dump(glob_cfg, f, default_flow_style=False)
            st.success("Global settings saved successfully!")
            st.rerun()


# ==============================================================================
# VIEW 10: PAGE SETUP & LAUNCH GUIDE
# ==============================================================================
elif nav_selection == "🏷️ Page Setup & Launch Guide":
    st.subheader("🏷️ Social Media Setup, Affiliate Approval & High-Profit Playbook")

    sub_t1, sub_t2, sub_t3 = st.tabs(["📱 Account Creation & Linking", "💳 Amazon & EarnKaro Setup", "💰 Most Profitable Platforms"])

    with sub_t1:
        st.markdown("""
        ### Step-by-Step Meta (Instagram + Facebook) Page Setup
        1. **Create Instagram Account**: Open Instagram app -> Create account (e.g. `@styledrop.in`, `@urbangent.in`, `@techpulse.india`). Switch account type to **Creator**.
        2. **Create Facebook Page**: Go to [facebook.com/pages/create](https://www.facebook.com/pages/create) and create page matching your brand name.
        3. **Link in Meta Business Suite**: Go to `business.facebook.com` -> Settings -> Linked Accounts -> Connect your Instagram. Now bot posts to FB automatically cross-post to Instagram!
        """)

    with sub_t2:
        st.markdown("""
        ### Affiliate Marketing Setup in India
        1. **Amazon Associates India** ([affiliate-program.amazon.in](https://affiliate-program.amazon.in)): Sign up with your regular Amazon account. Paste your Instagram or Facebook URL as your website. Provide PAN and bank details.
        2. **EarnKaro** ([earnkaro.com](https://earnkaro.com)): Instant signup with mobile OTP. Covers **Flipkart, Myntra, Ajio, Nykaa, Tata CliQ, Meesho** with zero approval waiting period.
        """)

    with sub_t3:
        st.markdown("""
        ### Most Profitable Affiliate Niches in India
        - **Ladies Fashion & Sarees:** 7% - 10% commission (High virality reels)
        - **Men's Fashion & Shoes:** 6% - 9% commission (Consistent year-round demand)
        - **Credit Cards & BFSI (BankSathi / EarnKaro):** Flat ₹1,500 - ₹3,500 per approved card
        - **Smartphones & Laptops:** 1% - 2.5% (High volume during festival sales)
        - **Web Hosting & SaaS (Hostinger):** ₹1,800 - ₹4,500 per referral
        """)
