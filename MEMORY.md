# AutoAffiliate AI — Project Memory & Architecture Context

## 1. System Overview
AutoAffiliate AI is an autonomous, multi-channel affiliate marketing, scraping, and social media publishing engine targeting Amazon India, Flipkart, and the EarnKaro network (150+ brands including Myntra & Nykaa).

- **Web Dashboard**: Local Streamlit application running on `http://localhost:8501`.
- **Database**: SQLite storage located at `data/autoaffiliate.db`.
- **Git Repository**: `https://github.com/tinku107/AutoAffiliate.git` on branch `main`.

---

## 2. Channel Profiles & Credentials
- **Active Channel**: `elenas_world` (Elena's World — Ladies Fashion & Beauty)
  - **Facebook Page ID**: `1484650751391885`
  - **Instagram Username**: `@affiliatem262` (`https://www.instagram.com/affiliatem262/`)
  - **Amazon Associate Tag**: `tinkukrishnan-21`
  - **EarnKaro User/API Key**: `5736594`
- **Other Available Channels**:
  - `fashion`: StyleDrop India (Ladies Fashion)
  - `electronics`: TechPulse India (Electronics & Mobiles)
  - `mens_fashion`: UrbanGent India (Men's Fashion & Shirts)
  - `general`: Mega Loot Deals (General Deals)

---

## 3. Strict Operating Rules
1. **100% Humanoid Content (Zero Emojis)**:
   - Captions, headline hooks, and reel scripts must never contain emojis or decorative icons.
   - Standard punctuation and plain conversational English only.
2. **Link Integrity**:
   - Amazon links must always use canonical format or official `amzn.to` short links. Never use TinyURL.
3. **Security & Credentials**:
   - All live secrets (`META_ACCESS_TOKEN`, `META_USER_TOKEN`, `OPENAI_API_KEY`, etc.) are isolated strictly in `.env`.
   - `.env` is permanently excluded by `.gitignore`. `config/settings.yaml` contains only sanitized metadata.

---

## 4. Key Modules & Implementations
- **Scraper (`tools/scraper.py`)**:
  - Scrapes Amazon India and Flipkart with dynamic failover.
  - `_extract_img_from_elem()` parses `data-a-dynamic-image`, `data-src`, and `srcset`, filtering out 1x1 tracking pixels (`grey-pixel.gif`).
- **Image Generation (`tools/image_generator.py`)**:
  - Generates 1080x1080 social media carousel slides.
  - Multi-tiered image fetching with fallback to avoid white screens.
  - Only paints white background when product photo is verified.
- **AI Virtual Try-On (`tools/avatar_tryon.py`)**:
  - Powered by OpenAI image generation (`gpt-image-1-mini`).
  - Generates 1024x1024 studio photoshoots of Elena wearing the scraped fashion item.
  - Integrated into the Sandbox UI under the `✨ Elena AI Try-On` tab.
- **Publisher (`agents/marketer_agent.py` & `tools/meta_api.py`)**:
  - Publishes to Facebook Page (`/{page_id}/photos` and `/{page_id}/feed`) and Instagram.
  - Verifies publication response before updating database status to prevent false `PUBLISHED` states.

---

## 5. Meta Publishing Requirement
- Live posting requires a Page Access Token for Elena's World with:
  - `pages_manage_posts`
  - `pages_read_engagement`
  - `instagram_content_publish`
  - `instagram_basic`
- If permissions are hidden in Graph API Explorer, the app must have the "Manage Pages" / "Business" use case added, or be created as a "Business" app type.
