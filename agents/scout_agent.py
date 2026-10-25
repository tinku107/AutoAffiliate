"""Product Scout Agent ('Scout').
Discovers live, real-time selling products from Amazon India & Flipkart dynamically.
Zero hardcoding: dynamically pulls High-ticket Mobiles/iPhones, Fashion, Toys, Festive Deals, etc.
"""

from typing import List, Dict, Any, Optional
from tools.scraper import ProductScraper
from tools.affiliate_tagger import AffiliateTagger
from core.db import save_product, log_agent_action


class ScoutAgent:
    def __init__(self, amazon_tag: str = "autoaffil-21", earnkaro_id: Optional[str] = None):
        self.name = "Scout (Product Hunter)"
        self.scraper = ProductScraper()
        self.tagger = AffiliateTagger(amazon_tag=amazon_tag, earnkaro_id=earnkaro_id)

    def scout_trending_products(
        self,
        category: str = "all",
        query: Optional[str] = None,
        platform: str = "auto",
        count: int = 5,
        target_profit: float = 500.0
    ) -> List[Dict[str, Any]]:
        """
        Dynamically scouts real live products from Amazon India & Flipkart.
        Can scout by platform ('auto', 'amazon', 'flipkart'), category, or search query.
        """
        log_agent_action(self.name, f"Live scouting [{platform.upper()}] for: {query or category}", "started")

        raw_items = self.scraper.scrape_unified_deals(
            platform=platform,
            category=category,
            query=query,
            limit=count
        )

        processed_products = []
        for item in raw_items:
            # Dynamic Affiliate Tagging (Cloaked: Never show EarnKaro directly to followers)
            url_meta = self.tagger.convert_url_details(item["source_url"], platform=item.get("platform", "Amazon"))
            item["affiliate_url"] = url_meta["public_url"]
            item["raw_affiliate_url"] = url_meta["raw_tracking_url"]
            item["is_cloaked"] = url_meta["is_cloaked"]
            item["status"] = "scouted"

            # Dynamic Commission Calculation
            price = item.get("deal_price", 0.0)
            comm_rate = item.get("commission_rate", 0.05)
            est_comm_per_sale = round(price * comm_rate, 2)
            item["est_comm_per_sale"] = est_comm_per_sale

            # Dynamic units to goal based on user's target profit
            units_to_goal = max(1, int(target_profit / max(1.0, est_comm_per_sale)))
            item["units_to_goal"] = units_to_goal

            # Save to Database
            pid = save_product(item)
            item["id"] = pid
            processed_products.append(item)

        log_agent_action(
            self.name,
            f"Successfully found {len(processed_products)} live products for {query or category}",
            "completed",
            details=f"Top: {processed_products[0]['title'][:40] if processed_products else 'None'}"
        )
        return processed_products

    def import_product_from_url(self, raw_url: str, target_profit: float = 500.0) -> Optional[Dict[str, Any]]:
        """Extracts and auto-tags any live Amazon or Flipkart URL provided by the user."""
        log_agent_action(self.name, f"Live scraping URL: {raw_url[:40]}...", "started")
        item = self.scraper.fetch_product_by_url(raw_url)
        if not item:
            log_agent_action(self.name, "Failed to scrape product from URL", "failed")
            return None

        url_meta = self.tagger.convert_url_details(item["source_url"], platform=item["platform"])
        item["affiliate_url"] = url_meta["public_url"]
        item["raw_affiliate_url"] = url_meta["raw_tracking_url"]
        item["is_cloaked"] = url_meta["is_cloaked"]
        comm_rate = item.get("commission_rate", 0.05)
        item["est_comm_per_sale"] = round(item["deal_price"] * comm_rate, 2)
        item["units_to_goal"] = max(1, int(target_profit / max(1.0, item["est_comm_per_sale"])))

        pid = save_product(item)
        item["id"] = pid
        log_agent_action(self.name, f"Imported: {item['title'][:40]}", "completed")
        return item
