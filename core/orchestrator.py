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

    def test_next_product(self, category: str = "all", query: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes an instant end-to-end test:
        1. Dynamically finds the next live selling product
        2. Generates complete copy, reel script, hashtags, and visual banner
        3. Returns the full asset package for immediate user inspection
        """
        log_agent_action("Orchestrator", f"Testing next product in: {query or category}", "started")

        products = self.scout.scout_trending_products(
            category=category,
            query=query,
            count=1,
            target_profit=self.daily_target_inr
        )
        if not products:
            return {"success": False, "error": "No live product could be retrieved from search"}

        target_prod = products[0]
        post = self.creative.generate_content_for_product(target_prod)

        log_agent_action("Orchestrator", f"Test product package ready: {target_prod['title'][:35]}", "completed")
        return {
            "success": True,
            "product": target_prod,
            "post": post
        }

    def run_full_daily_autonomous_cycle(self, category: str = "all") -> Dict[str, Any]:
        """
        Executes the complete autonomous daily cycle:
        1. Scout 3 trending viral deals dynamically
        2. Generate complete posts (captions, reel scripts, image graphics)
        3. Publish the top-rated post to Instagram & Facebook
        4. Run humanized target audience engagement
        5. Update progress towards target INR X
        """
        log_agent_action("Orchestrator", f"Initiating Full Autonomous Daily Cycle ({category})", "started")

        products = self.scout.scout_trending_products(category=category, count=3, target_profit=self.daily_target_inr)

        created_posts = []
        for prod in products:
            post = self.creative.generate_content_for_product(prod)
            created_posts.append(post)

        publish_result = {}
        if created_posts:
            publish_result = self.marketer.publish_approved_post(created_posts[0])

        engagement = self.marketer.scout_and_engage_with_target_audience(niche="deals", count=3)

        log_agent_action("Orchestrator", "Full Autonomous Daily Cycle Completed", "completed")

        return {
            "scouted_count": len(products),
            "created_posts_count": len(created_posts),
            "published_post": publish_result,
            "engagement_actions": len(engagement),
            "summary": f"Autonomous cycle finished: Discovered {len(products)} deals, generated {len(created_posts)} posts, published Top Deal #{created_posts[0]['id'] if created_posts else 'N/A'}, and completed {len(engagement)} organic interactions."
        }

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
