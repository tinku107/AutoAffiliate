import unittest
from unittest.mock import MagicMock, patch
from core.auto_daemon import AutonomousAgentDaemon


class TestAutoDaemon(unittest.TestCase):
    def test_daemon_returns_no_channels_when_empty(self):
        mock_orch = MagicMock()
        mock_orch.get_enabled_autopilot_profiles.return_value = []
        daemon = AutonomousAgentDaemon(orchestrator=mock_orch)

        result = daemon.run_one_autonomous_cycle()
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "No channels enabled")

    @patch("time.sleep", return_value=None)
    def test_daemon_executes_cycle_when_channels_enabled(self, mock_sleep):
        mock_orch = MagicMock()
        mock_profile = {
            "id": "fashion",
            "name": "StyleDrop India",
            "focus_niche": "fashion",
            "enabled_for_autopilot": True
        }
        mock_orch.get_enabled_autopilot_profiles.return_value = [mock_profile]
        mock_orch.cleaner.clean_expired_published_media.return_value = {"files_deleted": 0, "freed_mb": 0.0}

        # Mock product, post, and publish flow
        mock_product = {
            "id": 1,
            "title": "Banarasi Soft Silk Saree",
            "deal_price": 799,
            "original_price": 2499,
            "discount_pct": 68,
            "image_url": "https://m.media-amazon.com/images/I/sample.jpg"
        }
        mock_orch.scout.scout_trending_products.return_value = [mock_product]
        mock_orch.creative.generate_content_for_product.return_value = {
            "id": 101,
            "headline": "Featured Find",
            "caption": "Clean caption",
            "hashtags": "#ad #affiliate",
            "media_paths": []
        }
        mock_orch.marketer.publish_approved_post.return_value = {"success": True, "post_id": 101}
        mock_orch.marketer.grow_audience_and_engage.return_value = []

        daemon = AutonomousAgentDaemon(orchestrator=mock_orch)
        result = daemon.run_one_autonomous_cycle()

        self.assertTrue(result["success"], "Autonomous cycle must execute when channels are enabled")
        self.assertEqual(result["channels_processed"], 1)

    def test_dynamic_interval_generation(self):
        mock_orch = MagicMock()
        daemon = AutonomousAgentDaemon(orchestrator=mock_orch, min_interval_minutes=30, max_interval_minutes=60)
        secs = daemon._get_next_dynamic_interval_seconds()
        self.assertGreaterEqual(secs, 30 * 60)
        self.assertLessEqual(secs, 60 * 60 + 600)


if __name__ == "__main__":
    unittest.main()
