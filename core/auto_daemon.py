"""AutoAffiliate AI - 24/7 Fully Autonomous Agentic Daemon.
Runs in the background with strict anti-bot humanization:
1. NO fixed schedule (no 12:30 or static intervals): Uses dynamic randomized jitter
2. Independent channel execution:
   - Ladies Fashion posts exclusively to Ladies Fashion FB & Insta
   - Electronics posts exclusively to Electronics FB & Insta
   - Any custom added niche posts exclusively to its connected accounts
3. Daily organic audience growth:
   - Discovers new people in each niche daily
   - Likes their posts, leaves authentic humanoid comments (zero icons, zero spam)
   - Invites high-intent prospects to follow the page & join group
4. Anti-spam safety jitter: Variable pacing between actions to prevent flagging.
"""

import time
import os
import sys
import random
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Ensure project root in sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.orchestrator import AgentOrchestrator
from core.db import log_agent_action, get_posts


class AutonomousAgentDaemon:
    def __init__(
        self,
        min_interval_minutes: int = 90,
        max_interval_minutes: int = 210,
        orchestrator: Optional[Any] = None
    ):
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.min_interval_minutes = min_interval_minutes
        self.max_interval_minutes = max_interval_minutes
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self.cycle_count = 0
        self.active_channel_names: List[str] = []

    def _get_next_dynamic_interval_seconds(self) -> int:
        """
        Calculates a dynamic, non-fixed interval with randomized jitter.
        Prevents static schedules (e.g. not 12:30 or fixed 3h) to avoid spam/bot detection.
        """
        mins = random.randint(self.min_interval_minutes, self.max_interval_minutes)
        jitter_secs = random.randint(-600, 600)  # +/- 10 minutes jitter
        total_secs = max(1800, (mins * 60) + jitter_secs)
        return total_secs

    def run_one_autonomous_cycle(self) -> Dict[str, Any]:
        """
        Executes one full autonomous cycle across all enabled channels independently:
        - Ladies Fashion -> Posts to Ladies FB & Insta + Niche growth
        - Electronics -> Posts to Electronics FB & Insta + Tech growth
        - Any custom niche -> Posts to its configured accounts + Custom growth
        """
        enabled_profiles = self.orchestrator.get_enabled_autopilot_profiles()
        if not enabled_profiles:
            log_agent_action("AutoDaemon", "No channels currently enabled for Autopilot. Pausing cycle.", "warning")
            # Routine Janitor Run: Automatically purge published media files older than 24 hours
            try:
                purge_res = self.orchestrator.cleaner.clean_expired_published_media()
                if isinstance(purge_res, dict) and int(purge_res.get("files_deleted", 0) or 0) > 0:
                    log_agent_action("AutoDaemon", f"Janitor Purge: Reclaimed {purge_res.get('freed_mb', 0)} MB from published media >24h.", "completed")
            except Exception as e:
                print(f"Janitor daemon cleanup note: {e}")
            return {"success": False, "reason": "No channels enabled"}

        self.cycle_count += 1
        self.last_run_time = datetime.now()
        self.active_channel_names = [p.get("name", "Channel") for p in enabled_profiles]

        log_agent_action(
            "AutoDaemon",
            f"Autonomous Cycle #{self.cycle_count} Started for {len(enabled_profiles)} active channel(s): {', '.join(self.active_channel_names)}",
            "started"
        )

        cycle_results = []

        for idx, profile in enumerate(enabled_profiles):
            prof_name = profile.get("name", "Channel")
            target_niche = profile.get("focus_niche", "all")

            try:
                # Anti-bot human pacing between multiple accounts
                if idx > 0:
                    inter_account_delay = random.randint(35, 80)
                    log_agent_action("AutoDaemon", f"Anti-spam human jitter: Waiting {inter_account_delay}s before starting next account...", "started")
                    time.sleep(inter_account_delay)

                # 1. Scout 1 top live product matching this specific channel's niche
                products = self.orchestrator.scout.scout_trending_products(
                    category=target_niche,
                    count=1,
                    target_profit=self.orchestrator.daily_target_inr
                )
                if not products:
                    products = self.orchestrator.scout.scout_trending_products(
                        category="all",
                        count=1,
                        target_profit=self.orchestrator.daily_target_inr
                    )

                if not products:
                    continue

                target_product = products[0]

                # 2. Generate 100% humanoid copy (zero emojis, zero icons, zero special characters)
                post = self.orchestrator.creative.generate_content_for_product(
                    target_product,
                    channel_niche=target_niche
                )
                post["target_channel"] = profile.get("id")

                # Simulated human review delay
                time.sleep(random.randint(5, 15))

                # 3. Publish to this specific channel's Facebook & Instagram accounts
                publish_res = self.orchestrator.marketer.publish_approved_post(
                    post,
                    channel_profile=profile
                )

                # Simulated human browsing delay
                time.sleep(random.randint(10, 25))

                # 4. Organic Audience Growth: Find new people, like posts, humanoid comments, invite to page/group
                growth_res = self.orchestrator.marketer.grow_audience_and_engage(
                    niche=target_niche,
                    channel_profile=profile,
                    count=2
                )

                result_summary = {
                    "channel": prof_name,
                    "niche": target_niche,
                    "product": target_product.get("title", "")[:35],
                    "post_id": post.get("id"),
                    "published": publish_res.get("success", False),
                    "growth_actions": len(growth_res)
                }
                cycle_results.append(result_summary)

                log_agent_action(
                    "AutoDaemon",
                    f"Completed independent cycle for [{prof_name}]: Published #{post.get('id')} to Meta & ran {len(growth_res)} organic growth tasks.",
                    "completed"
                )

            except Exception as e:
                log_agent_action("AutoDaemon", f"Error processing [{prof_name}]: {str(e)}", "failed")

        # Post-cycle maintenance: Purge published media older than retention threshold
        try:
            purge_res = self.orchestrator.cleaner.clean_expired_published_media()
            if isinstance(purge_res, dict) and int(purge_res.get("files_deleted", 0) or 0) > 0:
                log_agent_action("AutoDaemon", f"Janitor Purge: Reclaimed {purge_res.get('freed_mb', 0)} MB from published media >24h.", "completed")
        except Exception as e:
            print(f"Janitor daemon cleanup note: {e}")

        return {
            "success": True,
            "cycle": self.cycle_count,
            "channels_processed": len(cycle_results),
            "details": cycle_results
        }

    def start_background_loop(self):
        """Starts the daemon loop in a background thread with dynamic non-fixed timing."""
        if self.is_running:
            return

        self.is_running = True

        def _loop():
            # Run first cycle immediately
            self.run_one_autonomous_cycle()

            while self.is_running:
                # Dynamic next run interval with jitter (no fixed clock)
                sleep_seconds = self._get_next_dynamic_interval_seconds()
                self.next_run_time = datetime.now() + timedelta(seconds=sleep_seconds)
                log_agent_action(
                    "AutoDaemon",
                    f"Dynamic schedule: Next run dynamically scheduled in ~{sleep_seconds // 60} mins at {self.next_run_time.strftime('%I:%M %p')} (Anti-spam jitter applied)",
                    "completed"
                )

                # Sleep in 1-second ticks for instant cancellation
                for _ in range(sleep_seconds):
                    if not self.is_running:
                        break
                    time.sleep(1)

                if self.is_running:
                    self.run_one_autonomous_cycle()

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        log_agent_action("AutoDaemon", "Dynamic Autonomous Daemon Started (No fixed clock, independent channels)", "started")

    def stop_background_loop(self):
        """Stops the autonomous daemon."""
        self.is_running = False
        self._thread = None
        log_agent_action("AutoDaemon", "Autonomous Daemon Paused by User", "stopped")


# Global daemon instance for UI sharing
_daemon_instance: Optional[AutonomousAgentDaemon] = None


def get_auto_daemon(min_interval_minutes: int = 90, max_interval_minutes: int = 210) -> AutonomousAgentDaemon:
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = AutonomousAgentDaemon(
            min_interval_minutes=min_interval_minutes,
            max_interval_minutes=max_interval_minutes
        )
    return _daemon_instance


if __name__ == "__main__":
    print("=====================================================")
    print(" AutoAffiliate AI - 24/7 Autonomous Agentic Daemon   ")
    print(" Dynamic Timing + Independent Multi-Channel Engine   ")
    print("=====================================================")
    daemon = get_auto_daemon()
    print("Starting continuous autonomous daemon. Press Ctrl+C to stop.")
    daemon.start_background_loop()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping daemon...")
        daemon.stop_background_loop()
        print("Daemon stopped gracefully.")

