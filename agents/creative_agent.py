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

    def generate_content_for_product(self, product: Dict[str, Any], post_type: str = "carousel", channel_niche: Optional[str] = None, channel_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        if "men" in category or "mens_fashion" in category or "mens" in title.lower() or ("shirt" in title.lower() and "women" not in title.lower()):
            hooks = [
                f"Spotted a really clean piece while checking deals today: {short_title}.",
                f"If you need versatile everyday shirts or sneakers, take a look at {short_title}.",
                f"Sharing a solid discount on {short_title} today."
            ]
            feature_summary = "The fabric blend is durable, comfortable for all-day wear, and holds shape well."
            use_case = "Great for office wear, weekend outings, or casual everyday layering."
            hashtags = "#mensfashion #menswear #menstyle #outfitideas #dailydeals #smartshopping"

        elif "saree" in title.lower() or "saree" in category:
            hooks = [
                f"Sharing a beautiful saree discovery today: {short_title}.",
                f"If you love traditional draping with a modern touch, take a look at {short_title}.",
                f"Found an elegant festive saree currently available on a great price drop: {short_title}."
            ]
            feature_summary = "The weave has a rich graceful sheen, the pallu border is delicately finished, and the fabric drapes effortlessly."
            use_case = "Perfect for weddings, festive celebrations, temple visits, and family ceremonies."
            hashtags = "#saree #sareelove #silksoftsaree #indiansaree #traditionalwear #festiveoutfit #elenasworld #dailydeals"

        elif "watch" in title.lower() or "jewellery" in title.lower() or "earring" in title.lower() or "necklace" in title.lower():
            hooks = [
                f"Sharing an elegant accessory piece today: {short_title}.",
                f"If you are looking for a classy watch or jewellery piece to elevate everyday outfits, here is {short_title}.",
                f"Found a very stylish ladies watch with a significant price cut: {short_title}."
            ]
            feature_summary = "The dial finish is subtle and refined, with a scratch-resistant build and comfortable wristband."
            use_case = "Complements both formal office wear and ethnic party outfits effortlessly."
            hashtags = "#watches #ladieswatch #jewellery #fashionaccessories #elegance #elenasworld #shoppingfinds"

        elif "beauty" in category or "skincare" in category or "serum" in title.lower() or "cream" in title.lower() or "sunscreen" in title.lower():
            hooks = [
                f"Sharing a verified skincare find that is currently on offer: {short_title}.",
                f"If you want healthy hydrated skin and a lightweight everyday routine, take a look at {short_title}.",
                f"Spotted a genuine discount on {short_title} today."
            ]
            feature_summary = "Lightweight formulation, absorbs quickly without feeling greasy, and dermatologically tested for daily skin nourishment."
            use_case = "Ideal for morning skincare prep, sun protection, and evening hydration rituals."
            hashtags = "#beauty #skincare #skincareroutine #glowingskin #selfcare #elenasworld #beautyfinds"

        elif "fashion" in category or "dress" in category or "kurta" in title.lower() or "kurti" in title.lower():
            hooks = [
                f"Found a really pretty option while checking deals today: {short_title}.",
                f"If you are looking for comfortable ethnic wear, take a look at {short_title}.",
                f"Sharing a nice outfit find that is currently on discount: {short_title}."
            ]
            feature_summary = "The fabric feels breathable and the stitching details look very neat in person."
            use_case = "Works nicely for festive gatherings, family functions, or everyday casual styling."
            hashtags = "#fashion #indianfashion #ethnicwear #kurtis #sarees #outfitideas #elenasworld #dailydeals"

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

        # 100% Humanoid Caption with Explicit Real Price (MRP) & Offer Price
        price_breakdown = f"""Price Details:
Real Price (MRP): Rs {orig_price}
Offer Deal Price: Rs {deal_price}
You Save: Flat {discount} percent off""" if orig_price > deal_price else f"Offer Price: Rs {deal_price}"

        prof_name = (channel_profile or {}).get("name", "").lower() if isinstance(channel_profile, dict) else ""
        brand_signoff = "Curated by Elena for Elena's World" if ("elena" in category or "saree" in category or "elena" in prof_name) else "Curated Deals Team"

        caption = f"""{headline}

{price_breakdown}

Rating: {rating} out of 5 based on verified buyer reviews.
Platform: {platform_name}

Highlights:
{feature_summary}
{use_case}

How to buy:
Comment LINK below and I will send the direct verified purchase link straight to your message inbox. You can also tap the link in bio to browse all featured items today.

{brand_signoff}

Disclosure: This post contains affiliate links. As an associate I earn from qualifying purchases.

{hashtags}
"""

        caption = clean_humanoid_text(caption)

        # 15-Second Clean Humanoid Reel Script with Avatar Visual Cues
        avatar_cue = "Elena wearing and showcasing the saree drape" if "saree" in title.lower() else ("Elena wearing the watch and showing wrist details" if "watch" in title.lower() else "Elena holding and showcasing the item")

        reel_script = f"""15-Second Video Script: {short_title}

Scene 1 (0 to 3 seconds):
Visual: {avatar_cue} with clean studio lighting.
Voiceover: "{headline}"
On-screen text: Real Price Rs {orig_price} | Offer Rs {deal_price}

Scene 2 (3 to 8 seconds):
Visual: Close-up on the fabric weave, dial, or product texture.
Voiceover: "Real price is {orig_price} rupees, but today it is on offer for just {deal_price} rupees. {feature_summary}"
On-screen text: Save {discount} percent

Scene 3 (8 to 12 seconds):
Visual: Highlighting product quality and certified buyer rating.
Voiceover: "It has a {rating} star rating from verified customers."
On-screen text: Rated {rating} out of 5

Scene 4 (12 to 15 seconds):
Visual: Elena smiling and prompting viewer to comment.
Voiceover: "Comment LINK below and I will message you the direct purchase link right away."
On-screen text: Comment LINK for Direct Order Link
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

