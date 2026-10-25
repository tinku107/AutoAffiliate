"""Central Multi-Agent Business Orchestrator.
Manages the digital employee bots (Scout, Creative, Marketer),
handles dynamic profit target X, multi-platform affiliate routing,
and live product test generation.
"""

import re
import yaml
import os
from typing import Dict, Any, List, Optional
from agents.scout_agent import ScoutAgent
from agents.creative_agent import CreativeAgent
from agents.marketer_agent import MarketerAgent
from core.db import (
    get_products,
    get_posts,
    get_revenue_history,
    get_recent_logs,
    log_agent_action,
    log_daily_revenue
)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml")


class AgentOrchestrator:
    def __init__(self):
        self.config = self._load_config()
        self.daily_target_inr = float(self.config.get("app", {}).get("daily_revenue_target_inr", 500.0))

        aff_tag = self.config.get("affiliate", {}).get("amazon_associate_tag", "autoaffil-21")
        earnkaro_id = self.config.get("affiliate", {}).get("earnkaro_api_key", "")
        gemini_key = self.config.get("ai", {}).get("gemini_api_key", "")

        self.scout = ScoutAgent(amazon_tag=aff_tag, earnkaro_id=earnkaro_id)
        self.creative = CreativeAgent(gemini_api_key=gemini_key)
        self.marketer = MarketerAgent()
        self.tested_product_ids = set()
        self.test_counter = 0

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {}

    def set_daily_target(self, new_target: float):
        """Allows user to dynamically change daily profit target X anytime."""
        self.daily_target_inr = float(new_target)
        try:
            cfg = self._load_config()
            if "app" not in cfg:
                cfg["app"] = {}
            cfg["app"]["daily_revenue_target_inr"] = self.daily_target_inr
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            log_agent_action("Orchestrator", f"Updated daily profit target to INR {self.daily_target_inr}", "completed")
        except Exception as e:
            print(f"Could not update target in config: {e}")

    def get_channel_profiles(self) -> List[Dict[str, Any]]:
        """Returns the list of configured channel profiles."""
        cfg = self._load_config()
        return cfg.get("channel_profiles", [
            {
                "id": "general",
                "name": "🌟 Mega Loot Deals (General)",
                "focus_niche": "all",
                "description": "Common focus: Scrapes top deals across all categories",
                "instagram_username": "",
                "facebook_page_id": ""
            }
        ])

    def get_channel_mode(self) -> str:
        """Returns 'single' (focus on active profile) or 'multi_channel' (cycle through all profiles)."""
        cfg = self._load_config()
        return cfg.get("channel_mode", "single")

    def set_channel_mode(self, mode: str):
        cfg = self._load_config()
        cfg["channel_mode"] = mode
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            log_agent_action("Orchestrator", f"Channel mode switched to: {mode}", "completed")
        except Exception as e:
            print(f"Error saving channel mode: {e}")

    def get_active_profile(self) -> Dict[str, Any]:
        """Returns the currently active channel profile."""
        cfg = self._load_config()
        active_id = cfg.get("active_profile_id", "general")
        profiles = self.get_channel_profiles()
        for p in profiles:
            if p.get("id") == active_id:
                return p
        return profiles[0] if profiles else {"id": "general", "name": "General Deals", "focus_niche": "all"}

    def set_active_profile(self, profile_id: str):
        """Switches the active channel profile."""
        cfg = self._load_config()
        cfg["active_profile_id"] = profile_id
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            p = self.get_active_profile()
            log_agent_action("Orchestrator", f"Active channel profile changed to: {p.get('name')}", "completed")
        except Exception as e:
            print(f"Error saving active profile: {e}")

    def get_enabled_autopilot_profiles(self) -> List[Dict[str, Any]]:
        """Returns the list of profiles that the user has enabled for autonomous posting."""
        profiles = self.get_channel_profiles()
        enabled = [p for p in profiles if p.get("enabled_for_autopilot", False)]
        if not enabled and profiles:
            # Fallback to first profile if none explicitly enabled
            return [profiles[0]]
        return enabled

    def set_profile_autopilot_enabled(self, profile_id: str, enabled: bool):
        """Enables or disables an individual channel profile for autopilot."""
        cfg = self._load_config()
        profiles = cfg.get("channel_profiles", [])
        for p in profiles:
            if p.get("id") == profile_id:
                p["enabled_for_autopilot"] = bool(enabled)
                break
        cfg["channel_profiles"] = profiles
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            status_str = "ENABLED" if enabled else "DISABLED"
            log_agent_action("Orchestrator", f"Channel profile #{profile_id} autopilot {status_str}", "completed")
        except Exception as e:
            print(f"Error updating profile autopilot status: {e}")

    def save_channel_profile(self, profile_data: Dict[str, Any]):
        """Adds or updates a channel profile."""
        cfg = self._load_config()
        profiles = cfg.get("channel_profiles", [])
        pid = profile_data.get("id") or profile_data.get("name", "channel").lower().replace(" ", "_")
        profile_data["id"] = pid
        if "enabled_for_autopilot" not in profile_data:
            profile_data["enabled_for_autopilot"] = True

        found = False
        for idx, p in enumerate(profiles):
            if p.get("id") == pid:
                profiles[idx] = profile_data
                found = True
                break
        if not found:
            profiles.append(profile_data)

        cfg["channel_profiles"] = profiles
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            log_agent_action("Orchestrator", f"Saved channel profile: {profile_data.get('name')}", "completed")
        except Exception as e:
            print(f"Error saving profile: {e}")

    def delete_channel_profile(self, profile_id: str) -> bool:
        """Deletes a channel profile."""
        cfg = self._load_config()
        profiles = cfg.get("channel_profiles", [])
        if len(profiles) <= 1:
            return False
        new_profiles = [p for p in profiles if p.get("id") != profile_id]
        cfg["channel_profiles"] = new_profiles
        if cfg.get("active_profile_id") == profile_id:
            cfg["active_profile_id"] = new_profiles[0]["id"]
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            log_agent_action("Orchestrator", f"Deleted channel profile #{profile_id}", "completed")
            return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False

    def get_niche_mappings(self) -> List[Dict[str, Any]]:

        """Returns the list of configured niches and their mapped channel accounts."""
        cfg = self._load_config()
        default_niches = [
            {
                "id": "fashion",
                "name": "Ladies Fashion & Ethnic",
                "keywords": "women dress, anarkali kurti, saree, lehenga, ethnic wear",
                "mapped_account_id": "fashion",
                "commission_rate": "7% - 10%"
            },
            {
                "id": "mobiles",
                "name": "High-Ticket Mobiles & Tech",
                "keywords": "smartphones, iphone 16, samsung galaxy, flagship phones",
                "mapped_account_id": "electronics",
                "commission_rate": "1% - 2.5%"
            },
            {
                "id": "mens_fashion",
                "name": "Men's Fashion & Grooming",
                "keywords": "men shirts, men jeans, formal suits, sneakers, grooming",
                "mapped_account_id": "mens_fashion",
                "commission_rate": "6% - 9%"
            },
            {
                "id": "electronics",
                "name": "Smart Gadgets & Electronics",
                "keywords": "earbuds, smartwatches, power banks, desk gadgets",
                "mapped_account_id": "electronics",
                "commission_rate": "4% - 6%"
            },
            {
                "id": "kitchen",
                "name": "Home & Kitchen Hacks",
                "keywords": "kitchen tools, cookware, food organizers, storage hacks",
                "mapped_account_id": "general",
                "commission_rate": "6% - 9%"
            }
        ]
        return cfg.get("niche_mappings", default_niches)

    def save_niche_mapping(self, mapping_data: Dict[str, Any]):
        """Adds or updates a niche mapping."""
        cfg = self._load_config()
        mappings = self.get_niche_mappings()
        nid = mapping_data.get("id") or mapping_data.get("name", "niche").lower().replace(" ", "_")
        mapping_data["id"] = nid
        found = False
        for idx, m in enumerate(mappings):
            if m.get("id") == nid:
                mappings[idx] = mapping_data
                found = True
                break
        if not found:
            mappings.append(mapping_data)
        cfg["niche_mappings"] = mappings
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            log_agent_action("Orchestrator", f"Saved niche mapping: {mapping_data.get('name')} -> {mapping_data.get('mapped_account_id')}", "completed")
        except Exception as e:
            print(f"Error saving niche mapping: {e}")

    def delete_niche_mapping(self, niche_id: str) -> bool:
        """Deletes a niche mapping."""
        cfg = self._load_config()
        mappings = self.get_niche_mappings()
        new_mappings = [m for m in mappings if m.get("id") != niche_id]
        cfg["niche_mappings"] = new_mappings
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
            self.config = cfg
            log_agent_action("Orchestrator", f"Deleted niche mapping #{niche_id}", "completed")
            return True
        except Exception as e:
            print(f"Error deleting niche mapping: {e}")
            return False

    def bulk_save_channel_profiles(self, profiles_list: List[Dict[str, Any]]) -> bool:
        """Saves a full list of channel profiles edited in the table editor."""
        cfg = self._load_config()
        clean_profiles = []
        for p in profiles_list:
            if not p.get("name"):
                continue
            pid = str(p.get("id") or p.get("name", "channel").lower().replace(" ", "_"))
            p_data = {
                "id": pid,
                "name": str(p.get("name")),
                "focus_niche": str(p.get("focus_niche", "all")).strip().lower(),
                "description": str(p.get("description", "")),
                "instagram_username": str(p.get("instagram_username", "")),
                "facebook_page_id": str(p.get("facebook_page_id", "")),
                "telegram_channel_id": str(p.get("telegram_channel_id", "")),
                "enabled_for_autopilot": bool(p.get("enabled_for_autopilot", True))
            }
            clean_profiles.append(p_data)
        if clean_profiles:
            cfg["channel_profiles"] = clean_profiles
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False)
                self.config = cfg
                log_agent_action("Orchestrator", f"Bulk updated {len(clean_profiles)} channel profiles from table editor", "completed")
                return True
            except Exception as e:
                print(f"Error bulk saving profiles: {e}")
                return False
        return False

    def bulk_save_niche_mappings(self, mappings_list: List[Dict[str, Any]]) -> bool:
        """Saves a full list of niche mappings edited in the table editor."""
        cfg = self._load_config()
        clean_mappings = []
        for m in mappings_list:
            if not m.get("name") or not m.get("keywords"):
                continue
            nid = str(m.get("id") or m.get("name", "niche").lower().replace(" ", "_"))
            m_data = {
                "id": nid,
                "name": str(m.get("name")),
                "keywords": str(m.get("keywords")),
                "mapped_account_id": str(m.get("mapped_account_id", "fashion")),
                "commission_rate": str(m.get("commission_rate", "5% - 8%"))
            }
            clean_mappings.append(m_data)
        if clean_mappings:
            cfg["niche_mappings"] = clean_mappings
            try:
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False)
                self.config = cfg
                log_agent_action("Orchestrator", f"Bulk updated {len(clean_mappings)} niche mappings from table editor", "completed")
                return True
            except Exception as e:
                print(f"Error bulk saving niche mappings: {e}")
                return False
        return False

    def bulk_save_platforms(self, platforms_list: List[Dict[str, Any]]) -> bool:
        """Saves a full list of platforms edited in the platforms table editor."""
        for p in platforms_list:
            key = str(p.get("key") or p.get("name", "platform").lower().replace(" ", "_")).strip()
            name = str(p.get("name", key.capitalize())).strip()
            domain = str(p.get("domain", f"{key}.com")).strip()
            param = str(p.get("param", "tag")).strip()
            aff_id = str(p.get("id", "affiliate")).strip()
            if key and domain:
                self.scout.tagger.add_platform(
                    key=key,
                    name=name,
                    domain=domain,
                    param=param,
                    affiliate_id=aff_id
                )
        log_agent_action("Orchestrator", "Bulk updated platforms from table editor", "completed")
        return True


    def test_next_product(
        self,
        category: str = "all",
        query: Optional[str] = None,
        platform: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes an instant end-to-end test with guaranteed fresh product rotation:
        1. Dynamically finds live selling products from Amazon India & Flipkart.
        2. Filters out previously tested items so EVERY press shows the NEXT real product!
        3. Generates complete copy, reel script, hashtags, and visual carousel / video.
        4. Returns the full asset package for immediate user inspection.
        """
        log_agent_action("Orchestrator", f"Testing next product [{platform.upper()}] in: {query or category}", "started")

        # Fetch a pool of live products so we can select the NEXT fresh product
        pool_size = 15
        products = self.scout.scout_trending_products(
            category=category,
            query=query,
            platform=platform,
            count=pool_size,
            target_profit=self.daily_target_inr
        )
        if not products:
            return {"success": False, "error": f"No live products retrieved from {platform.upper()} for '{query or category}'"}

        # Find the next product that has not been tested in this session
        target_prod = None
        for p in products:
            pid = p.get("product_id")
            if pid and pid not in self.tested_product_ids:
                target_prod = p
                self.tested_product_ids.add(pid)
                break

        # If all products in the pool have been tested, clear history and cycle
        if not target_prod:
            self.tested_product_ids.clear()
            idx = self.test_counter % len(products)
            target_prod = products[idx]
            self.tested_product_ids.add(target_prod.get("product_id"))

        self.test_counter += 1

        post = self.creative.generate_content_for_product(target_prod, channel_niche=category, channel_profile=self.get_active_profile())

        log_agent_action("Orchestrator", f"Test product #{self.test_counter} ready: [{target_prod['platform']}] {target_prod['title'][:35]}", "completed")
        return {
            "success": True,
            "test_number": self.test_counter,
            "platform": target_prod.get("platform", "Amazon"),
            "product": target_prod,
            "post": post
        }

    def run_profile_autonomous_cycle(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an independent autonomous cycle for a single channel profile:
        1. Scouts a live product matching the profile's dedicated focus_niche
        2. Generates humanoid copy (zero icons/special characters) tailored to that niche
        3. Publishes to that profile's specific Instagram & Facebook accounts
        4. Runs organic audience growth (likes, comments, follower invites) in that niche
        """
        prof_name = profile.get("name", "Channel")
        target_niche = profile.get("focus_niche", "all")
        log_agent_action("Orchestrator", f"Starting independent cycle for [{prof_name}] in niche '{target_niche}'", "started")

        products = self.scout.scout_trending_products(category=target_niche, count=1, target_profit=self.daily_target_inr)
        if not products:
            products = self.scout.scout_trending_products(category="all", count=1, target_profit=self.daily_target_inr)

        if not products:
            return {"success": False, "channel": prof_name, "error": "No products discovered"}

        prod = products[0]
        post = self.creative.generate_content_for_product(prod, channel_niche=target_niche, channel_profile=profile)
        post["target_channel"] = profile.get("id")

        publish_res = self.marketer.publish_approved_post(post, channel_profile=profile)
        growth_res = self.marketer.grow_audience_and_engage(niche=target_niche, channel_profile=profile, count=2)

        summary = f"Completed independent cycle for [{prof_name}]: Posted {prod['title'][:35]} and ran {len(growth_res)} organic growth actions."
        log_agent_action("Orchestrator", summary, "completed")

        return {
            "success": True,
            "channel": prof_name,
            "channel_id": profile.get("id"),
            "product": prod,
            "post": post,
            "published": publish_res,
            "growth_actions": len(growth_res)
        }

    def run_all_enabled_autopilot_cycles(self) -> List[Dict[str, Any]]:
        """
        Runs autonomous cycles for all user-selected active channels independently.
        Ladies fashion posts to ladies pages, electronics posts to electronics pages.
        """
        enabled_profiles = self.get_enabled_autopilot_profiles()
        results = []
        for prof in enabled_profiles:
            res = self.run_profile_autonomous_cycle(prof)
            results.append(res)
        return results

    def run_full_daily_autonomous_cycle(self, category: Optional[str] = None, channel_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Runs cycle for active profile (backwards compatible)."""
        prof = channel_profile or self.get_active_profile()
        return self.run_profile_autonomous_cycle(prof)


    def process_chat_command(self, user_prompt: str) -> Dict[str, Any]:
        """
        Grok-style natural language interface for commanding the multi-agent team.
        """
        prompt = user_prompt.strip().lower()

        # Target Profit Update (e.g., "set target to 1000", "daily target 2000")
        target_match = re.search(r"(?:target|profit|goal)\s*(?:to|is|=)?\s*(?:inr|rs|₹)?\s*(\d+)", prompt)
        if target_match and any(w in prompt for w in ["set", "change", "target", "goal"]):
            new_val = float(target_match.group(1))
            self.set_daily_target(new_val)
            return {
                "agent": "Orchestrator",
                "response": f"🎯 **Daily Profit Target Updated to ₹{new_val:,.0f} / day!** All bot projections, units-to-goal calculations, and progress trackers have been updated."
            }

        # Test Next Product
        if any(w in prompt for w in ["test", "try next", "sample", "check next"]):
            query = None
            if "iphone" in prompt:
                query = "iPhone 16"
            elif "dress" in prompt or "fashion" in prompt:
                query = "women trending dress"
            elif "toy" in prompt:
                query = "bestselling toy"

            category = "all"
            if "mobile" in prompt or "phone" in prompt:
                category = "mobiles"
            elif "fashion" in prompt:
                category = "fashion"
            elif "toy" in prompt:
                category = "toys"

            test_res = self.test_next_product(category=category, query=query)
            if test_res.get("success"):
                p = test_res["product"]
                pst = test_res["post"]
                return {
                    "agent": "Orchestrator",
                    "response": (
                        f"⚡ **Live Product Test Completed!**\n\n"
                        f"• **Product:** {p['title'][:60]}...\n"
                        f"• **Price:** ₹{int(p['deal_price']):,} (MRP: ₹{int(p['original_price']):,})\n"
                        f"• **Est. Commission:** ₹{p.get('est_comm_per_sale', 0)} / sale (~{p.get('units_to_goal', 1)} sales to hit your ₹{self.daily_target_inr:,.0f} goal)\n"
                        f"• **Graphic Banner:** Generated and saved to `data/generated_images/`\n"
                        f"• **Headline:** {pst['headline']}\n\n"
                        f"👉 *View the full preview card in the Posts & Visual Assets tab!*"
                    ),
                    "data": test_res
                }

        # Autonomous Cycle
        if any(w in prompt for w in ["auto", "autopilot", "daily cycle", "run all", "full cycle"]):
            res = self.run_full_daily_autonomous_cycle()
            return {
                "agent": "Orchestrator",
                "response": (
                    f"🚀 **Autonomous Business Cycle Completed!**\n\n"
                    f"• **Scout Bot**: Discovered {res['scouted_count']} live deals.\n"
                    f"• **Creative Bot**: Generated {res['created_posts_count']} visual banners and reel scripts.\n"
                    f"• **Marketer Bot**: Published top deal #{res['published_post'].get('post_id')} to Instagram & Facebook.\n\n"
                    f"Everything is synced with your daily profit target of ₹{self.daily_target_inr:,.0f}/day."
                ),
                "data": res
            }

        # Content Creation
        elif any(w in prompt for w in ["create", "generate", "content", "script", "reel", "caption", "banner", "make post"]):
            scouted = get_products(status="scouted", limit=3)
            if not scouted:
                scouted = self.scout.scout_trending_products(count=2, target_profit=self.daily_target_inr)

            posts_created = []
            for p in scouted:
                post = self.creative.generate_content_for_product(p)
                posts_created.append(post)

            reply = f"🎨 **Creative Studio Report:** Generated **{len(posts_created)}** complete Instagram & Facebook post packages!\n\n"
            for p in posts_created:
                reply += (
                    f"**Post #{p['id']} Generated:**\n"
                    f"• **Headline:** {p['headline']}\n"
                    f"• **Asset:** Visual banner saved to `data/generated_images/`\n\n"
                )
            reply += "👉 *Check the preview cards in the Posts tab and click 'Publish'!*"
            return {"agent": "Creative", "response": reply, "data": posts_created}

        # Product Scouting
        elif any(w in prompt for w in ["find", "scout", "search", "products", "deals", "amazon", "flipkart", "mobiles", "fashion", "toys"]):
            category = "all"
            query = None
            if "mobile" in prompt or "phone" in prompt or "iphone" in prompt:
                category = "mobiles"
                if "iphone" in prompt:
                    query = "iPhone 16"
            elif "fashion" in prompt or "dress" in prompt:
                category = "fashion"
            elif "toy" in prompt:
                category = "toys"
            elif "kitchen" in prompt:
                category = "kitchen"

            products = self.scout.scout_trending_products(category=category, query=query, count=3, target_profit=self.daily_target_inr)
            reply = f"🔍 **Scout Bot Report:** Discovered **{len(products)}** live products in **{category.title()}**:\n\n"
            for idx, p in enumerate(products, 1):
                reply += (
                    f"**{idx}. {p['title'][:55]}...**\n"
                    f"• Deal Price: **₹{int(p['deal_price']):,}** (MRP: ₹{int(p['original_price']):,})\n"
                    f"• Est. Commission: **₹{p.get('est_comm_per_sale', 40)}/sale** (~{p.get('units_to_goal', 1)} sales to hit ₹{self.daily_target_inr:,.0f}/day)\n"
                    f"• Affiliate Link: `{p['affiliate_url']}`\n\n"
                )
            return {"agent": "Scout", "response": reply, "data": products}

        # Publishing
        elif any(w in prompt for w in ["publish", "post", "share"]):
            posts = get_posts(status="draft", limit=1)
            if not posts:
                scouted = self.scout.scout_trending_products(count=1, target_profit=self.daily_target_inr)
                posts = [self.creative.generate_content_for_product(scouted[0])]

            res = self.marketer.publish_approved_post(posts[0])
            return {
                "agent": "Marketer",
                "response": f"🚀 **Marketer Bot:** Post #{posts[0]['id']} published across Instagram, Facebook & Telegram!",
                "data": res
            }

        # Engagement
        elif any(w in prompt for w in ["engage", "audience", "comment", "like", "growth"]):
            actions = self.marketer.scout_and_engage_with_target_audience(count=3)
            return {"agent": "Marketer", "response": f"🤝 **Marketer Growth Radar:** Executed {len(actions)} safe human-like interactions.", "data": actions}

        # Revenue
        elif any(w in prompt for w in ["revenue", "income", "money", "progress", "goal", "stats", "target"]):
            history = get_revenue_history(days=7)
            total_earned = sum(h.get("estimated_earnings_inr", 0) for h in history)
            total_clicks = sum(h.get("clicks", 0) for h in history)
            return {
                "agent": "Orchestrator",
                "response": (
                    f"📊 **Financial Report:**\n\n"
                    f"• **Current Daily Target:** ₹{self.daily_target_inr:,.0f} / day (Change anytime via settings/chat)\n"
                    f"• **Total Estimated Earnings (Logged):** ₹{total_earned:,.2f}\n"
                    f"• **Total Link Clicks:** {total_clicks}"
                ),
                "data": history
            }

        else:
            return {
                "agent": "Orchestrator",
                "response": (
                    f"🤖 **AutoAffiliate AI Team Active!**\n\n"
                    f"• `Test next product` (Runs instant end-to-end live test)\n"
                    f"• `Find trending mobiles` / `Find fashion dresses` / `Find toys`\n"
                    f"• `Set target profit to 1000` (Dynamically change daily target X)\n"
                    f"• `Run full autopilot cycle`"
                )
            }
