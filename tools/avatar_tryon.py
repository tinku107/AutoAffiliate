"""AI Avatar Virtual Try-On Engine powered by OpenAI.
Takes the brand avatar model (Elena) and dynamically dresses her in the scraped fashion product
(sarees, kurtas, dresses, jewellery, shirts) for 100% personalized high-converting social posts.
"""

import os
import io
import time
import base64
import requests
from PIL import Image
from typing import Dict, Any, Optional

TRYON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "generated_images")


class AvatarTryOnEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        os.makedirs(TRYON_DIR, exist_ok=True)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-"))

    def _build_tryon_prompt(self, product: Dict[str, Any], channel_profile: Optional[Dict[str, Any]] = None) -> str:
        """Constructs a high-fashion editorial photoshoot prompt for the avatar."""
        title = product.get("title", "curated fashion outfit").strip()
        category = product.get("category", "fashion").lower()
        platform = product.get("platform", "Amazon")

        # Clean title to extract the core garment
        clean_garment = title.split("(")[0].split("-")[0].split("|")[0].strip()
        words = clean_garment.split()
        if len(words) > 8:
            clean_garment = " ".join(words[:8])

        # Gender & style detection
        if any(k in category or k in title.lower() for k in ["men", "shirt", "suit", "kurta pajama", "t-shirt"]):
            model_desc = "A handsome, stylish 26-year-old Indian male fashion model with well-groomed hair, sharp jawline, and confident smile"
            garment_desc = f"wearing an authentic, perfectly tailored {clean_garment}"
        else:
            model_desc = "Elena, a stunning and elegant 24-year-old Indian female fashion model with glowing warm complexion, expressive eyes, and graceful poise"
            garment_desc = f"draped gracefully in a luxurious, authentic {clean_garment} with intricate fabric details and rich textures"

        prompt = (
            f"Professional studio fashion catalog photoshoot of {model_desc}, {garment_desc}. "
            f"Clean minimalist luxury studio background with soft warm ambient lighting, 8k resolution, "
            f"photorealistic fabric weave, vibrant true-to-life colors, editorial magazine aesthetic, sharp focus."
        )
        return prompt

    def generate_avatar_photoshoot(
        self,
        product: Dict[str, Any],
        avatar_path: Optional[str] = None,
        channel_profile: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Generates an AI photoshoot of the avatar model wearing the scraped product.
        Returns the saved local image path or None on failure.
        """
        if not self.is_configured():
            return None

        pid = product.get("product_id") or f"prod_{int(time.time())}"
        cache_filename = f"tryon_{pid}_avatar.jpg"
        cache_path = os.path.join(TRYON_DIR, cache_filename)

        # Return cached photoshoot if already generated for this product
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 10000:
            return cache_path

        prompt = self._build_tryon_prompt(product, channel_profile=channel_profile)

        # Try OpenAI image models
        candidate_models = ["gpt-image-1-mini", "gpt-image-1", "gpt-image-1.5"]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for model_name in candidate_models:
            try:
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024"
                }
                resp = requests.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=headers,
                    json=payload,
                    timeout=45
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    if data:
                        item = data[0]
                        # Handle base64 output
                        if "b64_json" in item:
                            raw_bytes = base64.b64decode(item["b64_json"])
                            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                            img.save(cache_path, "JPEG", quality=95)
                            return cache_path
                        # Handle URL output
                        elif "url" in item:
                            img_resp = requests.get(item["url"], timeout=15)
                            if img_resp.status_code == 200:
                                img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                                img.save(cache_path, "JPEG", quality=95)
                                return cache_path
            except Exception as e:
                print(f"OpenAI try-on attempt with {model_name} note: {e}")
                continue

        return None
