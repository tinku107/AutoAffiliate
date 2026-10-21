"""AutoAffiliate AI - 24/7 Fully Autonomous Agentic Daemon.
Runs in the background without ANY human intervention:
1. Scouts live trending products (Mobiles, Fashion, Gadgets, Toys, Kitchen)
2. Automatically generates 1080x1080 graphics, captions, hashtags, and Reel scripts
3. Automatically publishes to Instagram, Facebook & Telegram
4. Executes safe human-like organic engagement
5. Tracks earnings & progress towards target profit X
"""

import time
import os
import sys
import threading
from datetime import datetime
from typing import Optional

# Ensure project root in sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.orchestrator import AgentOrchestrator
from core.db import log_agent_action, get_posts


class AutonomousAgentDaemon:
    def __init__(self, interval_hours: float = 3.0):
        self.orchestrator = AgentOrchestrator()
        self.interval_seconds = int(interval_hours * 3600)
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self.cycle_count = 0

        # Category rotation for varied social feeds
        self.categories = ["mobiles", "fashion", "electronics", "toys", "kitchen", "beauty"]
        self.current_cat_idx = 0

    def run_one_autonomous_cycle(self) -> dict:
        """Executes one hands-free cycle: Find -> Create -> Publish -> Engage."""
        category = self.categories[self.current_cat_idx % len(self.categories)]
        self.current_cat_idx += 1
        self.cycle_count += 1
        self.last_run_time = datetime.now()

        log_agent_action(
            "AutoDaemon",
            f"Autonomous Cycle #{self.cycle_count} Started for Category: '{category.upper()}'",
            "started"
        )

        try:
            # 1. Scout 1 top live product in the current rotated category
            products = self.orchestrator.scout.scout_trending_products(
                category=category,
                count=1,
                target_profit=self.orchestrator.daily_target_inr
            )
            if not products:
                # Fallback to general bestsellers
                products = self.orchestrator.scout.scout_trending_products(
                    category="all",
                    count=1,
                    target_profit=self.orchestrator.daily_target_inr
                )

            if not products:
                log_agent_action("AutoDaemon", "No live products discovered in this cycle", "warning")
                return {"success": False, "reason": "No products"}

            target_product = products[0]

            # 2. Automatically generate high-converting post and Pillow 1080x1080 banner
            post = self.orchestrator.creative.generate_content_for_product(target_product)

            # 3. Automatically publish immediately (No human approval needed)
            publish_res = self.orchestrator.marketer.publish_approved_post(post)

            # 4. Automatically run safe audience engagement
            engagement_res = self.orchestrator.marketer.scout_and_engage_with_target_audience(
                niche=category,
                count=2
            )

            summary = (
                f"Autonomous Cycle #{self.cycle_count} Complete: "
                f"Discovered '{target_product['title'][:40]}', generated 1080x1080 banner, "
                f"auto-published Post #{post['id']} to Meta & Telegram, and completed {len(engagement_res)} organic engagements."
            )
            log_agent_action("AutoDaemon", summary, "completed")

            return {
                "success": True,
                "cycle": self.cycle_count,
                "product": target_product,
                "post": post,
                "publish": publish_res,
                "engagement": len(engagement_res)
            }

        except Exception as e:
            log_agent_action("AutoDaemon", f"Cycle #{self.cycle_count} encountered error: {str(e)}", "failed")
            return {"success": False, "error": str(e)}

    def start_background_loop(self):
        """Starts the daemon loop in a background thread."""
        if self.is_running:
            return

        self.is_running = True

        def _loop():
            # Run immediately on start
            self.run_one_autonomous_cycle()

            while self.is_running:
                self.next_run_time = datetime.fromtimestamp(time.time() + self.interval_seconds)
                # Sleep in short increments to allow instant graceful shutdown
                for _ in range(self.interval_seconds):
                    if not self.is_running:
                        break
                    time.sleep(1)

                if self.is_running:
                    self.run_one_autonomous_cycle()

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        log_agent_action("AutoDaemon", f"24/7 Autonomous Daemon Started (Interval: {self.interval_seconds // 3600} hours)", "started")

    def stop_background_loop(self):
        """Stops the autonomous daemon."""
        self.is_running = False
        self._thread = None
        log_agent_action("AutoDaemon", "Autonomous Daemon Paused by User", "stopped")


# Global daemon instance for UI sharing
_daemon_instance: Optional[AutonomousAgentDaemon] = None


def get_auto_daemon(interval_hours: float = 3.0) -> AutonomousAgentDaemon:
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = AutonomousAgentDaemon(interval_hours=interval_hours)
    return _daemon_instance


if __name__ == "__main__":
    print("=====================================================")
    print(" AutoAffiliate AI - 24/7 Autonomous Agentic Daemon   ")
    print(" Hands-free mode: Scrapes -> Generates -> Publishes  ")
    print("=====================================================")
    daemon = get_auto_daemon(interval_hours=2.0)
    print("Starting continuous autonomous daemon. Press Ctrl+C to stop.")
    daemon.start_background_loop()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping daemon...")
        daemon.stop_background_loop()
        print("Daemon stopped gracefully.")
