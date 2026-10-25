"""Dynamic Multi-Platform Affiliate URL Manager.
Allows adding ANY e-commerce website (Amazon, Flipkart, Myntra, Ajio, Nykaa, Meesho, Croma, etc.)
without code modifications. Supports direct query params and aggregator deep links.
"""

import re
import urllib.parse
import os
import requests
import yaml
from typing import Dict, Any, Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml")


class AffiliateTagger:
    def __init__(self, amazon_tag: str = "autoaffil-21", earnkaro_id: Optional[str] = None):
        self.amazon_tag = amazon_tag or "autoaffil-21"
        self.earnkaro_id = earnkaro_id
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

        self._load_custom_platforms()

    def _load_custom_platforms(self):
        """Loads custom user-added platforms from settings.yaml."""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    custom = cfg.get("custom_affiliate_platforms", {})
                    for k, v in custom.items():
                        self.platforms[k.lower()] = v
            except Exception:
                pass

    def add_platform(self, key: str, name: str, domain: str, param: str, affiliate_id: str):
        """Dynamically registers any new e-commerce website at runtime."""
        clean_key = key.lower().strip()
        data = {
            "name": name,
            "domains": [domain.lower().replace("https://", "").replace("http://", "").strip("/")],
            "param": param.strip(),
            "id": affiliate_id.strip(),
            "clean_params": []
        }
        self.platforms[clean_key] = data

        # Persist to settings.yaml
        try:
            cfg = {}
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}

            if "custom_affiliate_platforms" not in cfg:
                cfg["custom_affiliate_platforms"] = {}

            cfg["custom_affiliate_platforms"][clean_key] = data

            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False)
        except Exception as e:
            print(f"Could not persist custom platform: {e}")

    def cloak_url(self, raw_affiliate_url: str) -> str:
        """
        Cloaks/shortens affiliate links (specifically EarnKaro and deep tracking links)
        so followers and social algorithms NEVER see raw 'earnkaro.com' tracking links.
        Uses TinyURL's free instant API with memory caching.
        """
        if not raw_affiliate_url:
            return ""

        if raw_affiliate_url in self._url_cache:
            return self._url_cache[raw_affiliate_url]

        try:
            api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(raw_affiliate_url)}"
            resp = requests.get(api_url, timeout=5)
            if resp.status_code == 200 and resp.text.startswith("http"):
                shortened = resp.text.strip()
                self._url_cache[raw_affiliate_url] = shortened
                return shortened
        except Exception as e:
            print(f"URL cloaking fallback note: {e}")

        # If offline or TinyURL unreachable, never expose earnkaro.com directly!
        if "earnkaro.com" in raw_affiliate_url:
            m = re.search(r"link=([^&]+)", raw_affiliate_url)
            clean_dest = urllib.parse.unquote(m.group(1)) if m else raw_affiliate_url
            return clean_dest

        return raw_affiliate_url

    def convert_url(self, raw_url: str, platform: Optional[str] = None) -> str:
        """Converts any URL into an affiliate link dynamically based on domain matching."""
        if not raw_url:
            return ""

        # Special Amazon ASIN extraction
        if "amazon." in raw_url:
            asin_match = re.search(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", raw_url)
            if asin_match:
                return f"https://www.amazon.in/dp/{asin_match.group(1)}?tag={self.amazon_tag}"

        # If EarnKaro aggregator is active and not Amazon
        if self.earnkaro_id and not "amazon." in raw_url:
            clean_url = raw_url.split("?")[0]
            encoded = urllib.parse.quote(clean_url)
            raw_ek = f"https://earnkaro.com?r={self.earnkaro_id}&link={encoded}"
            # STRICT RULE: NEVER show earnkaro.com directly to followers!
            # Automatically cloaks into clean short link
            return self.cloak_url(raw_ek)

        # Match against registered platforms
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
            query = urllib.parse.parse_qs(parsed.query)
            query[matched_plat["param"]] = [matched_plat["id"]]
            for cp in matched_plat.get("clean_params", []):
                query.pop(cp, None)
            new_query = urllib.parse.urlencode(query, doseq=True)
            return urllib.parse.urlunparse(parsed._replace(query=new_query))

        # Fallback default parameter
        return f"{raw_url}&tag={self.amazon_tag}" if "?" in raw_url else f"{raw_url}?tag={self.amazon_tag}"

    def convert_url_details(self, raw_url: str, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns both the public clean cloaked URL (shown to followers)
        and the underlying raw tracking URL (for publisher verification).
        """
        if not raw_url:
            return {"public_url": "", "raw_tracking_url": "", "is_cloaked": False}

        if "amazon." in raw_url:
            asin_match = re.search(r"/(?:dp|gp/product|d)/([A-Z0-9]{10})", raw_url)
            if asin_match:
                amz_url = f"https://www.amazon.in/dp/{asin_match.group(1)}?tag={self.amazon_tag}"
                return {"public_url": amz_url, "raw_tracking_url": amz_url, "is_cloaked": False}

        if self.earnkaro_id and not "amazon." in raw_url:
            clean_url = raw_url.split("?")[0]
            encoded = urllib.parse.quote(clean_url)
            raw_ek = f"https://earnkaro.com?r={self.earnkaro_id}&link={encoded}"
            cloaked = self.cloak_url(raw_ek)
            return {"public_url": cloaked, "raw_tracking_url": raw_ek, "is_cloaked": True}

        pub = self.convert_url(raw_url, platform)
        return {"public_url": pub, "raw_tracking_url": pub, "is_cloaked": False}

    def get_disclosure_text(self) -> str:
        return "#ad #affiliate #commissionsearned #dealsindia"
