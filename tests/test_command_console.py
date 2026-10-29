import unittest
import os
from core.orchestrator import AgentOrchestrator


class TestCommandConsole(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AgentOrchestrator()

    def test_greetings_does_not_return_repetitive_fallback_menu(self):
        res = self.orchestrator.process_chat_command("hi")
        self.assertIn("response", res)
        self.assertNotIn("AutoAffiliate AI Team Active! • Test next product", res["response"])

    def test_env_question_returns_helpful_instructions(self):
        res = self.orchestrator.process_chat_command("can you update environment values")
        self.assertIn("response", res)
        # Should explain updating via chat or settings
        resp_lower = res["response"].lower()
        self.assertTrue("update env" in resp_lower or "settings" in resp_lower or ".env" in resp_lower)
        self.assertNotIn("AutoAffiliate AI Team Active! • Test next product", res["response"])

    def test_show_env_returns_sanitized_summary(self):
        res = self.orchestrator.process_chat_command("show env")
        self.assertIn("response", res)
        self.assertIn("AMAZON_ASSOCIATE_TAG", res["response"])
        self.assertIn("tinkukrishnan-21", res["response"])

    def test_direct_env_update(self):
        res = self.orchestrator.process_chat_command("update env TEST_DUMMY_VAR = hello123")
        self.assertIn("response", res)
        self.assertIn("TEST_DUMMY_VAR", res["response"])
        self.assertEqual(os.environ.get("TEST_DUMMY_VAR"), "hello123")


if __name__ == "__main__":
    unittest.main()
