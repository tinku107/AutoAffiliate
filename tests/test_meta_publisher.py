import unittest
from tools.meta_api import MetaPublisher


class TestMetaPublisher(unittest.TestCase):
    def test_simulation_mode_when_unconfigured(self):
        pub = MetaPublisher(access_token="", ig_user_id="", fb_page_id="")
        self.assertFalse(pub.is_configured())

        res_ig = pub.publish_instagram_photo("https://m.media-amazon.com/sample.jpg", "caption")
        self.assertTrue(res_ig["success"])
        self.assertEqual(res_ig["mode"], "simulation")

        res_fb = pub.publish_facebook_post("caption", "https://amzn.to/sample")
        self.assertTrue(res_fb["success"])
        self.assertEqual(res_fb["mode"], "simulation")

    def test_instagram_rejects_local_file_path_for_live_post(self):
        # Even with credentials, passing a local Windows path should return an informative error
        pub = MetaPublisher(access_token="TEST_TOKEN", ig_user_id="178414000000000", fb_page_id="1484650751391885")
        res = pub.publish_instagram_photo(r"C:\AI\data\test_image.jpg", "caption")
        self.assertFalse(res["success"])
        self.assertIn("requires a publicly accessible HTTPS image URL", res["error"])

    def test_telegram_simulation_when_unconfigured(self):
        pub = MetaPublisher()
        res = pub.broadcast_telegram_deal(None, "Deal text")
        self.assertTrue(res["success"])
        self.assertEqual(res["mode"], "simulation")


if __name__ == "__main__":
    unittest.main()
