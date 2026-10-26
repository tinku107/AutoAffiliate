"""Dynamic Multi-Platform Affiliate URL Manager.
Allows adding ANY e-commerce website (Amazon, Flipkart, Myntra, Ajio, Nykaa, Meesho, Croma, etc.)
without code modifications. Supports direct query params and aggregator deep links.
Zero TinyURL dependencies: uses official Amazon links (amzn.to / amazon.in?tag=...) directly.
"""

import re
import urllib.parse
import os
import requests
import yaml
from typing import Dict, Any, Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml")


PLACEHOLDER_IDS = {"flipkart_aff", "affiliate", "affiliate_partner", "placeholder", ""}


class AffiliateTagger:
    def __init__(self, amazon_tag: Optional[str] = None, earnkaro_id: Optional[str] = None, earnkaro_api_key: Optional[str] = None):
        self.amazon_tag = amazon_tag if amazon_tag is not None else os.getenv("AMAZON_ASSOCIATE_TAG", "tinkukrishnan-21")
        if earnkaro_id is not None:
            self.earnkaro_id = earnkaro_id
        elif earnkaro_api_key is not None:
            self.earnkaro_id = earnkaro_api_key
        else:
            self.earnkaro_id = os.getenv("EARNKARO_API_KEY", os.getenv("EARNKARO_USER_ID", "5736594"))
        self._url_cache: Dict[str, str] = {}

        # Built-in and dynamically extensible platform registry
        self.platforms: Dict[str, Dict[str, Any]] = {
            "amazon": {
                "name": "Amazon India",
                "domains": ["amazon.in", "amazon.com", "amzn.to"],
                "param": "tag",
                "id": self.amazon_tag,
                "clean_params": ["ref", "ref_", "crid", "sprefix", "keywords", "qid"]
            },
            "flipkart": {
                "name": "Flipkart",
                "domains": ["flipkart.com", "fkrt.it"],
                "param": "affid",
                "id": "flipkart_aff",
                "clean_params": ["pid", "lid", "marketplace"]
            },
            "myntra": {
                "name": "Myntra",
                "domains": ["myntra.com"],
                "param": "utm_source",
                "id": "affiliate_partner",
                "clean_params": []
            },
            "ajio": {
                "name": "Ajio",
                "domains": ["ajio.com"],
                "param": "utm_source",
                "id": "affiliate",
                "clean_params": []
            },
            "meesho": {
                "name": "Meesho",
                "domains": ["meesho.com"],
                "param": "utm_campaign",
                "id": "affiliate",
                "clean_params": []
            },
            "nykaa": {
                "name": "Nykaa",
                "domains": ["nykaa.com"],
                "param": "utm_source",
                "id": "affiliate",
                "clean_params": []
            }
        }

        # Load any user-defined custom platforms from settings.yaml
        self._load_custom_platforms()

    def _load_custom_platforms(self):
        """Loads custom platform definitions added via Admin UI from settings.yaml."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                custom = cfg.get("custom_affiliate_platforms", {})
                for key, data in custom.items():
                    if isinstance(data, dict) and "domains" in data and "param" in data:
                        self.platforms[key] = data
        except Exception as e:
            print(f"Note: Could not load custom platforms from config: {e}")

    def add_platform(
        self,
        name: str,
        domain: str,
        param: str = "tag",
        tracking_id: Optional[str] = None,
        key: Optional[str] = None,
        affiliate_id: Optional[str] = None
    ):
        """Dynamically registers a new e-commerce store with its affiliate query parameter."""
        clean_key = (key or name).lower().replace(" ", "_")
        clean_domain = domain.lower().replace("https://", "").replace("http://", "").split("/")[0]
        actual_id = (tracking_id or affiliate_id or "affiliate").strip()

        data = {
            "name": name,
            "domains": [clean_domain],
            "param": param.strip(),
            "id": actual_id,
            "clean_params": []
        }
        self.platforms[clean_key] = data

        # Persist to settings.yaml safely
        try:
            from core.orchestrator import load_settings, save_settings_safely
            cfg = load_settings()
            if "custom_affiliate_platforms" not in cfg:
                cfg["custom_affiliate_platforms"] = {}

            cfg["custom_affiliate_platforms"][clean_key] = data
            save_settings_safely(cfg)
        except Exception as e:
            print(f"Could not persist custom platform: {e}")

    def cloak_url(self, raw_affiliate_url: str) -> str:
        """Clean direct URL handler (TinyURL removed as requested)."""
        return raw_affiliate_url

    def convert_url(self, raw_url: str, platform: Optional[str] = None) -> str:
        """Converts any URL into an affiliate link dynamically based on domain matching."""
        if not raw_url:
            return ""

        raw_lower = raw_url.lower()

        # 1. Official Amazon short link (amzn.to) - preserve exactly as generated!
        if "amzn.to" in raw_lower:
            return raw_url

        # 2. Amazon regular canonical product URL
        if "amazon." in raw_lower:
            asin_match = re.search(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", raw_url)
            if asin_match:
                return f"https://www.amazon.in/dp/{asin_match.group(1)}?tag={self.amazon_tag}"
            parsed = urllib.parse.urlparse(raw_url)
            query = urllib.parse.parse_qs(parsed.query)
            query["tag"] = [self.amazon_tag]
            return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query, doseq=True)))

        # 3. Match against registered platforms
        parsed = urllib.parse.urlparse(raw_url)
        netloc = parsed.netloc.lower()

        matched_plat = None
        for key, p_data in self.platforms.items():
            for d in p_data.get("domains", []):
                if d in netloc:
                    matched_plat = p_data
                    break
            if matched_plat:
                break

        if matched_plat and matched_plat.get("param") and matched_plat.get("id"):
            plat_id = str(matched_plat["id"]).strip()
            # If user configured a real non-placeholder merchant affiliate ID
            if plat_id and plat_id not in PLACEHOLDER_IDS:
                query = urllib.parse.parse_qs(parsed.query)
                query[matched_plat["param"]] = [plat_id]
                for cp in matched_plat.get("clean_params", []):
                    query.pop(cp, None)
                new_query = urllib.parse.urlencode(query, doseq=True)
                return urllib.parse.urlunparse(parsed._replace(query=new_query))
            else:
                # Platform has a placeholder ID (e.g. flipkart_aff)
                # Route through EarnKaro aggregator if available so clicks earn real commissions!
                if self.earnkaro_id:
                    clean_url = raw_url.split("?")[0]
                    encoded = urllib.parse.quote(clean_url)
                    return f"https://earnkaro.com?r={self.earnkaro_id}&link={encoded}"
                # If no EarnKaro, return clean merchant URL without fake placeholder parameters
                clean_query = urllib.parse.parse_qs(parsed.query)
                for cp in matched_plat.get("clean_params", []):
                    clean_query.pop(cp, None)
                new_query = urllib.parse.urlencode(clean_query, doseq=True)
                return urllib.parse.urlunparse(parsed._replace(query=new_query))

        # 4. If EarnKaro aggregator is active and not Amazon
        if self.earnkaro_id and not ("amazon." in raw_lower or "amzn.to" in raw_lower):
            clean_url = raw_url.split("?")[0]
            encoded = urllib.parse.quote(clean_url)
            return f"https://earnkaro.com?r={self.earnkaro_id}&link={encoded}"

        # 5. Clean Fallback: If domain is Amazon, ensure tag is present
        if "amazon." in netloc or "amzn" in netloc:
            return f"{raw_url}&tag={self.amazon_tag}" if "?" in raw_url else f"{raw_url}?tag={self.amazon_tag}"

        # For any unknown 3rd-party store, return clean URL as-is (NEVER append &tag=)
        return raw_url

    tag_url = convert_url

    def convert_url_details(self, raw_url: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns the official public referral URL (shown to followers)
        and tracking metadata. Zero TinyURL dependency.
        """
        if not raw_url:
            return {"public_url": "", "raw_tracking_url": "", "is_cloaked": False, "link_type": "empty"}

        raw_lower = raw_url.lower()

        # 1. Official Amazon short link (amzn.to)
        if "amzn.to" in raw_lower:
            return {
                "public_url": raw_url,
                "raw_tracking_url": raw_url,
                "is_cloaked": False,
                "link_type": "amzn_to"
            }

        # 2. Canonical Amazon Associate URL
        if "amazon." in raw_lower:
            asin_match = re.search(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", raw_url)
            if asin_match:
                amz_url = f"https://www.amazon.in/dp/{asin_match.group(1)}?tag={self.amazon_tag}"
                return {
                    "public_url": amz_url,
                    "raw_tracking_url": amz_url,
                    "is_cloaked": False,
                    "link_type": "amazon_canonical"
                }

        # 3. Check registered platforms or EarnKaro
        conv = self.convert_url(raw_url, platform)
        l_type = "earnkaro" if "earnkaro.com" in conv else ("direct" if conv != raw_url else "clean")
        return {
            "public_url": conv,
            "raw_tracking_url": conv,
            "is_cloaked": False,
            "link_type": l_type
        }

    def get_disclosure_text(self) -> str:
        return "#ad #affiliate #commissionsearned #dealsindia"
