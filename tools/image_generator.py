"""High-converting Instagram & Facebook Graphic Asset Generator.
Creates viral product showcase banners, discount badges, and carousel slides using Pillow.
"""

import os
import io
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Any, Optional

GENERATED_IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated_images")


class ImageGenerator:
    def __init__(self):
        os.makedirs(GENERATED_IMG_DIR, exist_ok=True)

    def _get_font(self, size: int, bold: bool = False):
        """Loads a clean system font with fallback."""
        font_names = [
            "arialbd.ttf" if bold else "arial.ttf",
            "seguisb.ttf" if bold else "segoeui.ttf",
            "tahoma.ttf",
            "calibri.ttf"
        ]
        # Common Windows font paths
        win_fonts = os.environ.get("WINDIR", "C:\\Windows") + "\\Fonts"
        for name in font_names:
            font_path = os.path.join(win_fonts, name)
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def generate_product_banner(self, product: Dict[str, Any], banner_type: str = "square") -> str:
        """
        Generates an Instagram-optimized banner.
        banner_type: 'square' (1080x1080) or 'story' (1080x1920)
        """
        width, height = (1080, 1080) if banner_type == "square" else (1080, 1920)

        # 1. Create Base Background with Dark Gradient
        img = Image.new("RGB", (width, height), color=(15, 18, 26))
        draw = ImageDraw.Draw(img)

        # Draw subtle gradient / background glow
        for y in range(height):
            ratio = y / height
            r = int(15 + ratio * 15)
            g = int(18 + ratio * 10)
            b = int(26 + ratio * 20)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # 2. Header Hook Banner
        header_bg_height = 130
        draw.rectangle([(0, 0), (width, header_bg_height)], fill=(245, 158, 11))  # Amber/Yellow accent
        title_font = self._get_font(44, bold=True)
        draw.text((width // 2, 65), "VIRAL AMAZON FIND OF THE DAY", fill=(10, 10, 15), anchor="mm", font=title_font)

        # 3. Product Photo Card
        card_w, card_h = 760, 520 if banner_type == "square" else 760
        card_x = (width - card_w) // 2
        card_y = 170

        # Draw card background & drop shadow
        draw.rounded_rectangle([(card_x - 4, card_y - 4), (card_x + card_w + 4, card_y + card_h + 4)], radius=24, fill=(35, 42, 58))
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=20, fill=(255, 255, 255))

        # Download & paste product image
        product_img_loaded = False
        img_url = product.get("image_url")
        if img_url:
            try:
                resp = requests.get(img_url, timeout=5)
                if resp.status_code == 200:
                    prod_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    # Resize keeping aspect ratio
                    prod_img.thumbnail((card_w - 40, card_h - 40), Image.Resampling.LANCZOS)
                    # Center inside card
                    px = card_x + (card_w - prod_img.width) // 2
                    py = card_y + (card_h - prod_img.height) // 2
                    img.paste(prod_img, (px, py))
                    product_img_loaded = True
            except Exception:
                pass

        if not product_img_loaded:
            placeholder_font = self._get_font(40, bold=True)
            draw.text((width // 2, card_y + card_h // 2), "BEST SELLING GADGET", fill=(100, 100, 100), anchor="mm", font=placeholder_font)

        # 4. Badge: Discount %
        discount = int(product.get("discount_pct", 50))
        badge_text = f"FLAT {discount}% OFF"
        badge_w, badge_h = 280, 64
        badge_x = card_x - 20
        badge_y = card_y + 20
        draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=16, fill=(239, 68, 68))
        badge_font = self._get_font(30, bold=True)
        draw.text((badge_x + badge_w // 2, badge_y + badge_h // 2), badge_text, fill=(255, 255, 255), anchor="mm", font=badge_font)

        # 5. Product Title
        cur_y = card_y + card_h + 35
        title_text = product.get("title", "Viral Trending Gadget")
        if len(title_text) > 55:
            title_text = title_text[:52] + "..."
        prod_title_font = self._get_font(36, bold=True)
        draw.text((width // 2, cur_y), title_text, fill=(255, 255, 255), anchor="mm", font=prod_title_font)

        # 6. Ratings & Social Proof
        cur_y += 50
        rating = product.get("rating", 4.5)
        reviews = product.get("reviews_count", 1500)
        rating_text = f"Rating: {rating} / 5.0  •  {reviews:,}+ Verified Orders"
        rating_font = self._get_font(26, bold=False)
        draw.text((width // 2, cur_y), rating_text, fill=(251, 191, 36), anchor="mm", font=rating_font)

        # 7. Price Block
        cur_y += 65
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        price_font = self._get_font(48, bold=True)
        mrp_font = self._get_font(30, bold=False)

        price_str = f"Deal: ₹{deal_price:,}"
        mrp_str = f"MRP: ₹{orig_price:,}" if orig_price > deal_price else ""

        # Draw green deal price and strikethrough MRP
        if mrp_str:
            draw.text((width // 2 - 140, cur_y), price_str, fill=(16, 185, 129), anchor="mm", font=price_font)
            mrp_x = width // 2 + 150
            draw.text((mrp_x, cur_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
            draw.line([(mrp_x - 90, cur_y), (mrp_x + 90, cur_y)], fill=(239, 68, 68), width=3)
        else:
            draw.text((width // 2, cur_y), price_str, fill=(16, 185, 129), anchor="mm", font=price_font)

        # 8. Call To Action Footer Bar
        footer_y = height - 120
        draw.rectangle([(0, footer_y), (width, height)], fill=(30, 41, 59))
        cta_font = self._get_font(28, bold=True)
        draw.text((width // 2, footer_y + 40), "LINK IN BIO & STORIES", fill=(255, 255, 255), anchor="mm", font=cta_font)
        sub_cta_font = self._get_font(22, bold=False)
        draw.text((width // 2, footer_y + 80), "Comment 'LINK' & our bot will DM you the direct discount link!", fill=(245, 158, 11), anchor="mm", font=sub_cta_font)

        # Save to disk
        pid = product.get("product_id", "prod")
        filename = f"post_{pid}_{banner_type}.jpg"
        filepath = os.path.join(GENERATED_IMG_DIR, filename)
        img.save(filepath, "JPEG", quality=92)
        return filepath
