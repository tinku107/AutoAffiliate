"""AI Short-Form Video Generator for Instagram Reels, Facebook Reels, and YouTube Shorts.
Generates vertical 9:16 (720x1280) high-converting MP4 videos featuring:
- Real product images with subtle motion effects
- Neural AI voiceover narration using edge-tts (Indian English)
- Animated discount badges, price drop tags, star ratings, and CTA overlays
- Direct H.264/AAC MP4 compilation using bundled ffmpeg
"""

import os
import io
import math
import asyncio
import subprocess
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import edge_tts
from typing import Dict, Any, Optional

GENERATED_VID_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated_videos")


class VideoGenerator:
    def __init__(self):
        os.makedirs(GENERATED_VID_DIR, exist_ok=True)
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.width = 720
        self.height = 1280
        self.fps = 24

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
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()

    async def _generate_voiceover_async(self, text: str, output_path: str):
        """Generates clear, energetic neural voiceover in Indian English."""
        voice = "en-IN-PrabhatNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def generate_voiceover(self, text: str, output_path: str):
        try:
            asyncio.run(self._generate_voiceover_async(text, output_path))
            return True
        except Exception as e:
            print(f"Voiceover generation fallback: {e}")
            return False

    def generate_reel_video(self, product: Dict[str, Any]) -> str:
        """
        Creates a complete 9:16 vertical Reel MP4 video with AI voiceover and animated overlays.
        """
        pid = product.get("product_id", "prod")
        title = product.get("title", "Viral Trending Product")
        short_title = title.split("(")[0].split("-")[0].strip()[:35]
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        discount = int(product.get("discount_pct", 0))
        rating = product.get("rating", 4.5)
        reviews = product.get("reviews_count", 1200)

        # 1. Prepare Voiceover Script
        if orig_price > deal_price and discount > 0:
            narration = (
                f"Stop scrolling! Look at this massive offer on the {short_title}. "
                f"It is currently down to just {deal_price} rupees, with flat {discount} percent off. "
                f"Rated 4.5 stars with thousands of happy orders. "
                f"Comment LINK right now and I will immediately send you the direct discount link!"
            )
        else:
            narration = (
                f"Stop scrolling! Check out this top-rated {short_title}. "
                f"Grab it now for only {deal_price} rupees. "
                f"Rated 4.5 stars with verified buyer reviews. "
                f"Comment LINK below to get the direct discount link sent right to your DM!"
            )

        audio_path = os.path.join(GENERATED_VID_DIR, f"audio_{pid}.mp3")
        self.generate_voiceover(narration, audio_path)

        # Standard Reel Duration: 8 seconds (192 frames @ 24 fps)
        duration_sec = 8.0
        total_frames = int(duration_sec * self.fps)

        # 2. Download & cache product image
        prod_img = None
        img_url = product.get("image_url")
        if img_url:
            try:
                resp = requests.get(img_url, timeout=6)
                if resp.status_code == 200:
                    prod_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            except Exception:
                pass

        if not prod_img:
            # Fallback placeholder card
            prod_img = Image.new("RGBA", (500, 500), color=(255, 255, 255, 255))

        # 3. Render frames pipeline directly to ffmpeg via stdin pipe
        video_temp_path = os.path.join(GENERATED_VID_DIR, f"video_temp_{pid}.mp4")
        final_mp4_path = os.path.join(GENERATED_VID_DIR, f"reel_{pid}.mp4")

        # FFmpeg video writer process
        ffmpeg_cmd = [
            self.ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self.width}x{self.height}",
            "-pix_fmt", "rgb24",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            video_temp_path
        ]

        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        for frame_idx in range(total_frames):
            t = frame_idx / self.fps
            progress = t / duration_sec

            # Create base 9:16 frame with dark aesthetic gradient
            frame = Image.new("RGB", (self.width, self.height), color=(11, 15, 25))
            draw = ImageDraw.Draw(frame)

            # Draw background gradient
            for y in range(0, self.height, 4):
                ratio = y / self.height
                r = int(12 + ratio * 20)
                g = int(16 + ratio * 15)
                b = int(28 + ratio * 35)
                draw.rectangle([(0, y), (self.width, y + 4)], fill=(r, g, b))

            # Header Hook Banner
            header_y = 60
            draw.rectangle([(0, 0), (self.width, 110)], fill=(245, 158, 11))
            hook_font = self._get_font(34, bold=True)
            draw.text((self.width // 2, 55), "VIRAL DEAL ALERT ⚡", fill=(10, 10, 15), anchor="mm", font=hook_font)

            # Animated zoom on product card (Gentle breathing effect)
            zoom_factor = 1.0 + 0.04 * math.sin(t * 2.5)
            card_w = int(580 * zoom_factor)
            card_h = int(500 * zoom_factor)
            card_x = (self.width - card_w) // 2
            card_y = 160 + int(8 * math.sin(t * 2.0))

            # White Card with soft shadow
            draw.rounded_rectangle([(card_x - 3, card_y - 3), (card_x + card_w + 3, card_y + card_h + 3)], radius=24, fill=(40, 50, 70))
            draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=20, fill=(255, 255, 255))

            # Paste product image centered
            p_img_resized = prod_img.copy()
            p_img_resized.thumbnail((card_w - 40, card_h - 40), Image.Resampling.LANCZOS)
            px = card_x + (card_w - p_img_resized.width) // 2
            py = card_y + (card_h - p_img_resized.height) // 2
            frame.paste(p_img_resized, (px, py), p_img_resized if p_img_resized.mode == "RGBA" else None)

            # Floating Animated Badge (Pulsing discount)
            if discount > 0:
                badge_w, badge_h = 240, 60
                badge_x = card_x - 10
                badge_y = card_y + 15
                badge_color = (239, 68, 68) if int(t * 3) % 2 == 0 else (220, 38, 38)
                draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=15, fill=badge_color)
                b_font = self._get_font(26, bold=True)
                draw.text((badge_x + badge_w // 2, badge_y + badge_h // 2), f"FLAT {discount}% OFF", fill=(255, 255, 255), anchor="mm", font=b_font)

            # Title Block
            t_y = card_y + card_h + 40
            t_font = self._get_font(32, bold=True)
            draw.text((self.width // 2, t_y), short_title, fill=(255, 255, 255), anchor="mm", font=t_font)

            # Star Ratings
            t_y += 45
            star_font = self._get_font(24, bold=False)
            draw.text((self.width // 2, t_y), f"Rating: {rating} / 5.0  •  {reviews:,}+ Orders", fill=(251, 191, 36), anchor="mm", font=star_font)

            # Big Animated Price Drop
            t_y += 70
            price_font = self._get_font(48, bold=True)
            mrp_font = self._get_font(28, bold=False)
            deal_str = f"Deal: ₹{deal_price:,}"
            mrp_str = f"MRP: ₹{orig_price:,}" if orig_price > deal_price else ""

            if mrp_str:
                draw.text((self.width // 2 - 130, t_y), deal_str, fill=(16, 185, 129), anchor="mm", font=price_font)
                mrp_x = self.width // 2 + 130
                draw.text((mrp_x, t_y), mrp_str, fill=(156, 163, 175), anchor="mm", font=mrp_font)
                draw.line([(mrp_x - 70, t_y), (mrp_x + 70, t_y)], fill=(239, 68, 68), width=3)
            else:
                draw.text((self.width // 2, t_y), deal_str, fill=(16, 185, 129), anchor="mm", font=price_font)

            # Bottom Animated Call to Action Banner
            cta_y = self.height - 180
            # Subtle bounce
            cta_y += int(6 * math.sin(t * 4))
            draw.rounded_rectangle([(40, cta_y), (self.width - 40, cta_y + 110)], radius=22, fill=(220, 38, 38))
            cta_font = self._get_font(28, bold=True)
            draw.text((self.width // 2, cta_y + 38), "👉 COMMENT 'LINK' BELOW", fill=(255, 255, 255), anchor="mm", font=cta_font)
            sub_cta_font = self._get_font(20, bold=False)
            draw.text((self.width // 2, cta_y + 75), "Instant DM with direct discount link sent to you!", fill=(254, 240, 138), anchor="mm", font=sub_cta_font)

            # Write raw frame bytes to ffmpeg
            proc.stdin.write(frame.tobytes())

        proc.stdin.close()
        proc.wait()

        # 4. Multiplex Video + AI Voiceover Audio
        if os.path.exists(audio_path):
            merge_cmd = [
                self.ffmpeg_exe,
                "-y",
                "-i", video_temp_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                final_mp4_path
            ]
            subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Cleanup temp video
            if os.path.exists(video_temp_path):
                os.remove(video_temp_path)
            return final_mp4_path
        else:
            return video_temp_path
