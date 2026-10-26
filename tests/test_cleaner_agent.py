import unittest
from agents.cleaner_agent import CleanerAgent


class TestCleanerAgent(unittest.TestCase):
    def test_cleaner_retention_defaults(self):
        cleaner = CleanerAgent()
        self.assertGreaterEqual(cleaner.default_retention_hours, 1)

    def test_clean_expired_published_media_runs_safely(self):
        cleaner = CleanerAgent()
        res = cleaner.clean_expired_published_media()
        self.assertIn("files_deleted", res)
        self.assertIn("freed_mb", res)


if __name__ == "__main__":
    unittest.main()
