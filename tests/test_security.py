import unittest
import os
import yaml
from core.orchestrator import load_settings, save_settings_safely, CONFIG_PATH


class TestSecurity(unittest.TestCase):
    def test_settings_yaml_contains_no_raw_tokens(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        for profile in cfg.get("channel_profiles", []):
            token = profile.get("meta_access_token", "")
            user_token = profile.get("meta_user_token", "")
            self.assertEqual(token, "", f"Live token leaked in settings.yaml for {profile.get('name')}")
            self.assertEqual(user_token, "", f"Live user token leaked in settings.yaml for {profile.get('name')}")

    def test_gitignore_ignores_env_files(self):
        gitignore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".gitignore")
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(".env", content)
        self.assertIn(".streamlit/secrets.toml", content)

    def test_save_settings_safely_sanitizes_tokens(self):
        mock_cfg = {
            "channel_profiles": [
                {
                    "id": "test_profile",
                    "meta_access_token": "EAA_SECRET_TEST_TOKEN",
                    "meta_user_token": "EAA_SECRET_USER_TOKEN"
                }
            ],
            "ai": {
                "gemini_api_key": "AIzaSy_SECRET_KEY"
            }
        }
        test_path = os.path.join(os.path.dirname(__file__), "test_temp_settings.yaml")
        try:
            save_settings_safely(mock_cfg, path=test_path)
            with open(test_path, "r", encoding="utf-8") as f:
                saved = yaml.safe_load(f)

            self.assertEqual(saved["channel_profiles"][0]["meta_access_token"], "")
            self.assertEqual(saved["channel_profiles"][0]["meta_user_token"], "")
            self.assertEqual(saved["ai"]["gemini_api_key"], "")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)


if __name__ == "__main__":
    unittest.main()
