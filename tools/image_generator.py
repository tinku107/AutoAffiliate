"""High-converting Instagram & Facebook Graphic Asset Generator.
Creates multi-image carousels grabbing all angles/pictures from Amazon & Flipkart.
Zero AI/bot mentions: clean, professional, human-curator aesthetic.
"""

import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional

GENERATED_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated_images")


class ImageGenerator:
    def __init__(self):
        os.makedirs(GENERATED_IMG_DIR, exist_ok=True)

    def _get_font(self, size: int, bold: bool = False):
        candidate_paths = [
            # Windows font paths
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf" if bold else "arial.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "seguisb.ttf" if bold else "segoeui.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "tahoma.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "calibri.ttf"),
            # Linux font paths (Streamlit Cloud / Debian / Ubuntu)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
        for font_path in candidate_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()

    def _draw_base_slide(self, width: int = 1080, height: int = 1080) -> (Image.Image, ImageDraw.ImageDraw):
        """Creates standard dark charcoal gradient canvas."""
        img = Image.new("RGB", (width, height), color=(15, 18, 26))
        draw = ImageDraw.Draw(img)
        for y in range(height):
            ratio = y / height
            r = int(15 + ratio * 15)
            g = int(18 + ratio * 10)
            b = int(26 + ratio * 20)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        return img, draw

    def generate_carousel_slides(self, product: Dict[str, Any], max_slides: int = 4) -> List[str]:
        """
        Grabs multiple pictures extracted from Amazon/Flipkart and generates
        a complete 4-slide Instagram/Facebook carousel showcasing every angle!
        """
        pid = product.get("product_id", "prod")
        image_urls = product.get("image_urls", [])
        if not image_urls and product.get("image_url"):
            image_urls = [product.get("image_url")]

        generated_paths = []
        num_slides = min(max_slides, max(1, len(image_urls)))

        for slide_idx in range(num_slides):
            img_url = image_urls[slide_idx % len(image_urls)]
            slide_path = self.generate_single_slide(product, img_url=img_url, slide_idx=slide_idx, total_slides=num_slides)
            generated_paths.append(slide_path)

        return generated_paths

    def generate_single_slide(self, product: Dict[str, Any], img_url: str, slide_idx: int = 0, total_slides: int = 1) -> str:
        """Renders an individual carousel slide."""
        width, height = (1080, 1080)
        img, draw = self._draw_base_slide(width, height)

        title = product.get("title", "Curated Viral Find")
        short_title = title.split("(")[0].split("-")[0].strip()[:42]
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        discount = int(product.get("discount_pct", 0))
        rating = product.get("rating", 4.5)
        reviews = product.get("reviews_count", 1500)
        pid = product.get("product_id", "prod")

        # Slide Headers based on index
        if slide_idx == 0:
            header_text = "CURATED FIND OF THE DAY"
            badge_text = f"FLAT {discount}% OFF" if discount > 0 else "TOP RATED PICK"
            footer_text = "SWIPE TO SEE ALL ANGLES 👉" if total_slides > 1 else "LINK IN BIO & STORIES"
            sub_footer = "Comment 'LINK' and I'll DM you the direct discount link!"
        elif slide_idx == 1:
            header_text = "ANGLE & DETAIL VIEW"
            badge_text = "VERIFIED QUALITY"
            footer_text = "SWIPE FOR MORE 👉"
            sub_footer = "Comment 'LINK' for the verified purchase link!"
        elif slide_idx == 2:
            header_text = "IN-HAND & LIFESTYLE LOOK"
            badge_text = "TOP RATED"
            footer_text = "SWIPE TO CLAIM OFFER 👉"
            sub_footer = "Claim this exclusive price before deal ends!"
        else:
            header_text = "LIMITED TIME OFFER"
            badge_text = "CLAIM DISCOUNT"
            footer_text = "LINK IN BIO & STORIES"
            sub_footer = "Comment 'LINK' below and I'll send it directly to your DM!"

        # 1. Top Header Bar
        header_bg_height = 120
        draw.rectangle([(0, 0), (width, header_bg_height)], fill=(245, 158, 11))
        title_font = self._get_font(42, bold=True)
        draw.text((width // 2, 60), header_text, fill=(10, 10, 15), anchor="mm", font=title_font)

        # 2. Product Photo Card
        card_w, card_h = 760, 520
        card_x = (width - card_w) // 2
        card_y = 160

        draw.rounded_rectangle([(card_x - 4, card_y - 4), (card_x + card_w + 4, card_y + card_h + 4)], radius=24, fill=(35, 42, 58))
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=20, fill=(255, 255, 255))

        # Download & paste product image
        if img_url:
            try:
                resp = requests.get(img_url, timeout=5)
                if resp.status_code == 200:
                    prod_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    prod_img.thumbnail((card_w - 40, card_h - 40), Image.Resampling.LANCZOS)
                    px = card_x + (card_w - prod_img.width) // 2
                    py = card_y + (card_h - prod_img.height) // 2
                    img.paste(prod_img, (px, py))
            except Exception:
                pass

        # 3. Badge
        badge_w, badge_h = 290, 62
        badge_x = card_x - 15
        badge_y = card_y + 15
        draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=16, fill=(239, 68, 68))
        badge_font = self._get_font(28, bold=True)
        draw.text((badge_x + badge_w // 2, badge_y + badge_h // 2), badge_text, fill=(255, 255, 255), anchor="mm", font=badge_font)

        # 4. Slide Indicator Dots (e.g. 1 / 4)
        if total_slides > 1:
            page_text = f"{slide_idx + 1} / {total_slides}"
            page_font = self._get_font(24, bold=True)
            draw.text((card_x + card_w - 40, card_y + 35), page_text, fill=(100, 116, 139), anchor="mm", font=page_font)

        # 5. Product Title
        cur_y = card_y + card_h + 35
        prod_title_font = self._get_font(36, bold=True)
        draw.text((width // 2, cur_y), short_title, fill=(255, 255, 255), anchor="mm", font=prod_title_font)

        # 6. Ratings
        cur_y += 50
        rating_text = f"Rating: {rating} / 5.0  •  {reviews:,}+ Verified Orders"
        rating_font = self._get_font(26, bold=False)
        draw.text((width // 2, cur_y), rating_text, fill=(251, 191, 36), anchor="mm", font=rating_font)

        # 7. Price Block
        cur_y += 65
        price_font = self._get_font(48, bold=True)
        mrp_font = self._get_font(30, bold=False)
        price_str = f"Deal: ₹{deal_price:,}"
        mrp_str = f"MRP: ₹{orig_price:,}" if orig_price > deal_price else ""

        if mrp_str:
            draw.text((width // 2 - 140, cur_y), price_str, fill=(16, 185, 129), anchor="mm", font=price_font)
            mrp_x = width // 2 + 150
            draw.text((mrp_x, cur_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
            draw.line([(mrp_x - 90, cur_y), (mrp_x + 90, cur_y)], fill=(239, 68, 68), width=3)
        else:
            draw.text((width // 2, cur_y), price_str, fill=(16, 185, 129), anchor="mm", font=price_font)

        # 8. Human-Centric Footer (Zero AI mention)
        footer_y = height - 120
        draw.rectangle([(0, footer_y), (width, height)], fill=(30, 41, 59))
        cta_font = self._get_font(28, bold=True)
        draw.text((width // 2, footer_y + 40), footer_text, fill=(255, 255, 255), anchor="mm", font=cta_font)
        sub_cta_font = self._get_font(22, bold=False)
        draw.text((width // 2, footer_y + 80), sub_footer, fill=(245, 158, 11), anchor="mm", font=sub_cta_font)

        filename = f"post_{pid}_slide_{slide_idx + 1}.jpg"
        filepath = os.path.join(GENERATED_IMG_DIR, filename)
        img.save(filepath, "JPEG", quality=92)
        return filepath

    def generate_product_banner(self, product: Dict[str, Any], banner_type: str = "square") -> str:
        """Generates single slide (main hero banner)."""
        img_url = product.get("image_url", "")
        return self.generate_single_slide(product, img_url=img_url, slide_idx=0, total_slides=1)
