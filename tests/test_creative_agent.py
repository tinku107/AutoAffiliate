import unittest
from agents.creative_agent import clean_humanoid_text, CreativeAgent


class TestCreativeAgent(unittest.TestCase):
    def test_clean_humanoid_text_removes_emojis(self):
        dirty = "🔥 MEGA SALE!! 💥 Grab this awesome saree 👗 now!! 🚀 Link in bio 💯"
        cleaned = clean_humanoid_text(dirty)
        self.assertNotIn("🔥", cleaned)
        self.assertNotIn("💥", cleaned)
        self.assertNotIn("👗", cleaned)
        self.assertNotIn("🚀", cleaned)
        self.assertNotIn("💯", cleaned)
        self.assertIn("Grab this awesome saree now", cleaned)

    def test_caption_includes_ad_and_affiliate(self):
        agent = CreativeAgent()
        product = {
            "id": 99,
            "title": "Kanjivaram Silk Saree",
            "category": "saree",
            "deal_price": 999,
            "original_price": 2999,
            "discount_pct": 66,
            "image_url": "https://m.media-amazon.com/test.jpg"
        }
        post = agent.generate_content_for_product(product, channel_profile={"name": "Elena's World"})
        self.assertIn("#ad", post["hashtags"])
        self.assertIn("#affiliate", post["hashtags"])
        self.assertIn("Disclosure: This post contains affiliate links", post["caption"])

    def test_clean_humanoid_text_removes_fancy_unicode(self):
        fancy = "𝙏𝙝𝙞𝙨 𝙞𝙨 𝕓𝕠𝕝𝕕 𝒂𝒏𝒅 𝑖𝑡𝑎𝑙𝑖𝑐"
        cleaned = clean_humanoid_text(fancy)
        self.assertEqual(cleaned, "This is bold and italic")


if __name__ == "__main__":
    unittest.main()
