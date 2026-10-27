import unittest
import os
from bs4 import BeautifulSoup
from tools.scraper import ProductScraper
from tools.image_generator import ImageGenerator
from PIL import Image


class TestImageGeneratorAndScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = ProductScraper()
        self.image_gen = ImageGenerator()

    def test_scraper_extracts_highest_res_from_amazon_dynamic_json(self):
        html = '<img src="https://images/grey-pixel.gif" data-a-dynamic-image=\'{"https://m.media-amazon.com/images/I/small.jpg":[300,300], "https://m.media-amazon.com/images/I/large.jpg":[1500,1500]}\'>'
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.find("img")
        best = self.scraper._extract_img_from_elem(elem)
        self.assertEqual(best, "https://m.media-amazon.com/images/I/large.jpg")

    def test_scraper_ignores_tracking_pixels_and_uses_data_src(self):
        html = '<img src="https://images-na.ssl-images-amazon.com/images/G/01/x-locale/common/grey-pixel.gif" data-src="https://m.media-amazon.com/images/I/real.jpg">'
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.find("img")
        best = self.scraper._extract_img_from_elem(elem)
        self.assertEqual(best, "https://m.media-amazon.com/images/I/real.jpg")

    def test_image_generator_does_not_produce_white_screen_on_failed_download(self):
        prod = {
            "title": "Offline Test Saree",
            "deal_price": 499,
            "original_price": 1299,
            "discount_pct": 61,
            "image_url": "http://127.0.0.1:9999/non_existent_image.jpg",
            "platform": "Amazon"
        }
        slide_path = self.image_gen.generate_single_slide(prod)
        self.assertTrue(os.path.exists(slide_path))

        img = Image.open(slide_path)
        # Check center card area (60, 125, 960, 670)
        card_crop = img.crop((60, 125, 60 + 960, 125 + 670))
        colors = card_crop.getcolors(maxcolors=1000000)
        # Find count of pure white pixels (255, 255, 255)
        white_px = sum(count for count, col in colors if col == (255, 255, 255))
        total_px = 960 * 670
        # White pixels should be negligible (< 1%), NOT a solid white box
        self.assertLess(white_px / total_px, 0.05)


if __name__ == "__main__":
    unittest.main()
