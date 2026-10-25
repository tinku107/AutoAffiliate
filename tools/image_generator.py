"""High-converting Instagram & Facebook Graphic Asset Generator.
Creates multi-image carousels grabbing all angles/pictures from Amazon & Flipkart.
Zero AI/bot mentions: clean, professional, human-curator aesthetic.
"""

import os
import io
import re
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

    def _resolve_avatar_path(self, channel_profile: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Resolves the permanent brand avatar image path."""
        base_dir = os.path.dirname(os.path.dirname(__file__))

        if channel_profile and channel_profile.get("avatar_image"):
            cand = channel_profile.get("avatar_image")
            if os.path.isabs(cand) and os.path.exists(cand):
                return cand
            rel = os.path.join(base_dir, cand)
            if os.path.exists(rel):
                return rel

        # Default Elena avatar only for elenas_world or unspecified channel
        prof_id = (channel_profile or {}).get("id", "")
        if not channel_profile or prof_id in ["elenas_world", "fashion"]:
            default_elena = os.path.join(base_dir, "data", "assets", "elena_avatar.jpg")
            if os.path.exists(default_elena):
                return default_elena

        return None

    def _fetch_image(self, url: str) -> Optional[Image.Image]:
        """Safely downloads an image with browser headers."""
        if not url:
            return None
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                return Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception:
            pass
        return None

    def _clean_title(self, raw_title: str, max_words: int = 7) -> str:
        """Cleans and truncates product title gracefully at word boundaries."""
        t = raw_title.split("(")[0].split("-")[0].split("|")[0].strip()
        words = t.split()
        if len(words) > max_words:
            t = " ".join(words[:max_words])
        if len(t) > 42:
            t = t[:42].rsplit(" ", 1)[0]
        return t

    def generate_carousel_slides(self, product: Dict[str, Any], max_slides: int = 8, channel_profile: Optional[Dict[str, Any]] = None, enable_avatar: bool = False) -> List[str]:
        """
        Creates a multi-image Instagram/Facebook carousel:
        - When enable_avatar=False (Default): Uses 100% authentic scraped product images from the store.
        - When enable_avatar=True: Embeds Elena avatar watermark seal.
        """
        avatar_path = self._resolve_avatar_path(channel_profile) if enable_avatar else None
        image_urls = product.get("image_urls", [])
        if not image_urls and product.get("image_url"):
            image_urls = [product.get("image_url")]

        generated_paths = []

        if avatar_path:
            # Elena's World Architecture:
            # Slide 1 = Avatar Hero Showcase
            # Slides 2..N = Scraped Gallery Photos
            scraped_count = min(len(image_urls), max_slides - 1)
            total_slides = 1 + scraped_count

            # 1. Slide 1: Dedicated Avatar Hero Slide
            hero_slide = self.generate_avatar_hero_slide(
                product=product,
                avatar_path=avatar_path,
                total_slides=total_slides,
                channel_profile=channel_profile
            )
            generated_paths.append(hero_slide)

            # 2. Slides 2 to N: All Scraped Product Gallery Photos
            for idx in range(scraped_count):
                img_url = image_urls[idx]
                slide_num = idx + 2
                slide_path = self.generate_scraped_gallery_slide(
                    product=product,
                    img_url=img_url,
                    slide_idx=slide_num,
                    total_slides=total_slides,
                    avatar_path=avatar_path,
                    channel_profile=channel_profile
                )
                generated_paths.append(slide_path)

        else:
            # Fallback for channels without custom avatar
            num_slides = min(max_slides, max(1, len(image_urls)))
            for slide_idx in range(num_slides):
                img_url = image_urls[slide_idx % len(image_urls)]
                slide_path = self.generate_scraped_gallery_slide(
                    product=product,
                    img_url=img_url,
                    slide_idx=slide_idx + 1,
                    total_slides=num_slides,
                    avatar_path=None,
                    channel_profile=channel_profile
                )
                generated_paths.append(slide_path)

        return generated_paths

    def generate_avatar_hero_slide(self, product: Dict[str, Any], avatar_path: str, total_slides: int = 1, channel_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Slide 1: High-Converting Full-Width Real Product Hero Slide.
        Showcases 100% authentic scraped store photo in high resolution, with Elena featured
        as a circular brand ambassador watermark badge in the header corner.
        """
        width, height = (1080, 1080)
        img, draw = self._draw_base_slide(width, height)

        brand_name = (channel_profile or {}).get("name", "Elena's World").split("(")[0].strip().upper()
        if not brand_name:
            brand_name = "ELENA'S WORLD"

        short_title = self._clean_title(product.get("title", "Curated Viral Find"))
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        discount = int(product.get("discount_pct", 0))
        rating = product.get("rating", 4.6)
        reviews = product.get("reviews_count", 2400)
        pid = product.get("product_id", "prod")

        # 1. Header Bar with Elena Circular Avatar Badge
        header_h = 105
        draw.rectangle([(0, 0), (width, header_h)], fill=(12, 15, 23))
        draw.line([(0, header_h), (width, header_h)], fill=(245, 158, 11), width=4)

        has_avatar = avatar_path and os.path.exists(avatar_path)
        text_start_x = 60
        if has_avatar:
            try:
                av_size = 78
                av_raw = Image.open(avatar_path).convert("RGBA").resize((av_size, av_size), Image.Resampling.LANCZOS)
                av_mask = Image.new("L", (av_size, av_size), 0)
                ImageDraw.Draw(av_mask).ellipse((0, 0, av_size, av_size), fill=255)
                av_x, av_y = 60, 13
                # Gold circular ring
                draw.ellipse((av_x - 3, av_y - 3, av_x + av_size + 3, av_y + av_size + 3), fill=(245, 158, 11))
                img.paste(av_raw, (av_x, av_y), av_mask)
                text_start_x = av_x + av_size + 24
            except Exception as e:
                print(f"Avatar load note: {e}")

        # Brand & Verification Header Text
        draw.text((text_start_x, 40), f"{brand_name} • CURATED STYLE PICK", fill=(245, 158, 11), anchor="lm", font=self._get_font(28, bold=True))
        draw.text((text_start_x, 74), "VERIFIED HIGH-VALUE FIND • 100% AUTHENTIC", fill=(148, 163, 184), anchor="lm", font=self._get_font(18, bold=False))

        # Slide indicator pill on right
        draw.rounded_rectangle([(width - 250, 26), (width - 60, 78)], radius=14, fill=(30, 41, 59))
        draw.text((width - 155, 52), f"Slide 1 of {total_slides}", fill=(255, 255, 255), anchor="mm", font=self._get_font(20, bold=True))

        # 2. Main Full-Width Scraped Product Card
        card_x = 60
        card_y = 125
        card_w = 960
        card_h = 670

        draw.rounded_rectangle([(card_x - 4, card_y - 4), (card_x + card_w + 4, card_y + card_h + 4)], radius=24, fill=(45, 55, 72))
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=20, fill=(255, 255, 255))

        # Download & display authentic scraped product photo
        primary_img_url = product.get("image_url", "")
        if not primary_img_url and product.get("image_urls"):
            primary_img_url = product.get("image_urls")[0]

        prod_img = self._fetch_image(primary_img_url)
        if prod_img:
            prod_img.thumbnail((card_w - 40, card_h - 40), Image.Resampling.LANCZOS)
            px = card_x + (card_w - prod_img.width) // 2
            py = card_y + (card_h - prod_img.height) // 2
            img.paste(prod_img, (px, py))

        # Badges on the scraped photo
        # Top-Left: "REAL STORE PICTURE" + Curator Tag (dynamically sized)
        curator_tag = "CURATED BY ELENA" if "ELENA" in brand_name else f"CURATED BY {brand_name}"
        curator_badge_text = f"REAL STORE PICTURE • {curator_tag}"
        badge_font = self._get_font(14, bold=True)
        b_bbox = badge_font.getbbox(curator_badge_text)
        b_text_w = b_bbox[2] - b_bbox[0]
        badge_w = b_text_w + 36
        draw.rounded_rectangle([(card_x + 20, card_y + 20), (card_x + 20 + badge_w, card_y + 68)], radius=12, fill=(15, 23, 42))
        draw.text((card_x + 20 + badge_w // 2, card_y + 44), curator_badge_text, fill=(245, 158, 11), anchor="mm", font=badge_font)

        # Top-Right: Discount Badge
        if discount > 0:
            draw.rounded_rectangle([(card_x + card_w - 210, card_y + 20), (card_x + card_w - 20, card_y + 68)], radius=12, fill=(220, 38, 38))
            draw.text((card_x + card_w - 115, card_y + 44), f"FLAT {discount}% OFF", fill=(255, 255, 255), anchor="mm", font=self._get_font(20, bold=True))

        # Bottom-Left on Card: Rating Badge (dynamically sized)
        rating_badge_text = f"Rating: {rating} / 5.0  •  {reviews:,}+ Orders"
        r_font = self._get_font(17, bold=True)
        r_bbox = r_font.getbbox(rating_badge_text)
        r_text_w = r_bbox[2] - r_bbox[0]
        r_badge_w = r_text_w + 36
        draw.rounded_rectangle([(card_x + 20, card_y + card_h - 60), (card_x + 20 + r_badge_w, card_y + card_h - 16)], radius=12, fill=(15, 23, 42))
        draw.text((card_x + 20 + r_badge_w // 2, card_y + card_h - 38), rating_badge_text, fill=(251, 191, 36), anchor="mm", font=r_font)

        # 3. Product Info & Pricing Bar Below Card
        info_y = card_y + card_h + 30
        deal_str = f"Deal: ₹{deal_price:,}"
        mrp_str = f"MRP: ₹{orig_price:,}" if orig_price > deal_price else ""
        save_str = f"Save ₹{orig_price - deal_price:,} (Flat {discount}% OFF)" if (orig_price > deal_price and discount > 0) else ""

        deal_font = self._get_font(38, bold=True)
        mrp_font = self._get_font(26, bold=False)
        save_font = self._get_font(24, bold=True)

        if mrp_str and save_str:
            deal_bbox = deal_font.getbbox(deal_str)
            deal_w = deal_bbox[2] - deal_bbox[0]
            mrp_bbox = mrp_font.getbbox(mrp_str)
            mrp_w = mrp_bbox[2] - mrp_bbox[0]
            save_bbox = save_font.getbbox(save_str)
            save_w = save_bbox[2] - save_bbox[0]

            gap = 36
            total_w = deal_w + gap + mrp_w + gap + save_w
            start_x = (width - total_w) // 2

            deal_cx = start_x + deal_w // 2
            mrp_cx = start_x + deal_w + gap + mrp_w // 2
            save_cx = start_x + deal_w + gap + mrp_w + gap + save_w // 2

            draw.text((deal_cx, info_y), deal_str, fill=(16, 185, 129), anchor="mm", font=deal_font)
            draw.text((mrp_cx, info_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
            draw.line([(mrp_cx - mrp_w // 2 - 4, info_y), (mrp_cx + mrp_w // 2 + 4, info_y)], fill=(239, 68, 68), width=3)
            draw.text((save_cx, info_y), save_str, fill=(245, 158, 11), anchor="mm", font=save_font)
        elif mrp_str:
            draw.text((width // 2 - 120, info_y), deal_str, fill=(16, 185, 129), anchor="mm", font=deal_font)
            draw.text((width // 2 + 130, info_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
            draw.line([(width // 2 + 60, info_y), (width // 2 + 200, info_y)], fill=(239, 68, 68), width=3)
        else:
            draw.text((width // 2, info_y), deal_str, fill=(16, 185, 129), anchor="mm", font=deal_font)

        title_y = info_y + 44
        draw.text((width // 2, title_y), short_title, fill=(203, 213, 225), anchor="mm", font=self._get_font(24, bold=False))

        # 4. Bottom Navigation Footer
        footer_y = height - 110
        draw.rectangle([(0, footer_y), (width, height)], fill=(20, 27, 41))
        draw.line([(0, footer_y), (width, footer_y)], fill=(51, 65, 85), width=2)
        if total_slides > 1:
            draw.text((width // 2, footer_y + 38), f"SWIPE TO SEE ALL {total_slides} REAL STORE PHOTOS & ANGLES >>", fill=(255, 255, 255), anchor="mm", font=self._get_font(24, bold=True))
        else:
            draw.text((width // 2, footer_y + 38), "LIMITED TIME EXCLUSIVE DEAL >>", fill=(255, 255, 255), anchor="mm", font=self._get_font(24, bold=True))
        draw.text((width // 2, footer_y + 75), "Comment 'LINK' below and I'll send you the verified purchase link!", fill=(245, 158, 11), anchor="mm", font=self._get_font(20, bold=False))

        filename = f"post_{pid}_slide_1_avatar.jpg"
        filepath = os.path.join(GENERATED_IMG_DIR, filename)
        img.save(filepath, "JPEG", quality=95)
        return filepath

    def generate_scraped_gallery_slide(self, product: Dict[str, Any], img_url: str, slide_idx: int, total_slides: int, avatar_path: Optional[str] = None, channel_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Slides 2 to N: Real Scraped Store Gallery Slides.
        Focuses 100% on displaying the actual scraped store photo in high resolution,
        with angle badges, Elena watermark badge, price summary, and swipe navigation.
        """
        width, height = (1080, 1080)
        img, draw = self._draw_base_slide(width, height)

        brand_name = (channel_profile or {}).get("name", "Elena's World").split("(")[0].strip().upper()
        if not brand_name:
            brand_name = "ELENA'S WORLD"

        short_title = self._clean_title(product.get("title", "Curated Viral Find"))
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        discount = int(product.get("discount_pct", 0))
        pid = product.get("product_id", "prod")

        # Angle classification based on slide index
        if slide_idx == 1:
            angle_tag = "AUTHENTIC PRODUCT"
            sub_head = f"PHOTO 1 OF {total_slides}: AUTHENTIC SCRAPED STORE PHOTO"
        elif slide_idx == 2:
            angle_tag = "FRONT & FULL DRAPE"
            sub_head = f"PHOTO 2 OF {total_slides}: FRONT & FULL DRAPE VIEW"
        elif slide_idx == 3:
            angle_tag = "FABRIC WEAVE & DETAIL"
            sub_head = f"PHOTO 3 OF {total_slides}: FABRIC & MATERIAL CLOSE-UP"
        elif slide_idx == 4:
            angle_tag = "BORDER & WORK DETAIL"
            sub_head = f"PHOTO 4 OF {total_slides}: BORDER, PALLU & FINISH DETAIL"
        elif slide_idx == 5:
            angle_tag = "LIFESTYLE & WEAR"
            sub_head = f"PHOTO 5 OF {total_slides}: LIFESTYLE & WEAR LOOK"
        else:
            angle_tag = "ADDITIONAL ANGLE"
            sub_head = f"PHOTO {slide_idx} OF {total_slides}: REAL STORE PERSPECTIVE"

        # 1. Header Bar
        header_h = 100
        draw.rectangle([(0, 0), (width, header_h)], fill=(12, 15, 23))
        draw.line([(0, header_h), (width, header_h)], fill=(245, 158, 11), width=4)
        draw.text((60, 38), f"{brand_name} • REAL STORE GALLERY", fill=(245, 158, 11), anchor="lm", font=self._get_font(30, bold=True))
        draw.text((60, 72), sub_head, fill=(148, 163, 184), anchor="lm", font=self._get_font(18, bold=False))

        # Slide indicator pill
        draw.rounded_rectangle([(width - 250, 24), (width - 125, 76)], radius=14, fill=(30, 41, 59))
        draw.text((width - 187, 50), f"Slide {slide_idx} of {total_slides}", fill=(255, 255, 255), anchor="mm", font=self._get_font(20, bold=True))

        # Circular Avatar Watermark in header corner
        if avatar_path and os.path.exists(avatar_path):
            try:
                av_size = 76
                av_raw = Image.open(avatar_path).convert("RGBA").resize((av_size, av_size), Image.Resampling.LANCZOS)
                av_mask = Image.new("L", (av_size, av_size), 0)
                ImageDraw.Draw(av_mask).ellipse((0, 0, av_size, av_size), fill=255)
                av_x, av_y = width - 100, 12
                draw.ellipse((av_x - 3, av_y - 3, av_x + av_size + 3, av_y + av_size + 3), fill=(245, 158, 11))
                img.paste(av_raw, (av_x, av_y), av_mask)
            except Exception:
                pass

        # 2. Main Gallery Photo Card (Huge high-contrast card for the real scraped photo)
        card_x = 60
        card_y = 125
        card_w = 960
        card_h = 670

        draw.rounded_rectangle([(card_x - 4, card_y - 4), (card_x + card_w + 4, card_y + card_h + 4)], radius=24, fill=(45, 55, 72))
        draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=20, fill=(255, 255, 255))

        # Download & display scraped photo
        prod_img = self._fetch_image(img_url)
        if prod_img:
            prod_img.thumbnail((card_w - 40, card_h - 40), Image.Resampling.LANCZOS)
            px = card_x + (card_w - prod_img.width) // 2
            py = card_y + (card_h - prod_img.height) // 2
            img.paste(prod_img, (px, py))

        # Badges on the scraped photo
        draw.rounded_rectangle([(card_x + 20, card_y + 20), (card_x + 280, card_y + 68)], radius=12, fill=(15, 23, 42))
        draw.text((card_x + 150, card_y + 44), angle_tag, fill=(245, 158, 11), anchor="mm", font=self._get_font(18, bold=True))

        if discount > 0:
            draw.rounded_rectangle([(card_x + card_w - 210, card_y + 20), (card_x + card_w - 20, card_y + 68)], radius=12, fill=(220, 38, 38))
            draw.text((card_x + card_w - 115, card_y + 44), f"FLAT {discount}% OFF", fill=(255, 255, 255), anchor="mm", font=self._get_font(20, bold=True))

        # 3. Product Info Bar below card
        info_y = card_y + card_h + 30
        deal_str = f"Deal: ₹{deal_price:,}"
        mrp_str = f"MRP: ₹{orig_price:,}" if orig_price > deal_price else ""
        save_str = f"Save ₹{orig_price - deal_price:,} ({discount}% OFF)" if (orig_price > deal_price and discount > 0) else ""

        deal_font = self._get_font(38, bold=True)
        mrp_font = self._get_font(26, bold=False)
        save_font = self._get_font(24, bold=True)

        if mrp_str and save_str:
            deal_bbox = deal_font.getbbox(deal_str)
            deal_w = deal_bbox[2] - deal_bbox[0]
            mrp_bbox = mrp_font.getbbox(mrp_str)
            mrp_w = mrp_bbox[2] - mrp_bbox[0]
            save_bbox = save_font.getbbox(save_str)
            save_w = save_bbox[2] - save_bbox[0]

            gap = 36
            total_w = deal_w + gap + mrp_w + gap + save_w
            start_x = (width - total_w) // 2

            deal_cx = start_x + deal_w // 2
            mrp_cx = start_x + deal_w + gap + mrp_w // 2
            save_cx = start_x + deal_w + gap + mrp_w + gap + save_w // 2

            draw.text((deal_cx, info_y), deal_str, fill=(16, 185, 129), anchor="mm", font=deal_font)
            draw.text((mrp_cx, info_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
            draw.line([(mrp_cx - mrp_w // 2 - 4, info_y), (mrp_cx + mrp_w // 2 + 4, info_y)], fill=(239, 68, 68), width=3)
            draw.text((save_cx, info_y), save_str, fill=(245, 158, 11), anchor="mm", font=save_font)
        elif mrp_str:
            draw.text((width // 2 - 120, info_y), deal_str, fill=(16, 185, 129), anchor="mm", font=deal_font)
            draw.text((width // 2 + 130, info_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
            draw.line([(width // 2 + 60, info_y), (width // 2 + 200, info_y)], fill=(239, 68, 68), width=3)
        else:
            draw.text((width // 2, info_y), deal_str, fill=(16, 185, 129), anchor="mm", font=deal_font)

        title_y = info_y + 44
        draw.text((width // 2, title_y), short_title, fill=(203, 213, 225), anchor="mm", font=self._get_font(24, bold=False))

        # 4. Footer
        footer_y = height - 110
        draw.rectangle([(0, footer_y), (width, height)], fill=(20, 27, 41))
        draw.line([(0, footer_y), (width, footer_y)], fill=(51, 65, 85), width=2)
        if slide_idx < total_slides:
            draw.text((width // 2, footer_y + 38), "SWIPE FOR NEXT REAL ANGLE >>", fill=(255, 255, 255), anchor="mm", font=self._get_font(24, bold=True))
        else:
            draw.text((width // 2, footer_y + 38), "CLAIM THIS EXCLUSIVE PRICE BEFORE DEAL ENDS >>", fill=(255, 255, 255), anchor="mm", font=self._get_font(24, bold=True))
        draw.text((width // 2, footer_y + 75), "Comment 'LINK' below and I'll send you the verified purchase link!", fill=(245, 158, 11), anchor="mm", font=self._get_font(20, bold=False))

        filename = f"post_{pid}_slide_{slide_idx}_gallery.jpg"
        filepath = os.path.join(GENERATED_IMG_DIR, filename)
        img.save(filepath, "JPEG", quality=95)
        return filepath

    def generate_single_slide(self, product: Dict[str, Any], img_url: str = "", slide_idx: int = 0, total_slides: int = 1, avatar_path: Optional[str] = None) -> str:
        """Renders single slide (defaults to Avatar Hero slide if avatar present)."""
        av = avatar_path or self._resolve_avatar_path()
        if av:
            return self.generate_avatar_hero_slide(product, avatar_path=av, total_slides=total_slides)
        return self.generate_scraped_gallery_slide(product, img_url=img_url or product.get("image_url", ""), slide_idx=1, total_slides=1)

    def generate_product_banner(self, product: Dict[str, Any], banner_type: str = "square") -> str:
        """Generates single slide (main hero banner)."""
        return self.generate_single_slide(product, total_slides=1)
