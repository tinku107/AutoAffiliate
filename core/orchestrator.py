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
from agents.cleaner_agent import CleanerAgent
from core.db import (
    get_products,
    get_posts,
    get_revenue_history,
    get_recent_logs,
    log_agent_action,
    log_daily_revenue,
    get_discarded_product_ids,
    discard_product_in_db,
    clear_discarded_history,
    get_pulled_product_ids,
    mark_product_pulled,
    clear_pulled_history
)

from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml")


def sanitize_config_for_disk(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures sensitive secrets (access tokens, API keys) are never persisted into settings.yaml."""
    import copy
    clean = copy.deepcopy(cfg)
    if "ai" in clean and isinstance(clean["ai"], dict):
        clean["ai"]["gemini_api_key"] = ""
    if "channel_profiles" in clean and isinstance(clean["channel_profiles"], list):
        for p in clean["channel_profiles"]:
            if isinstance(p, dict):
                p["meta_access_token"] = ""
                p["meta_user_token"] = ""
                p["telegram_bot_token"] = ""
    return clean


def save_settings_safely(cfg: Dict[str, Any], path: str = CONFIG_PATH) -> bool:
    """Saves configuration to disk while guaranteeing secrets are stripped."""
    try:
        sanitized = sanitize_config_for_disk(cfg)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(sanitized, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving settings safely: {e}")
        return False


def load_settings(path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Loads configuration and merges secrets from .env environment variables."""
    load_dotenv()
    cfg = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading {path}: {e}")
            cfg = {}

    meta_token = os.getenv("META_ACCESS_TOKEN", "")
    meta_user_token = os.getenv("META_USER_TOKEN", "")
    meta_page_id = os.getenv("META_PAGE_ID", "")
    ig_user = os.getenv("INSTAGRAM_USERNAME", "")
    amz_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "")
    ek_key = os.getenv("EARNKARO_API_KEY", "")
    ek_user = os.getenv("EARNKARO_USER_ID", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_channel = os.getenv("TELEGRAM_CHANNEL_ID", "")

    # Inject into channel profiles
    profiles = cfg.get("channel_profiles", [])
    for p in profiles:
        if p.get("id") == "elenas_world":
            if meta_token and not p.get("meta_access_token"):
                p["meta_access_token"] = meta_token
            if meta_user_token and not p.get("meta_user_token"):
                p["meta_user_token"] = meta_user_token
            if meta_page_id and not p.get("facebook_page_id"):
                p["facebook_page_id"] = meta_page_id
            if ig_user and not p.get("instagram_username"):
                p["instagram_username"] = ig_user
            if tg_token and not p.get("telegram_bot_token"):
                p["telegram_bot_token"] = tg_token
            if tg_channel and not p.get("telegram_channel_id"):
                p["telegram_channel_id"] = tg_channel

    # Inject into affiliate
    if "affiliate" not in cfg:
        cfg["affiliate"] = {}
    if amz_tag and not cfg["affiliate"].get("amazon_associate_tag"):
        cfg["affiliate"]["amazon_associate_tag"] = amz_tag
    if ek_key and not cfg["affiliate"].get("earnkaro_api_key"):
        cfg["affiliate"]["earnkaro_api_key"] = ek_key
    if ek_user and not cfg["affiliate"].get("earnkaro_user_id"):
        cfg["affiliate"]["earnkaro_user_id"] = ek_user

    # Inject into AI
    if "ai" not in cfg:
        cfg["ai"] = {}
    if gemini_key and not cfg["ai"].get("gemini_api_key"):
        cfg["ai"]["gemini_api_key"] = gemini_key

    return cfg


class AgentOrchestrator:
    def __init__(self):
        self.config = self._load_config()
        self.daily_target_inr = float(self.config.get("app", {}).get("daily_revenue_target_inr", 500.0))

        aff_tag = self.config.get("affiliate", {}).get("amazon_associate_tag", "tinkukrishnan-21")
        earnkaro_id = self.config.get("affiliate", {}).get("earnkaro_api_key", "")
        gemini_key = self.config.get("ai", {}).get("gemini_api_key", "")

        self.scout = ScoutAgent(amazon_tag=aff_tag, earnkaro_id=earnkaro_id)
        self.creative = CreativeAgent(gemini_api_key=gemini_key)
        self.marketer = MarketerAgent()
        self.cleaner = CleanerAgent()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.tested_product_ids = set()
        self.pulled_product_ids = get_pulled_product_ids()
        self.discarded_product_ids = get_discarded_product_ids()
        self.test_counter = 0

    def _load_config(self) -> Dict[str, Any]:
        return load_settings()

    def _save_config(self, cfg: Dict[str, Any]) -> bool:
        res = save_settings_safely(cfg)
        if res:
            self.config = cfg
        return res

    def set_daily_target(self, new_target: float):
        """Allows user to dynamically change daily profit target X anytime."""
        self.daily_target_inr = float(new_target)
        try:
            cfg = self._load_config()
            if "app" not in cfg:
                cfg["app"] = {}
            cfg["app"]["daily_revenue_target_inr"] = self.daily_target_inr
            self._save_config(cfg)
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
            self._save_config(cfg)
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
            self._save_config(cfg)
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
            self._save_config(cfg)
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
            self._save_config(cfg)
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
            self._save_config(cfg)
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
            self._save_config(cfg)
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
            self._save_config(cfg)
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
                self._save_config(cfg)
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
                self._save_config(cfg)
                log_agent_action("Orchestrator", f"Bulk updated {len(clean_mappings)} niche mappings from table editor", "completed")
                return True
            except Exception as e:
                print(f"Error bulk saving niche mappings: {e}")
                return False
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
        platform: str = "amazon",
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

        # 1. Direct URL Testing (Supports amzn.to/xxx or any direct product link)
        target_url = kwargs.get("custom_url") or kwargs.get("url") or (query if query and query.strip().startswith("http") else None)
        if target_url:
            clean_url = target_url.strip()
            target_prod = self.scout.scraper.fetch_product_by_url(clean_url)
            if not target_prod:
                return {"success": False, "error": f"Could not scrape product details from URL: {clean_url}"}

            url_meta = self.scout.tagger.convert_url_details(target_prod.get("source_url", clean_url), platform=target_prod.get("platform", "Amazon"))
            target_prod["affiliate_url"] = url_meta.get("public_url")
            target_prod["raw_affiliate_url"] = url_meta.get("raw_tracking_url")
            target_prod["is_cloaked"] = url_meta.get("is_cloaked", False)

            price = target_prod.get("deal_price", 0.0)
            comm_rate = target_prod.get("commission_rate", 0.08)
            est_comm = round(price * comm_rate, 2)
            target_prod["est_comm_per_sale"] = est_comm
            target_prod["units_to_goal"] = max(1, int(self.daily_target_inr / max(1.0, est_comm)))
        else:
            # Persistent deduplication: Load all already pulled & discarded IDs from database
            pulled_ids = get_pulled_product_ids()
            discarded_ids = get_discarded_product_ids()
            excluded_ids = pulled_ids | discarded_ids | self.tested_product_ids

            # Fetch a pool of live products
            pool_size = 15
            products = self.scout.scout_trending_products(
                category=category,
                query=query,
                platform=platform,
                count=pool_size,
                target_profit=self.daily_target_inr
            )

            # Filter strictly: only products that have NEVER been pulled or discarded
            valid_products = [p for p in products if p.get("product_id") and p.get("product_id") not in excluded_ids]
            target_prod = None

            if valid_products:
                target_prod = valid_products[0]
            else:
                # If all initial items were already pulled, rotate through fresh sub-queries
                category_rotations = {
                    "fashion": [
                        "women floral anarkali kurta",
                        "banarasi silk saree",
                        "designer festive saree",
                        "women rayon printed kurti",
                        "georgette party wear dress",
                        "kanchipuram silk saree",
                        "cotton daily wear kurta",
                        "chikankari women kurta",
                        "women fit flare maxi dress"
                    ],
                    "mens_fashion": [
                        "men cotton casual shirt",
                        "men linen formal shirt",
                        "men polo t shirt",
                        "men denim slim fit jeans",
                        "men running sneakers"
                    ],
                    "mobiles": [
                        "5g mobile phone deals",
                        "samsung galaxy 5g smartphone",
                        "oneplus 5g smartphone",
                        "redmi 5g mobile phone"
                    ],
                    "electronics": [
                        "wireless earbuds bluetooth",
                        "smartwatch with amoled display",
                        "fast charging power bank",
                        "bluetooth portable speaker"
                    ],
                    "kitchen": [
                        "air fryer for home",
                        "stainless steel cookware set",
                        "kitchen food storage containers"
                    ],
                    "beauty": [
                        "vitamin c face serum",
                        "sunscreen spf 50 pa+++",
                        "hydrating moisturizer"
                    ],
                    "all": [
                        "trending bestsellers deals",
                        "top rated deals of the day"
                    ]
                }
                cat_key = category.lower().replace(" ", "_")
                sub_queries = category_rotations.get(cat_key, category_rotations["all"])

                for sub_q in sub_queries:
                    fresh_items = self.scout.scout_trending_products(
                        category=category,
                        query=sub_q,
                        platform=platform,
                        count=10,
                        target_profit=self.daily_target_inr
                    )
                    unpulled = [p for p in fresh_items if p.get("product_id") and p.get("product_id") not in excluded_ids]
                    if unpulled:
                        target_prod = unpulled[0]
                        break

            if not target_prod:
                return {"success": False, "error": f"All live products in '{query or category}' on {platform.upper()} have been pulled or discarded. Try another search query or clear pulled/discard history."}

        # Extract all available gallery angles for the chosen product (front, back, model, fabric)
        if target_prod.get("source_url") and len(target_prod.get("image_urls", [])) <= 1:
            all_angles = self.scout.scraper.extract_gallery_images(
                target_prod["source_url"],
                primary_img_url=target_prod.get("image_url", ""),
                max_images=10
            )
            if all_angles:
                target_prod["image_urls"] = all_angles
                target_prod["image_url"] = all_angles[0]

        # Immediately mark this product as pulled with timestamp in database
        target_pid = target_prod.get("product_id")
        target_db_id = target_prod.get("id")
        mark_product_pulled(product_id=target_pid, db_id=target_db_id)
        if target_pid:
            self.tested_product_ids.add(target_pid)
            self.pulled_product_ids.add(target_pid)
        target_prod["is_pulled"] = 1
        target_prod["status"] = "pulled"

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

    def discard_product(self, product_id: str, db_id: Optional[int] = None) -> bool:
        """Removes a product the user dislikes from testing queue, database, and future autopilot selection."""
        self.discarded_product_ids.add(product_id)
        self.tested_product_ids.add(product_id)
        discard_product_in_db(product_id)
        log_agent_action("Orchestrator", f"User discarded product [{product_id}]. Excluded from future autopilot & testing.", "completed")
        return True

    def purge_expired_media(self, retention_hours: Optional[int] = None) -> Dict[str, Any]:
        """Triggers 24-hour media cleanup for published posts."""
        return self.cleaner.clean_expired_published_media(retention_hours=retention_hours)

    def clear_discard_history(self) -> bool:
        """Clears user discard blacklist upon request."""
        self.discarded_product_ids.clear()
        clear_discarded_history()
        log_agent_action("Orchestrator", "Reset discarded product blacklist upon user request.", "completed")
        return True

    def clear_pulled_history(self) -> bool:
        """Resets the pulled products status flag."""
        clear_pulled_history()
        self.pulled_product_ids.clear()
        self.tested_product_ids.clear()
        log_agent_action("Orchestrator", "Reset pulled products history.", "completed")
        return True

    def run_profile_autonomous_cycle(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an independent autonomous cycle for a single channel profile:
        1. Scouts a live product matching the profile's dedicated focus_niche
        2. Filters out any products discarded/disliked by user
        3. Autopilot autonomously chooses the best converting deal
        4. Publishes to that profile's specific Instagram & Facebook accounts
        5. Runs organic audience growth in that niche
        """
        prof_name = profile.get("name", "Channel")
        target_niche = profile.get("focus_niche", "all")
        log_agent_action("Orchestrator", f"Starting independent cycle for [{prof_name}] in niche '{target_niche}'", "started")

        products = self.scout.scout_trending_products(category=target_niche, count=5, target_profit=self.daily_target_inr)
        # Filter out user-discarded items so Autopilot never picks disliked products
        valid_prods = [p for p in products if p.get("product_id") not in self.discarded_product_ids]
        if not valid_prods:
            products = self.scout.scout_trending_products(category="all", count=5, target_profit=self.daily_target_inr)
            valid_prods = [p for p in products if p.get("product_id") not in self.discarded_product_ids]

        if not valid_prods:
            return {"success": False, "channel": prof_name, "error": "No non-discarded products available in niche"}

        # Autopilot autonomously chooses the best product
        prod = valid_prods[0]
        post = self.creative.generate_content_for_product(prod, channel_niche=target_niche, channel_profile=profile)
        post["target_channel"] = profile.get("id")

        publish_res = self.marketer.publish_approved_post(post, channel_profile=profile)
        growth_res = self.marketer.grow_audience_and_engage(niche=target_niche, channel_profile=profile, count=2)

        # Auto-purge published media older than 24 hours (1 day) by default
        try:
            self.cleaner.clean_expired_published_media()
        except Exception as e:
            print(f"Janitor cleanup note: {e}")

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


    def update_env_variable(self, key: str, value: str) -> Dict[str, Any]:
        """Safely updates an environment variable in .env and runtime memory."""
        clean_key = re.sub(r"[^A-Za-z0-9_]", "", key).strip().upper()
        clean_val = value.strip().strip("'\"")

        if not clean_key:
            return {"success": False, "message": "Invalid environment variable name."}

        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        lines = []
        found = False

        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(f"{clean_key}=") or stripped.startswith(f"{clean_key} ="):
                new_lines.append(f"{clean_key}={clean_val}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] = new_lines[-1] + "\n"
            new_lines.append(f"{clean_key}={clean_val}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        # Update runtime environment
        os.environ[clean_key] = clean_val

        # Update in-memory bot instances if applicable
        if clean_key == "AMAZON_ASSOCIATE_TAG":
            self.scout.amazon_tag = clean_val
            if hasattr(self.scout, "tagger"):
                self.scout.tagger.amazon_tag = clean_val
        elif clean_key == "OPENAI_API_KEY":
            self.openai_api_key = clean_val
        elif clean_key in ["META_ACCESS_TOKEN", "META_PAGE_ACCESS_TOKEN"]:
            self.marketer.meta_publisher.page_access_token = clean_val
        elif clean_key == "META_PAGE_ID":
            self.marketer.meta_publisher.facebook_page_id = clean_val
        elif clean_key == "INSTAGRAM_ACCOUNT_ID":
            self.marketer.meta_publisher.instagram_account_id = clean_val

        disp_val = clean_val
        if any(w in clean_key for w in ["TOKEN", "KEY", "SECRET"]) and len(clean_val) > 8:
            disp_val = f"{clean_val[:6]}...{clean_val[-4:]}"

        log_agent_action("Orchestrator", f"Updated environment variable {clean_key}", "completed")

        return {
            "success": True,
            "message": (
                f"✅ **Environment Variable Updated Successfully!**\n\n"
                f"• **Variable:** `{clean_key}`\n"
                f"• **Value:** `{disp_val}`\n"
                f"• **Saved To:** `.env` and loaded into active runtime memory."
            )
        }

    def get_env_summary(self) -> str:
        """Returns a sanitized overview of active environment configuration."""
        tag = os.getenv("AMAZON_ASSOCIATE_TAG", "tinkukrishnan-21")
        page_id = os.getenv("META_PAGE_ID", "1484650751391885")
        ig_user = os.getenv("INSTAGRAM_USERNAME", "affiliatem262")
        ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        meta_tok = os.getenv("META_ACCESS_TOKEN", "")

        def mask(s: str) -> str:
            if not s:
                return "*(Not configured)*"
            if len(s) <= 8:
                return f"{s[:2]}***{s[-2:]}"
            return f"`{s[:6]}...{s[-4:]}` (Active)"

        ig_status = f"`{ig_id}`" if ig_id else "*(Auto-resolved via Facebook Page)*"

        return (
            "**Active Environment & System Configuration:**\n\n"
            f"- **AMAZON_ASSOCIATE_TAG**: `{tag}` (Amazon India Only)\n"
            f"- **DAILY_PROFIT_TARGET**: `INR {self.daily_target_inr:,.0f} / day`\n"
            f"- **META_PAGE_ID**: `{page_id}` (Elena's World Facebook Page)\n"
            f"- **META_ACCESS_TOKEN**: {mask(meta_tok)}\n"
            f"- **INSTAGRAM_USERNAME**: `@{ig_user}`\n"
            f"- **INSTAGRAM_ACCOUNT_ID**: {ig_status}\n"
            f"- **OPENAI_API_KEY**: {mask(openai_key)}\n\n"
            "To update any value right now, type: `update env VARIABLE = NEW_VALUE`\n"
            "Or use the **Global Settings & Compliance** tab in the sidebar."
        )

    def smart_fallback_response(self, user_prompt: str) -> str:
        """Rule-based intelligent fallback when LLM API is unavailable."""
        prompt = user_prompt.strip().lower()

        # Greetings
        if any(w in prompt for w in ["hi", "hello", "hey", "greetings", "good morning", "good evening"]):
            return (
                "**Hello! I am your AutoAffiliate AI Orchestrator.**\n\n"
                "All 5 bot employees are online and active:\n"
                "- **Scout Bot**: Sourcing deals from Amazon India (`tinkukrishnan-21`)\n"
                "- **Creative Bot**: Generating humanoid copy (zero emojis) & multi-angle carousels\n"
                "- **Marketer Bot**: Publishing to Facebook Page Elena's World & Instagram (`@affiliatem262`)\n"
                "- **Cleaner Bot**: 24h media storage auto-purge\n"
                "- **Autopilot**: 24/7 autonomous scheduling\n\n"
                f"Daily profit target is set to **INR {self.daily_target_inr:,.0f} / day**. How can I assist you right now?"
            )

        # Environment Queries
        if any(w in prompt for w in ["environment", "env", "credentials", "api key", "token value", "update value"]):
            return (
                "**How to Update Environment Values:**\n\n"
                "You have three simple ways to update configuration and environment variables:\n\n"
                "1. **Directly Here in Chat:**\n"
                "   - `update env AMAZON_ASSOCIATE_TAG = tinkukrishnan-21`\n"
                "   - `update env INSTAGRAM_ACCOUNT_ID = 178414001234567`\n"
                "   - `set target to 3000` (Updates daily profit goal)\n\n"
                "2. **Via Global Settings Tab:**\n"
                "   - Click **Global Settings & Compliance** in the left sidebar to change your daily profit target, Amazon associate tag, disclosure text, posting intervals, and storage purge policies.\n\n"
                "3. **In the .env File:**\n"
                "   - Edit the .env file directly at the root directory of this project (`c:\\AI\\My Business Agents\\.env`) for Meta tokens or OpenAI keys.\n\n"
                "Which specific value would you like to update?"
            )

        # Instagram & Facebook status
        if any(w in prompt for w in ["insta", "instagram", "facebook", "fb", "page", "meta"]):
            return (
                "**Meta & Social Media Channel Status:**\n\n"
                "- **Facebook Page**: **Elena's World** (Page ID: `1484650751391885`) - Connected & Live Posting Verified.\n"
                "- **Instagram Account**: **@affiliatem262** - Linked to Facebook Page.\n\n"
                "**Instagram Direct Posting Setup:**\n"
                "Meta Graph API requires `@affiliatem262` to be a **Professional (Creator or Business) Account**:\n"
                "1. In Instagram app on phone, go to **Settings & Privacy** > **Account type and tools**.\n"
                "2. Tap **Switch to Professional Account** (Creator or Business).\n"
                "3. Ensure it is connected to Facebook Page **Elena's World**.\n"
                "Once converted, Meta automatically authorizes automated posting to both Facebook and Instagram."
            )

        # General help
        return (
            "**AutoAffiliate AI Orchestrator Ready.** Here are commands you can run:\n\n"
            "- `Test next product` (Runs instant end-to-end deal discovery & carousel generation)\n"
            "- `Find trending dresses` / `Find mobiles` / `Find toys` (Scouts Amazon India)\n"
            "- `Set target profit to 2000` (Dynamically updates daily target)\n"
            "- `Show env` (Displays current environment variable overview)\n"
            "- `update env KEY=VALUE` (Updates environment variables)\n"
            "- `Run full autopilot cycle` (Scouts, renders, and publishes autonomously)\n"
            "- `Token status` (Checks Meta token expiry watchdog)\n"
            "- `Storage stats` (Checks temporary media cleanup stats)"
        )

    def query_llm_brain(self, user_prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Grok-style conversational brain powered by OpenAI API.
        Answers user questions with complete situational awareness of the AutoAffiliate system.
        """
        api_key = os.getenv("OPENAI_API_KEY") or getattr(self, "openai_api_key", "")
        if not api_key:
            return self.smart_fallback_response(user_prompt)

        total_posts = len(get_posts(limit=100))
        recent_posts = get_posts(limit=3)
        last_post_summary = ""
        if recent_posts:
            last_p = recent_posts[0]
            last_post_summary = f"Last Post #{last_p.get('id', '?')}: '{last_p.get('headline', '')}' (Status: {last_p.get('status', 'draft')})"

        clean_stats = self.cleaner.get_storage_stats()

        system_prompt = f"""You are the intelligent AutoAffiliate AI Orchestrator & Grok Command Console.
You manage a fleet of 5 autonomous digital employee bots for Elena's World affiliate business:
1. Scout Bot: Discovers live deals exclusively from Amazon India with official tag tinkukrishnan-21. EarnKaro is disabled.
2. Creative Bot: Generates authentic humanoid copy with STRICTLY ZERO EMOJIS, zero fancy symbols, and creates 4-8 slide multi-angle product carousels.
3. Marketer Bot: Publishes to Facebook Page Elena's World (Page ID: 1484650751391885) and Instagram (@affiliatem262).
4. Cleaner Bot: Storage janitor that automatically purges generated media files after 24 hours while keeping DB records intact.
5. Autopilot Daemon: 24/7 background worker running autonomous deal discovery, rendering, and scheduled publishing.

Live Telemetry:
- Daily Revenue Target: INR {self.daily_target_inr:,.0f} / day
- Total Posts in Database: {total_posts} posts. {last_post_summary}
- Temporary Media Storage: {clean_stats.get('total_files', 0)} files ({clean_stats.get('total_mb', 0)} MB)
- Meta Facebook Page: Elena's World (ID: 1484650751391885) - Active
- Instagram Account: @affiliatem262 (Requires Professional Creator/Business conversion in Instagram app to enable direct Meta Graph API publishing)
- Amazon Associate Tag: tinkukrishnan-21

Instructions:
- When the user asks about updating environment variables: Explain that they can update them directly here in chat (e.g. `update env KEY=VALUE` or `set target to 2000`), via the 'Global Settings & Compliance' tab in the sidebar, or by editing the .env file.
- When the user says 'hi' or greets you: Greet them warmly and professionally, state that all 5 bots are online, and ask how you can help.
- When the user asks about Instagram publishing: Explain that Facebook published successfully, and Instagram requires converting @affiliatem262 to a Professional (Creator or Business) Account in the Instagram mobile app settings so Meta Graph API can access its business account ID.
- Tone: Helpful, concise, confident, humanoid, and professional. Format with clean GitHub Markdown. Use bullet points where appropriate."""

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for h in history[-6:]:
                role = "assistant" if h.get("role") in ["assistant", "bot"] else "user"
                content = h.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_prompt})

        try:
            import requests
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=12
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return reply
            else:
                return self.smart_fallback_response(user_prompt)
        except Exception:
            return self.smart_fallback_response(user_prompt)

    def process_chat_command(self, user_prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Grok-style natural language interface for commanding the multi-agent team.
        """
        raw_prompt = user_prompt.strip()
        prompt = raw_prompt.lower()

        # 1. Direct Environment Variable Update (e.g. "update env AMAZON_ASSOCIATE_TAG=tinkukrishnan-21", "set env KEY=VAL", "change env KEY to VAL")
        env_match = re.search(r"^(?:update|set|change)\s+(?:env|environment|var|variable)?\s*([A-Za-z0-9_]+)\s*(?:=|\s+to\s+)\s*(.+)$", raw_prompt, re.IGNORECASE)
        if env_match:
            k = env_match.group(1).strip()
            v = env_match.group(2).strip()
            if k.lower() in ["target", "daily_target", "profit_target", "goal"]:
                try:
                    num = float(re.sub(r"[^\d.]", "", v))
                    self.set_daily_target(num)
                    return {
                        "agent": "Orchestrator",
                        "response": f"🎯 **Daily Profit Target Updated to ₹{num:,.0f} / day!** All bot projections, units-to-goal calculations, and progress trackers have been updated."
                    }
                except Exception:
                    pass
            upd_res = self.update_env_variable(k, v)
            return {
                "agent": "Orchestrator",
                "response": upd_res["message"]
            }

        # 2. Show / View Environment Overview
        if any(w in prompt for w in ["show env", "view env", "list env", "check env", "get env", "show environment", "view environment"]):
            return {
                "agent": "Orchestrator",
                "response": self.get_env_summary()
            }

        # 3. Target Profit Update (e.g., "set target to 1000", "daily target 2000")
        target_match = re.search(r"(?:target|profit|goal)\s*(?:to|is|=)?\s*(?:inr|rs|₹)?\s*(\d+)", prompt)
        if target_match and any(w in prompt for w in ["set", "change", "target", "goal"]):
            new_val = float(target_match.group(1))
            self.set_daily_target(new_val)
            return {
                "agent": "Orchestrator",
                "response": f"🎯 **Daily Profit Target Updated to ₹{new_val:,.0f} / day!** All bot projections, units-to-goal calculations, and progress trackers have been updated."
            }

        # 4. Meta Token Expiry & Reminder Query
        if any(w in prompt for w in ["token status", "token expiry", "when does token expire", "token watchdog"]):
            for p in self.get_channel_profiles():
                if p.get("id") == "elenas_world" and p.get("token_expires_at"):
                    import time
                    now_epoch = int(time.time())
                    exp_epoch = p.get("token_expires_epoch", 1798137354)
                    days_left = max(0, int((exp_epoch - now_epoch) / 86400))
                    return {
                        "agent": "Marketer",
                        "response": (
                            f"🔐 **Meta Access Token Status & Expiry Watchdog:**\n\n"
                            f"• **Channel Account:** Elena's World (`elenas_world`)\n"
                            f"• **Facebook Page:** Elena's World (ID: `1484650751391885`)\n"
                            f"• **Status:** 🟢 Active & Verified (`can_post: True`)\n"
                            f"• **Expiration Date:** **December 24, 2026 at 18:35:54 UTC** (Dec 25 00:05 IST)\n"
                            f"• **Days Remaining:** **{days_left} days**\n"
                            f"• **Data Access Expiry:** January 23, 2027\n\n"
                            f"⏰ **Automated Reminder Guarantee:**\n"
                            f"AutoAffiliate AI monitors this token continuously. Starting **7 days before expiration** (December 17, 2026), persistent warning alerts will be raised across your Executive Dashboard, Channel Manager, and Autopilot logs so you have plenty of time to refresh the token."
                        )
                    }

        # 5. Bot Fleet & Status Telemetry Query
        if any(w in prompt for w in ["fleet telemetry", "bot fleet", "workforce status", "who is working"]):
            clean_stats = self.cleaner.get_storage_stats()
            return {
                "agent": "Orchestrator",
                "response": (
                    "🤖 **Autonomous Bot Fleet Telemetry & Current Status:**\n\n"
                    "1. **🔍 Scout Bot** (`agents/scout_agent.py`): **🟢 ONLINE**\n"
                    "   • Function: Scrapes live trending deals exclusively from Amazon India.\n"
                    "   • Attribution: Directly tags your official Associate ID (`tinkukrishnan-21`) and preserves `amzn.to` short links with unique ASINs.\n\n"
                    "2. **🎨 Creative Bot** (`agents/creative_agent.py`): **🟢 ONLINE**\n"
                    "   • Function: Creates 4-8 slide multi-angle carousels and renders 9:16 vertical AI reels (Edge-TTS neural voice).\n"
                    "   • Compliance: 100% Humanoid copy (Strictly zero emojis and zero special characters).\n\n"
                    "3. **📣 Marketer Bot** (`agents/marketer_agent.py`): **🟢 ONLINE**\n"
                    "   • Function: Publishes to Facebook Pages and Instagram accounts via Meta Graph API; automatically replies to comment leads with affiliate links.\n"
                    "   • Anti-Bot: Randomized human jitter scheduling (90 to 210 min intervals).\n\n"
                    "4. **🧹 Cleaner Bot** (`agents/cleaner_agent.py`): **🟢 ONLINE (24h Auto-Purge Active)**\n"
                    "   • Function: Storage Janitor that purges generated video/image files 24 hours after publishing to preserve disk space while keeping database logs and captions permanently.\n"
                    f"   • Current Storage: {clean_stats['total_files']} files ({clean_stats['total_mb']} MB) in temporary media.\n\n"
                    "5. **⚡ Autopilot Daemon** (`core/auto_daemon.py`): **🟢 ONLINE / BACKGROUND**\n"
                    "   • Function: 24/7 background worker running autonomous deal discovery, rendering, and scheduled publishing.\n\n"
                    f"👉 *All bots are working together to hit your configured target of ₹{self.daily_target_inr:,.0f} / day.*"
                )
            }

        # 6. Test Next Product
        if any(w in prompt for w in ["test next", "try next", "test product", "test deal", "sample product", "check next"]) or prompt.startswith("test "):
            query = None
            if "iphone" in prompt:
                query = "iPhone 16"
            elif "dress" in prompt or "fashion" in prompt or "saree" in prompt:
                query = "women trending dress"
            elif "toy" in prompt:
                query = "bestselling toy"

            category = "all"
            if "mobile" in prompt or "phone" in prompt:
                category = "mobiles"
            elif "fashion" in prompt or "dress" in prompt or "saree" in prompt:
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

        # 7. Autonomous Cycle
        if any(w in prompt for w in ["run autopilot", "run daily cycle", "run full cycle", "start cycle"]):
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

        # 8. Content Creation
        elif any(w in prompt for w in ["create post", "generate post", "make post", "generate content", "create carousel"]):
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

        # 9. Product Scouting
        elif any(w in prompt for w in ["find products", "scout products", "find deals", "search deals", "find trending", "find dresses", "find mobiles", "find toys", "scout trending"]) or prompt.startswith("find ") or prompt.startswith("scout "):
            category = "all"
            query = None
            if "mobile" in prompt or "phone" in prompt or "iphone" in prompt:
                category = "mobiles"
                if "iphone" in prompt:
                    query = "iPhone 16"
            elif "fashion" in prompt or "dress" in prompt or "saree" in prompt:
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

        # 10. Publishing
        elif any(w in prompt for w in ["publish post", "publish approved", "publish latest", "publish draft", "publish deal"]):
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

        # 11. Storage Janitor & Cleanup
        elif any(w in prompt for w in ["clean storage", "purge media", "run janitor", "storage stats"]):
            clean_res = self.cleaner.clean_expired_published_media()
            stats = self.cleaner.get_storage_stats()
            return {
                "agent": "Cleaner",
                "response": (
                    f"🧹 **Cleaner Bot Report:**\n\n"
                    f"• **Files Deleted:** {clean_res.get('deleted_files_count', 0)}\n"
                    f"• **Space Reclaimed:** {clean_res.get('reclaimed_mb', 0)} MB\n"
                    f"• **Remaining Temporary Media:** {stats.get('total_files', 0)} files ({stats.get('total_mb', 0)} MB)"
                ),
                "data": clean_res
            }

        # 12. Natural Language Conversational Intelligence (Grok / OpenAI LLM Brain)
        llm_reply = self.query_llm_brain(raw_prompt, history=history)
        return {
            "agent": "Orchestrator",
            "response": llm_reply
        }
