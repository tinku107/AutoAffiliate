"""Content Creator Agent ('Creative').
Generates 100% humanoid, natural conversational social media content.
Strictly adheres to:
1. No icons or emojis
2. No decorative special characters (no fancy unicode borders, bullets, or arrows)
3. Authentic, friendly human curator phrasing
"""

import os
import re
import random
from typing import Dict, Any, Optional, List
from tools.image_generator import ImageGenerator
from tools.video_generator import VideoGenerator
from core.db import save_post, update_product_status, log_agent_action


def clean_humanoid_text(text: str) -> str:
    """
    Strips all emojis, pictorial symbols, and decorative special characters.
    Ensures text reads like clean, authentic, humanoid copy.
    """
    if not text:
        return ""
    # Remove emoji ranges
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010ffff]|[\u2600-\u27ff]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\u200d]|[\ufe0f]",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub("", text)
    # Remove decorative borders and non-standard bullets
    cleaned = re.sub(r"[━═─—_]{3,}", "", cleaned)
    cleaned = cleaned.replace("•", "-").replace("👉", "").replace("⭐", "star").replace("▼", "").replace("▲", "")
    # Clean up double spaces while keeping linebreaks
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
    return "\n".join(lines).strip()


class CreativeAgent:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.name = "Creative (Content Studio)"
        self.image_gen = ImageGenerator()
        self.video_gen = VideoGenerator()
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")

    def generate_content_for_product(self, product: Dict[str, Any], post_type: str = "carousel", channel_niche: Optional[str] = None) -> Dict[str, Any]:
        """Generates authentic humanoid copy, reel script, and visual assets without icons or special characters."""
        log_agent_action(self.name, f"Generating humanoid {post_type} content for: {product['title'][:35]}...", "started")

        # 1. Generate Multi-Image Carousel Slides
        try:
            media_paths = self.image_gen.generate_carousel_slides(product, max_slides=4)
        except Exception as e:
            log_agent_action(self.name, f"Image carousel note: {e}", "warning")
            media_paths = product.get("image_urls", [product.get("image_url", "")])

        title = product.get("title", "Featured Trending Find")
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        discount = int(product.get("discount_pct", 0))
        aff_url = product.get("affiliate_url", "")
        rating = product.get("rating", 4.4)
        reviews = product.get("reviews_count", 1200)
        category = (channel_niche or product.get("category", "General")).lower()
        platform_name = product.get("platform", "Amazon")

        short_title = title.split("(")[0].split("-")[0].strip()[:42]

        # Authentic humanoid copy per niche (Zero icons, zero decorative special characters)
        if "fashion" in category or "dress" in category or "kurta" in title.lower() or "saree" in title.lower():
            hooks = [
                f"Found a really pretty option while checking deals today: {short_title}.",
                f"If you are looking for comfortable ethnic wear, take a look at {short_title}.",
                f"Sharing a nice outfit find that is currently on discount: {short_title}."
            ]
            feature_summary = "The fabric feels breathable and the stitching details look very neat in person."
            use_case = "Works nicely for festive gatherings, family functions, or everyday casual styling."
            hashtags = "#fashion #indianfashion #ethnicwear #kurtis #sarees #outfitideas #dailydeals"

        elif "mobile" in category or "electronic" in category or "tech" in category or deal_price > 15000:
            hooks = [
                f"Spotted a solid price drop on the {short_title}.",
                f"If you have been waiting for a deal before upgrading your phone, look at {short_title}.",
                f"Just noticed a notable discount on the {short_title} today."
            ]
            feature_summary = "It offers smooth performance, reliable battery life, and strong camera capabilities."
            use_case = "Good option if you want reliable daily performance without paying the full retail launch price."
            hashtags = "#tech #gadgets #smartphones #electronics #techindia #deals #shopping"

        elif "toy" in category or "kid" in title.lower():
            hooks = [
                f"Found a fun and creative activity toy for kids: {short_title}.",
                f"If you need a thoughtful birthday gift idea, check out this {short_title}.",
                f"Sharing a top rated toy that keeps kids meaningfully occupied: {short_title}."
            ]
            feature_summary = "Build quality is sturdy, child safe, and designed to encourage problem solving skills."
            use_case = "Great choice for weekend playtime, gifting, and motor skill development."
            hashtags = "#toys #parenting #kidsgiftideas #learningtoys #deals #shopping"

        else:
            # Universal Humanoid Pattern for Any Niche (Home, Kitchen, Beauty, Fitness, etc.)
            hooks = [
                f"Came across a very practical find today: {short_title}.",
                f"If you like useful daily problem solvers, here is {short_title}.",
                f"Good discount currently running on the {short_title}."
            ]
            feature_summary = "Very functional design, easy to set up, and well rated by customers who purchased it."
            use_case = "Simple, durable, and genuinely convenient for regular daily use."
            hashtags = "#deals #usefulfinds #smartshopping #qualityfinds #onlineshopping"

        headline = random.choice(hooks)

        # 100% Humanoid Caption (Zero emojis, zero special bullets, natural conversational English)
        mrp_text = f" Original retail price was {orig_price} rupees, bringing the discount to {discount} percent." if orig_price > deal_price else ""
        caption = f"""{headline}

Here is a quick overview of this item:
Current deal price is {deal_price} rupees on {platform_name}.{mrp_text}
Customer rating is currently {rating} out of 5 based on verified purchaser reviews.
{feature_summary}
{use_case}

If you would like the direct verified link to check sizes or full specifications, simply reply or comment link below and I will send it straight to your message inbox.

You can also visit the link in my profile bio to see all of today's handpicked recommendations in one place.

Online prices and stock availability can change frequently on the platform.

Disclosure: This post contains affiliate links. As an associate I earn from qualifying purchases.

{hashtags}
"""

        caption = clean_humanoid_text(caption)

        # 15-Second Clean Humanoid Reel Script (Zero icons, zero special glyphs)
        reel_script = f"""15-Second Video Script: {short_title}

Scene 1 (0 to 3 seconds):
Visual: Clear view of the {short_title}.
Voiceover: "{headline}"
On-screen text: Deal Alert: {short_title}

Scene 2 (3 to 8 seconds):
Visual: Highlighting the key product features.
Voiceover: "The current price is {deal_price} rupees. {feature_summary}."
On-screen text: Deal Price: {deal_price} rupees

Scene 3 (8 to 12 seconds):
Visual: Showing customer reviews and close-up detail.
Voiceover: "It has a {rating} star rating from verified customers."
On-screen text: Rated {rating} out of 5

Scene 4 (12 to 15 seconds):
Visual: Prompting viewer to comment.
Voiceover: "Comment link below and I will message you the direct purchase link right away."
On-screen text: Comment LINK for Direct Link
"""
        reel_script = clean_humanoid_text(reel_script)

        # 2. Generate AI Vertical 9:16 Reel Video with Voiceover
        video_path = ""
        try:
            video_path = self.video_gen.generate_reel_video(product)
        except Exception as e:
            log_agent_action(self.name, f"Video generation note: {e}", "warning")

        post_data = {
            "product_id": product.get("id"),
            "platform": "instagram",
            "post_type": post_type,
            "headline": clean_humanoid_text(headline),
            "caption": caption,
            "hashtags": hashtags,
            "reel_script": reel_script,
            "media_paths": media_paths,
            "video_path": video_path,
            "affiliate_url": aff_url,
            "status": "draft"
        }

        # Save to DB
        post_id = save_post(post_data)
        post_data["id"] = post_id

        if product.get("id"):
            update_product_status(product["id"], "content_created")

        log_agent_action(self.name, f"Humanoid content created: Post ID #{post_id} (Zero icons/special characters)", "completed")
        return post_data

