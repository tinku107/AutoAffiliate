"""Content Creator Agent ('Creative').
Generates category-intelligent viral social media content:
Adapts copy dynamically for High-ticket Mobiles/iPhones, Fashion/Dresses, Toys, Kitchen, and Seasonal Festivals.
"""

import os
import random
from typing import Dict, Any, Optional, List
from tools.image_generator import ImageGenerator
from core.db import save_post, update_product_status, log_agent_action


class CreativeAgent:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.name = "Creative (Content Studio)"
        self.image_gen = ImageGenerator()
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")

    def generate_content_for_product(self, product: Dict[str, Any], post_type: str = "carousel") -> Dict[str, Any]:
        """Generates viral copy, reel script, hashtags, and promotional graphic for any product dynamically."""
        log_agent_action(self.name, f"Generating {post_type} content for: {product['title'][:35]}...", "started")

        # 1. Generate Promotional Image Graphic
        try:
            image_path = self.image_gen.generate_product_banner(product, banner_type="square")
            media_paths = [image_path]
        except Exception as e:
            log_agent_action(self.name, f"Image generation note: {e}", "warning")
            media_paths = [product.get("image_url", "")]

        title = product.get("title", "Featured Trending Find")
        deal_price = int(product.get("deal_price", 0))
        orig_price = int(product.get("original_price", 0))
        discount = int(product.get("discount_pct", 0))
        aff_url = product.get("affiliate_url", "")
        rating = product.get("rating", 4.4)
        reviews = product.get("reviews_count", 1200)
        category = product.get("category", "General").lower()

        # Dynamic Category-Specific Hooks & Copy
        short_title = title.split("(")[0].split("-")[0].strip()[:40]

        if "mobile" in category or "iphone" in title.lower() or deal_price > 20000:
            hooks = [
                f"🚨 Huge Price Drop on {short_title}! Deal alert 👇",
                f"Thinking of upgrading your phone? Look at this offer on {short_title} 📱",
                f"Never buy at full retail MRP! Huge discount live on {short_title} 🔥"
            ]
            feature_1 = "Premium flagship build & outstanding camera performance"
            feature_2 = "Huge exchange bonus and No Cost EMI options available"
            niche_tags = "#mobilesindia #smartphonedeals #techindia #appleindia #samsungindia #gadgetindia"
        elif "fashion" in category or "apparel" in category or "dress" in title.lower():
            hooks = [
                f"✨ Found the most aesthetic festival fit: {short_title}!",
                f"Obsessed with the styling on this! And it's currently on sale 👇",
                f"Outfit recommendation that looks expensive but is flat {discount}% off 😍"
            ]
            feature_1 = "Super comfortable premium breathable fabric & modern fit"
            feature_2 = "Perfect for parties, casual outings, and festive celebrations"
            niche_tags = "#fashionindia #outfitinspo #ethnicwear #festivelook #indianfashion #budgetfashion"
        elif "toy" in category or "kid" in title.lower():
            hooks = [
                f"🧸 The viral toy every kid (and adult!) is loving right now!",
                f"Best gift idea alert: {short_title} has flat {discount}% discount 🎁",
                f"Keeps them engaged for hours! Check out this top-rated find 👇"
            ]
            feature_1 = "100% child-safe, non-toxic durable build quality"
            feature_2 = "Boosts creativity, problem-solving, and hand-eye coordination"
            niche_tags = "#toysindia #kidsgifts #parentingindia #viraltoys #giftideasindia"
        else:
            hooks = [
                f"Wait… why did nobody tell me this {short_title} was on sale?! 🤯",
                f"Stop wasting money on overpriced items! Look at this top find 👇",
                f"Found the ultimate gamechanger: {short_title} (Flat {discount}% OFF) ⚡"
            ]
            feature_1 = "Clever problem-solving design with stellar customer ratings"
            feature_2 = "Durable, high utility, and verified verified buyer satisfaction"
            niche_tags = "#amazonfinds #amazonfindsindia #budgetdeals #dealsindia #smartshopping"

        headline = random.choice(hooks)

        # High-Converting Caption with Comment 'LINK' Funnel
        mrp_line = f" (MRP ₹{orig_price:,} - Flat {discount}% OFF)" if orig_price > deal_price else ""
        caption = f"""{headline}

Looking for the best deal online? This {short_title} is currently trending at an unbeatable price!

✨ Key Highlights:
• ⭐ Rated {rating} / 5.0 with {reviews:,}+ verified orders
• 🏷️ Deal Price: ₹{deal_price:,}{mrp_line}
• 📦 {feature_1}
• 🚚 {feature_2}

👇 HOW TO GET THE DIRECT LINK:
1. Comment "LINK" or "DEAL" below, and our bot will instantly DM you the verified purchase link!
2. OR Tap the link in our bio & stories before this offer expires!

⚠️ Price and stock can change anytime on the platform. Grab it now!

#ad #affiliate #dealalert #shoppingindia {niche_tags}
"""

        # 15-Second Viral Reel Script
        reel_script = f"""🎬 [15-SEC VIRAL REEL SCRIPT: {short_title}]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• [0:00 - 0:03] HOOK:
  Visual: Fast motion dramatic close-up or problem situation.
  Voiceover: "{headline}"
  On-Screen Text: "MASSIVE DEAL ALERT ⚡"

• [0:03 - 0:08] THE HIGHLIGHT:
  Visual: Demonstrating the product features smoothly.
  Voiceover: "This {short_title} is currently down to just ₹{deal_price:,}. {feature_1}."
  On-Screen Text: "NOW ₹{deal_price:,} (FLAT {discount}% OFF)"

• [0:08 - 0:12] SOCIAL PROOF:
  Visual: Showing the star rating and customer unboxing clip.
  Voiceover: "It has over {reviews:,} 5-star ratings and is selling out super fast!"
  On-Screen Text: "⭐ {rating}/5.0 RATED ({reviews:,}+ ORDERS)"

• [0:12 - 0:15] CALL TO ACTION:
  Visual: Pointing to comments with arrow graphic.
  Voiceover: "Comment 'LINK' right now and I will immediately DM you the direct discounted link!"
  On-Screen Text: "COMMENT 'LINK' FOR DIRECT DM 📩"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        post_data = {
            "product_id": product.get("id"),
            "platform": "instagram",
            "post_type": post_type,
            "headline": headline,
            "caption": caption,
            "hashtags": niche_tags,
            "reel_script": reel_script,
            "media_paths": media_paths,
            "affiliate_url": aff_url,
            "status": "draft"
        }

        # Save to DB
        post_id = save_post(post_data)
        post_data["id"] = post_id

        if product.get("id"):
            update_product_status(product["id"], "content_created")

        log_agent_action(self.name, f"Content created: Post ID #{post_id}", "completed")
        return post_data
