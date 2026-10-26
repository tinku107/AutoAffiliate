import unittest
from tools.affiliate_tagger import AffiliateTagger, PLACEHOLDER_IDS


class TestAffiliateTagger(unittest.TestCase):
    def setUp(self):
        self.tagger = AffiliateTagger(amazon_tag="tinkukrishnan-21", earnkaro_id="5736594")

    def test_amazon_canonical_tagging(self):
        raw = "https://www.amazon.in/dp/B0DFX4PGB9"
        tagged = self.tagger.convert_url(raw)
        self.assertEqual(tagged, "https://www.amazon.in/dp/B0DFX4PGB9?tag=tinkukrishnan-21")

    def test_amazon_short_link_preserved(self):
        raw = "https://amzn.to/4inmR5V"
        tagged = self.tagger.convert_url(raw)
        self.assertEqual(tagged, raw, "Official amzn.to short links must be preserved exactly as generated")

    def test_non_amazon_fallback_does_not_append_amazon_tag(self):
        # Create tagger without EarnKaro to test direct fallback behavior
        pure_tagger = AffiliateTagger(amazon_tag="tinkukrishnan-21", earnkaro_id="")
        raw = "https://somestore.in/product/12345"
        converted = pure_tagger.convert_url(raw)
        self.assertNotIn("tag=tinkukrishnan-21", converted, "Non-Amazon stores must NEVER be tagged with Amazon Associate tags")
        self.assertEqual(converted, raw)

    def test_earnkaro_routing_for_non_amazon_stores(self):
        raw = "https://www.flipkart.com/ethnic-saree/p/itm123456?pid=SAR123"
        converted = self.tagger.convert_url(raw)
        self.assertTrue(converted.startswith("https://earnkaro.com?r=5736594&link="))
        self.assertIn("flipkart.com", converted)

    def test_placeholder_ids_detected(self):
        self.assertIn("flipkart_aff", PLACEHOLDER_IDS)
        self.assertIn("affiliate", PLACEHOLDER_IDS)

    def test_convert_url_details(self):
        details = self.tagger.convert_url_details("https://amzn.to/4inmR5V")
        self.assertEqual(details["link_type"], "amzn_to")
        self.assertEqual(details["public_url"], "https://amzn.to/4inmR5V")

    def test_disclosure_text_contains_ad_and_affiliate(self):
        disc = self.tagger.get_disclosure_text()
        self.assertIn("#ad", disc)
        self.assertIn("#affiliate", disc)


if __name__ == "__main__":
    unittest.main()
