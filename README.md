# AutoAffiliate AI 🚀
### Autonomous Multi-Agent Referral Income Engine

AutoAffiliate AI is an autonomous, multi-agent business operations team designed to discover trending, high-discount products on Amazon India and Flipkart, craft viral social media content (promotional graphic banners, 15-second Reels scripts, and high-converting captions), publish to Instagram & Facebook, and engage with prospective buyers organically to reach a target of **₹500+/day affiliate revenue within 14 days**.

---

## 🤖 Meet Your AI Employee Team

1. **🔍 Scout Bot (Product Hunter)**:
   - Scans Amazon India Best Sellers, Movers & Shakers, and Flipkart deals.
   - Filters for viral impulse purchases under ₹999 with 40%+ real discounts.
   - Automatically tags all links with your Amazon Associate tag or EarnKaro tracking ID.
   - Calculates commission ROI and units needed to hit your daily ₹500 goal.

2. **🎨 Creative Bot (Content Studio & Video Engine)**:
   - **AI Video Generator**: Generates 9:16 vertical MP4 video Reels with animated product motion, discount tags, price drops, and **neural Indian English voiceover narration** (via edge-tts & bundled ffmpeg).
   - **Graphic Studio**: Designs Instagram-ready 1080x1080 promotional graphics with discount badges and price tags using Pillow.
   - **Viral Copy & Funnels**: Writes psychological hooks, Indian audience captions, 25+ hashtags, and automates the **Comment "LINK" for DM** conversion funnel.

3. **🚀 Marketer Bot (Distribution & Growth Radar)**:
   - Safely publishes posts to Instagram Business Accounts and Facebook Pages via Meta Graph API.
   - Mirrors top deals to Telegram channels (proven 5x conversion rate in India).
   - Runs an anti-ban growth radar: discovers niche accounts and engages with authentic, human-like comments.
   - Automates direct message delivery when prospects comment "LINK" or "PRICE".

4. **⚡ Grok Command Console (Orchestrator)**:
   - Dark-mode Grok-style chat terminal to command all bots with plain English.
   - One-click shortcuts: "Run Full Autopilot", "Scout Top Deals", "Generate Posts", "Engage Audience".
   - Tracks daily progress towards your ₹500/day milestone.

---

## 🚀 Quick Start Guide

### 1. Launch the Application
Simply double-click `run.bat` or run:
```powershell
python -m streamlit run ui\app.py
```
Open your browser at `http://localhost:8501`.

### 2. Configure Your Affiliate Tag
Edit `config/settings.yaml` or create a `.env` file (see `.env.example`):
```ini
# Your Amazon India Associate Tag
AMAZON_ASSOCIATE_TAG=yourtag-21

# Optional Meta API (for automated Instagram & Facebook publishing)
META_ACCESS_TOKEN=your_token_here
INSTAGRAM_ACCOUNT_ID=your_ig_id
META_PAGE_ID=your_fb_page_id

# Optional Telegram Deals Channel (instant traffic boost)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel_username
```

*(Note: The system includes a full dry-run simulation mode, so you can test and operate immediately even before your Meta API tokens are generated!)*

---

## 🎯 Proven 14-Day Roadmap to ₹500/Day Minimum

To hit ₹500/day in India, you need approximately **10 to 12 sales per day** of ₹499 - ₹999 gadgets (at 8-9% commission = ~₹40 - ₹80 per sale):

- **Days 1 - 3 (Setup & Seeding)**:
  - Run Scout Bot to discover 5 top problem-solving gadgets under ₹499.
  - Generate and post 2 Reels + 1 Carousel post daily.
  - Setup a free Telegram channel ("Daily Loot Deals India") and place the link in your Instagram bio.
- **Days 4 - 8 (Lead Funnel Activation)**:
  - Add the **"Comment LINK for direct discount link"** CTA on every post.
  - When users comment, our Marketer Bot instantly DMs the affiliate link.
  - Run the Audience Radar to safely engage with 10-15 community posts daily during peak Indian shopping hours (12:30 PM & 8:30 PM IST).
- **Days 9 - 14 (Scaling to ₹500+/day)**:
  - Post 3 times a day.
  - Double down on the 2 products that generated the most link clicks.
  - Broadcast flash sales and lightning deals to your Telegram channel for instant conversions.

---

## 📁 System Architecture

```
c:/AI/My Business Agents/
├── config/
│   ├── settings.yaml          # System configuration & niche settings
│   └── .env.example           # Credentials template
├── core/
│   ├── orchestrator.py        # Grok-style command router & workflow engine
│   └── db.py                  # Local SQLite database (deals, posts, revenue, logs)
├── agents/
│   ├── scout_agent.py         # Product Hunter (Amazon & Flipkart)
│   ├── creative_agent.py      # Content & Graphic Studio
│   └── marketer_agent.py      # Meta Publisher, Growth Radar & Auto-DM
├── tools/
│   ├── scraper.py             # Product metadata & deals scraper
│   ├── image_generator.py     # Pillow 1080x1080 banner creator
│   ├── affiliate_tagger.py    # URL cleaner & Associate tag injector
│   └── meta_api.py            # Instagram, Facebook & Telegram API client
├── ui/
│   └── app.py                 # Streamlit Grok-style command console
├── data/
│   ├── autoaffiliate.db       # Persistent SQLite database
│   └── generated_images/      # Auto-generated social media graphics
├── requirements.txt           # Python dependencies
└── run.bat                    # 1-click Windows launcher
```
