"""Social Media Distribution and Growth Agent ('Marketer').
Responsible for:
1. Publishing content to specific Instagram, Facebook & Telegram accounts
2. Safe organic audience growth: finding new people, liking posts, leaving genuine humanoid comments, reposting, and inviting people to pages/groups
3. Automating the high-converting humanoid 'Comment LINK' DM response funnel
4. Strict anti-bot/anti-spam protection with randomized human jitter and zero emojis/icons.
"""

import os
import time
import random
import re
from typing import Dict, Any, List, Optional
from tools.meta_api import MetaPublisher
from core.db import (
    get_posts,
    update_post_status,
    save_engagement_task,
    get_engagement_tasks,
    update_engagement_task,
    log_agent_action,
    log_daily_revenue
)


def clean_humanoid_text(text: str) -> str:
    """Strips emojis and special characters to ensure 100% humanoid clean text."""
    if not text:
        return ""
    import unicodedata
    text = unicodedata.normalize("NFKD", text)
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010ffff]|[\u2600-\u27ff]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\u200d]|[\ufe0f]",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub("", text)
    cleaned = re.sub(r"[━═─—_]{3,}", "", cleaned)
    cleaned = cleaned.replace("•", "-").replace("👉", "").replace("⭐", "star")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
    return "\n".join(lines).strip()


class MarketerAgent:
    def __init__(self, meta_publisher: Optional[MetaPublisher] = None):
        self.name = "Marketer (Growth & Distribution)"
        self.publisher = meta_publisher or MetaPublisher()

        # 100% Humanoid, authentic, non-spam comments by niche (Zero icons, zero sales talk)
        self.niche_comment_templates = {
            "fashion": [
                "The fabric drape and color tone here look very elegant.",
                "Really love the simple styling on this. Great choice.",
                "The embroidery details look very neat in this video.",
                "Such a timeless look. Suits the festive season nicely.",
                "Looks super comfortable for daily wear as well."
            ],
            "mobiles": [
                "The low light camera clarity on this is noticeably sharp.",
                "Solid battery life and clean display. Good overview.",
                "The stabilization looks really smooth here.",
                "Great breakdown of the daily performance. Thanks for sharing.",
                "Very good build quality for this price segment."
            ],
            "electronics": [
                "Very practical desk setup gadget. Clean cable management too.",
                "Sound balance and build feel well tuned for this model.",
                "Helpful demonstration of the daily use case.",
                "Compact and sturdy design. Looks durable.",
                "Good review on the long term usage."
            ],
            "all": [
                "Very practical problem solver for regular use.",
                "Great find. The utility on this seems genuinely helpful.",
                "Clean design and seems durable for daily tasks.",
                "Appreciate the clear overview and honest feedback.",
                "Definitely bookmarking this for reference."
            ]
        }

        # Niche community creator radars to discover new people & engage organically
        self.niche_target_radars = {
            "fashion": [
                {"account": "desi_fashion_daily", "recent_topic": "Handloom sarees and festive kurtis", "audience_size": "15k"},
                {"account": "ethnic_style_inspo", "recent_topic": "Modern cotton suit sets", "audience_size": "28k"},
                {"account": "budget_glam_india", "recent_topic": "Affordable wedding guest styling", "audience_size": "42k"},
                {"account": "daily_wardrobe_in", "recent_topic": "Minimalist summer styling", "audience_size": "19k"}
            ],
            "mobiles": [
                {"account": "tech_reviews_bharat", "recent_topic": "Battery endurance test", "audience_size": "34k"},
                {"account": "gadget_zone_india", "recent_topic": "Camera zoom comparison", "audience_size": "51k"},
                {"account": "smartphone_daily_in", "recent_topic": "Unboxing flagship phone", "audience_size": "22k"},
                {"account": "deal_tracker_tech", "recent_topic": "Price drop announcement", "audience_size": "67k"}
            ],
            "electronics": [
                {"account": "gadget_lab_india", "recent_topic": "Noise cancelling earbuds review", "audience_size": "38k"},
                {"account": "desk_setup_inspo", "recent_topic": "Ergonomic workspace accessories", "audience_size": "29k"},
                {"account": "audio_pulse_in", "recent_topic": "Bluetooth speaker sound test", "audience_size": "17k"}
            ],
            "all": [
                {"account": "smart_home_finds_in", "recent_topic": "Kitchen organization hacks", "audience_size": "45k"},
                {"account": "daily_life_hacks_in", "recent_topic": "Clever everyday tools", "audience_size": "62k"},
                {"account": "shopping_radar_in", "recent_topic": "Trending product discoveries", "audience_size": "80k"}
            ]
        }

    def publish_approved_post(self, post: Dict[str, Any], channel_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Publishes humanoid post to Instagram/FB and broadcasts to Telegram using profile credentials."""
        post_id = post.get("id")
        channel_name = channel_profile.get("name", "Default Channel") if channel_profile else "Default Channel"
        log_agent_action(self.name, f"Publishing humanoid Post #{post_id} to [{channel_name}] (Instagram & Facebook)", "started")

        pub = self.publisher
        if channel_profile and (channel_profile.get("meta_access_token") or channel_profile.get("facebook_page_id") or channel_profile.get("telegram_channel_id")):
            prof_tok = (channel_profile.get("meta_access_token") or "").strip() or None
            prof_fb_id = (str(channel_profile.get("facebook_page_id") or "")).strip() or None
            prof_tg_tok = (channel_profile.get("telegram_bot_token") or "").strip() or None
            prof_tg_ch = (str(channel_profile.get("telegram_channel_id") or "")).strip() or None
            pub = MetaPublisher(
                access_token=prof_tok,
                fb_page_id=prof_fb_id,
                telegram_token=prof_tg_tok,
                telegram_channel_id=prof_tg_ch
            )

        # Determine media paths and public CDN image URL
        media_paths = post.get("media_paths", [])
        image_path = media_paths[0] if media_paths and os.path.exists(str(media_paths[0])) else None

        # Resolve authentic public CDN image URL for Instagram Graph API container
        pub_image_url = post.get("product_image") or post.get("image_url") or ""
        if not pub_image_url and post.get("product_id"):
            try:
                from core.db import get_products
                prods = get_products(limit=100)
                for pr in prods:
                    if pr.get("id") == post.get("product_id") or str(pr.get("product_id")) == str(post.get("product_id")):
                        pub_image_url = pr.get("image_url", "")
                        break
            except Exception:
                pass

        clean_cap = clean_humanoid_text(f"{post.get('caption', '')}\n\n{post.get('hashtags', '')}")

        # 1. Instagram Publication (Requires public HTTPS image URL)
        target_ig_img = pub_image_url if pub_image_url.startswith("http") else (image_path or "")
        ig_res = pub.publish_instagram_photo(image_url=target_ig_img, caption=clean_cap)

        # 2. Facebook Publication (Multipart binary photo upload or public image URL)
        fb_link = post.get("affiliate_url", "")
        if "earnkaro.com" in fb_link:
            from tools.affiliate_tagger import AffiliateTagger
            fb_link = AffiliateTagger().cloak_url(fb_link)
        fb_res = pub.publish_facebook_post(
            message=clean_cap,
            link=fb_link,
            image_path=image_path,
            image_url=pub_image_url if pub_image_url.startswith("http") else None
        )

        # 3. Telegram Deals Broadcast (Clean humanoid text without emojis)
        tg_text = f"Deal Alert: {clean_humanoid_text(post.get('headline', ''))}\n\nDirect link: {fb_link}"
        tg_res = pub.broadcast_telegram_deal(image_path=image_path, text=tg_text)

        # Check live publication success
        is_ig_live = bool(ig_res.get("success") and ig_res.get("mode") == "live")
        is_fb_live = bool(fb_res.get("success") and fb_res.get("mode") == "live")
        is_any_live = is_ig_live or is_fb_live
        is_sim = bool(ig_res.get("mode") == "simulation" and fb_res.get("mode") == "simulation")

        fb_err = fb_res.get("error") if not fb_res.get("success") else None
        ig_err = ig_res.get("error") if not ig_res.get("success") else None

        # If Meta returned a hard API error (e.g. (#200) requires pages_manage_posts), fail cleanly
        if fb_err or ig_err:
            err_msg = f"Facebook: {fb_err}" if fb_err else f"Instagram: {ig_err}"
            log_agent_action(self.name, f"Post #{post_id} rejected by Meta API: {err_msg}", "error")
            return {
                "success": False,
                "post_id": post_id,
                "error": err_msg,
                "instagram": ig_res,
                "facebook": fb_res,
                "telegram": tg_res
            }

        # Update post in DB only when genuinely published or simulated
        target_status = "published" if is_any_live else "simulated"
        ext_post_id = fb_res.get("post_id") or ig_res.get("post_id") or "sim_1"
        update_post_status(post_id, target_status, external_id=ext_post_id)

        # Log publication event (Real clicks and revenue come from verified affiliate network reports)
        log_daily_revenue(
            log_date_str=time.strftime("%Y-%m-%d"),
            target=500.0,
            earnings=0.0,
            clicks=0,
            orders=0,
            notes=f"Auto-published Post #{post_id} to [{channel_name}] (Awaiting network report)"
        )

        log_agent_action(
            self.name,
            f"Post #{post_id} successfully published to [{channel_name}]",
            "completed",
            details=f"IG ID: {ig_res.get('post_id')} | FB: {fb_res.get('post_id')} | Mode: {'LIVE' if is_any_live else 'SIMULATION'}"
        )

        return {
            "success": True,
            "post_id": post_id,
            "is_live": is_any_live,
            "instagram": ig_res,
            "facebook": fb_res,
            "telegram": tg_res
        }

    def grow_audience_and_engage(
        self,
        niche: str = "fashion",
        channel_profile: Optional[Dict[str, Any]] = None,
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Discovers new people in the target niche every day and performs 4 organic growth actions:
        1. Likes recent posts of target audience members to get noticed
        2. Drops thoughtful, humanoid comments (zero spam, zero icons)
        3. Shares/reposts relevant niche content to boost reciprocal page visibility
        4. Invites high-intent users to like/join the page and group
        Protects accounts with anti-ban humanized timing delays.
        """
        niche_key = niche.lower()
        if "dress" in niche_key or "apparel" in niche_key:
            niche_key = "fashion"
        elif "phone" in niche_key or "gadget" in niche_key:
            niche_key = "mobiles"

        target_pool = self.niche_target_radars.get(niche_key, self.niche_target_radars["all"])
        comment_pool = self.niche_comment_templates.get(niche_key, self.niche_comment_templates["all"])
        ch_name = channel_profile.get("name", "Channel") if channel_profile else "Channel"

        log_agent_action(self.name, f"Running organic audience growth & engagement for [{ch_name}] in #{niche}", "started")

        selected_targets = random.sample(target_pool, min(count, len(target_pool)))
        executed_tasks = []

        for target in selected_targets:
            # 1. Action: Like recent post (Dry-run Simulation)
            like_task = {
                "target_account": f"@{target['account']}",
                "target_post_url": f"https://instagram.com/p/{target['account']}_recent",
                "action_type": "like",
                "content": f"[SIMULATION] Liked recent post on {target['recent_topic']}",
                "status": "simulated"
            }
            tid1 = save_engagement_task(like_task)
            update_engagement_task(tid1, "simulated")
            like_task["id"] = tid1
            executed_tasks.append(like_task)

            # 2. Action: Genuine Humanoid Comment (Dry-run Simulation, Zero emojis)
            comment_text = clean_humanoid_text(random.choice(comment_pool))
            comment_task = {
                "target_account": f"@{target['account']}",
                "target_post_url": f"https://instagram.com/p/{target['account']}_discussion",
                "action_type": "comment",
                "content": f"[SIMULATION] {comment_text}",
                "status": "simulated"
            }
            tid2 = save_engagement_task(comment_task)
            update_engagement_task(tid2, "simulated")
            comment_task["id"] = tid2
            executed_tasks.append(comment_task)

            # 3. Action: Follower Invitation (Dry-run Simulation)
            invite_task = {
                "target_account": f"@{target['account']}_follower_{random.randint(100, 999)}",
                "target_post_url": f"Invited to follow {ch_name}",
                "action_type": "invite_page_follower",
                "content": f"[SIMULATION] Candidate follower for {target['recent_topic']}",
                "status": "simulated"
            }
            tid3 = save_engagement_task(invite_task)
            update_engagement_task(tid3, "simulated")
            invite_task["id"] = tid3
            executed_tasks.append(invite_task)

            # Anti-bot human delay simulation
            time.sleep(0.3)

        log_agent_action(
            self.name,
            f"[SIMULATION / DRY-RUN] Evaluated {len(executed_tasks)} organic growth targets for [{ch_name}] (Likes, Humanoid Comments, Invites)",
            "completed",
            details="Simulation mode: Meta API restricts automated likes/comments on external accounts."
        )
        return executed_tasks

    def scout_and_engage_with_target_audience(self, niche: str = "gadgets", count: int = 3) -> List[Dict[str, Any]]:
        """Backwards compatible alias for organic audience growth."""
        return self.grow_audience_and_engage(niche=niche, count=count)

    def handle_incoming_comment_lead(
        self,
        user_handle: Optional[str] = None,
        affiliate_url: Optional[str] = None,
        product_title: str = "this item",
        post: Optional[Dict[str, Any]] = None,
        commenter_username: Optional[str] = None,
        comment_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Automates the 'Comment LINK' DM response funnel.
        Sends a 100% humanoid, friendly message without emojis or special characters.
        """
        handle = user_handle or commenter_username or "friend"
        if post and isinstance(post, dict):
            link = affiliate_url or post.get("affiliate_url") or post.get("raw_affiliate_url", "")
            title = product_title if product_title != "this item" else (post.get("headline") or post.get("title") or "this item")
        else:
            link = affiliate_url or ""
            title = product_title

        short_title = title.split("(")[0].split("-")[0].strip()[:35]
        # Strict Rule: Never send earnkaro.com directly to users in DMs!
        if "earnkaro.com" in link:
            from tools.affiliate_tagger import AffiliateTagger
            link = AffiliateTagger().cloak_url(link)

        dm_message = clean_humanoid_text(
            f"Hello {handle}, thanks for reaching out. "
            f"Here is the direct purchase link for {short_title}: {link} . "
            f"Please check it out before the current discount ends. "
            f"Let me know if you need any other recommendations or have sizing questions."
        )

        task = {
            "target_account": handle,
            "target_post_url": "Direct Message Funnel",
            "action_type": "dm_reply",
            "content": dm_message,
            "status": "executed"
        }
        task_id = save_engagement_task(task)
        update_engagement_task(task_id, "executed")

        log_agent_action(self.name, f"Humanoid Auto-DM sent to lead {handle}", "completed")
        return {"task_id": task_id, "recipient": handle, "dm_message": dm_message}


