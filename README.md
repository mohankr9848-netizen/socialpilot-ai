# SocialPilot AI — Phase 1

This is a **working starter**, not the full platform. Phase 1 includes Supabase email authentication, private business profiles, logo uploads, automatic color extraction, manual color editing, and a simple dashboard. It does **not** yet generate posts, graphics, or publish to social accounts.

## Beginner setup (no local coding required)

1. Create a free account at https://github.com and a **private** repository named `socialpilot-ai`.
2. Unzip this download. In your GitHub repository click **Add file → Upload files**. Upload the project contents, preserving folders (you can drag the unzipped folder contents). Commit the files. Never upload actual secret keys.
3. At https://supabase.com create a project on an available free plan. In **SQL Editor → New query**, paste the entire contents of `database/001_phase1.sql` and click **Run** once. This creates the table, security policies and private logo bucket.
4. In Supabase open **Project Settings → API** (or the current **Connect / API Keys** screen). Copy the **Project URL** and **publishable/anon key**, NOT the service-role or secret key.
5. In Supabase **Authentication → Providers → Email**, ensure email login is enabled. Email confirmation may be required; use a real email address.
6. Visit https://share.streamlit.io and sign in with GitHub. Choose **Create app → Deploy a public app from GitHub**, select your repository, branch `main`, and main file path `app.py`.
7. In Streamlit deployment **Advanced settings → Secrets**, paste the following with your real values:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_PUBLISHABLE_OR_ANON_KEY"
```

8. Click **Deploy**. Once running, register, confirm email if required, log in, and create a business.
9. To test security, register a second account and confirm that it cannot see the first account's business records.

**Important:** Streamlit Community Cloud public apps may be visible to others; use private GitHub code and never upload confidential marketing data until access and security have been reviewed. Streamlit app deployment and Supabase free-tier quotas/availability can change. This is an educational MVP, not yet security-audited production software. Password reset is a basic email request; full in-app recovery and automatic session refresh remain future hardening tasks.

## Optional local run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your own keys
streamlit run app.py
```

## Tests

```bash
python -m pytest -q
```

## Phase checklist

- [x] Streamlit app and navigation
- [x] Supabase email sign-up/sign-in and logout
- [x] Private business records and private logo bucket
- [x] Logo color extraction and manual color edits
- [ ] Full password recovery and session-refresh hardening
- [ ] Website research
- [ ] Monthly content generation
- [ ] Branded graphics and ZIP exports
- [ ] Social OAuth and scheduled publishing

## Phase 2: Website Research (upgrade from your working Phase 1)

**Before upgrading:** Keep your current Streamlit secrets as-is. Never upload secrets or a `venv` folder to GitHub. Back up your existing repository first.

1. In Supabase open your existing `socialpilot-ai` project → **SQL Editor → New query**.
2. Paste **all** of `database/002_phase2.sql` and click **Run**. Expect `Success. No rows returned`.
3. In GitHub, upload the Phase 2 project files **into the root of your existing `socialpilot-ai` repository**, preserving folders and replacing existing files. Do not create a nested `socialpilot-ai` folder. Upload **only** files in this ZIP (do not upload a Python `venv` directory). Commit to `main`.
4. Streamlit Community Cloud will redeploy after the commit. If necessary use **Manage app → Reboot app**.
5. Sign in → **Website Research** → select a business → enter a public website with `https://` → **Analyze Website**.
6. Check extracted website headings and source URLs. Edit the research fields, check approval, then **Save research profile**.
7. If crawling fails, click **Generate from saved business details** and manually edit the profile.

### Scope and limitations
- Free rule-based analysis works without an external AI API. `modules/ai_provider.py` defines a provider interface; this release does **not** run an LLM or generate novel AI content.
- Crawler respects robots.txt, limits pages and bytes, and rejects private/reserved hostname resolutions. Only analyze websites you are permitted to access. Public pages can block automated traffic.
- Some sites render content in JavaScript; this crawler cannot read content that only appears after browser execution.
- For production deployment, consider egress-level blocking of private networks and DNS rebinding defenses in addition to application checks.
- Research is private per user via Supabase RLS. All extracted text is treated as untrusted and should be reviewed.
- Existing Phase 1 business records are preserved. Phase 3 will consume the approved research profiles.


## Phase 3 — Content Strategy & Monthly Calendar

**Install:** Upload/replace the project files in your existing GitHub repository, preserving paths. In your EXISTING Supabase project, run `database/003_phase3.sql` in SQL Editor once. Streamlit Cloud will redeploy from `main`. Your existing Secrets remain unchanged. Do not rerun Phase 1/2 migrations or delete existing tables.

**Use:** Log in → Content Calendar → choose business and month → choose platforms and posts/week → Generate monthly draft calendar → review → Save all drafts to Supabase. You can edit/approve/delete saved posts and download a UTF-8 CSV (Excel-compatible).

**Important:** Generation is a **deterministic, offline template-based drafting engine**, not an LLM. It uses approved Phase 2 research if available, otherwise saved business details. Content is a starting point, not fact-checked, and must be reviewed. Dates/times are draft planning fields only: nothing is connected to social media, published, or scheduled automatically. CSV is export, not direct Excel .xlsx. Repeated saves create additional posts; use the saved-post editor to manage duplicates. Graphics are prompts only; image creation comes in Phase 4. No paid API keys needed.

**Tests:** `python -m pytest tests -q`. Keep your Streamlit Supabase secrets in Cloud Secrets, never in GitHub.

## Phase 3 business-aware upgrade (no AI API)

This version uses your saved business product description and **approved** Phase 2 research, including website headings, titles, descriptions, positioning, content opportunities and customer pain points. It prioritizes specific phrases over generic content pillars. The Content Calendar page shows exactly which source phrases were found.

If you see **No specific product or website topics found**, open Businesses or Website Research and provide one product/feature/use-case per line, approve and save the research, then regenerate. Research is a planning input; review every generated claim before publishing.

**Upgrade instructions:** Replace `app.py`, `modules/content_planner.py`, `README.md`, and `tests/test_content_planner.py`; add `tests/test_business_aware_planner.py`. Other files remain unchanged. **Do not run a new SQL migration**: the existing `database/003_phase3.sql` table is compatible. Existing saved posts are retained. New drafts are created only when you click Generate; saved posts are not automatically rewritten.

This deterministic, offline approach can tailor topics to available information but cannot independently understand or verify product claims like a generative AI model. For best output, enter concise specific product features, pain points, and audience roles in the research profile.

## Phase 4 — Creative Studio (no paid API)

1. Upload the updated `app.py`, `modules/creative_studio.py`, `tests/test_creative_studio.py`, and `README.md` to GitHub, preserving paths.
2. Streamlit redeploys automatically. **No new Supabase SQL is required**; this phase reads existing `businesses` and `content_posts` records and the existing private `brand-logos` bucket.
3. Sign in, open **Creative Studio**, choose a business and a previously saved calendar post, choose a template and canvas size, edit the graphic headline, then download the PNG or design prompt.
4. Four offline templates and four canvas sizes are available. Generated graphics are not stored in Supabase, and the app does not generate photorealistic AI art or publish to social networks.
5. Run `python -m pytest -q` to test the project.

Fonts are loaded from the Streamlit Linux host when available; Pillow's fallback font is used if missing. For production typography consistency, install a redistributable font yourself (do not commit proprietary fonts).

## Phase 4.1 — Creative Studio visual redesign

Replace only `modules/creative_studio.py`, `README.md`, and `tests/test_creative_studio.py` in your existing GitHub repository. No new SQL, API keys, or dependency changes. The offline Pillow renderer now uses larger responsive typography, four distinct layouts, topic-aware network/finance/workflow diagrams, logo support, and full-resolution PNG export. Diagrams are rule-based illustrations, not generative AI artwork. Check all headlines and claims before publishing.


## Phase 4.2: Smart Creative Design Engine

The Creative Studio now proposes a concise headline and supporting line for every saved post. You can edit either before generating. Four templates have larger typography, stronger topic-specific flat illustrations, brand colors and logo support. All rendering is offline with Pillow; no AI API, migration or new package required. Rules are intentionally conservative: check final copy before publication.

## Phase 4.3 — Cloudflare Workers AI (optional, free tier)

Creative Studio now offers **AI artwork (Cloudflare free tier)** and the original **Free vector template** fallback. AI generation uses `@cf/black-forest-labs/flux-1-schnell` via the Cloudflare REST API. It creates an illustration, while Pillow adds exact headlines and the original uploaded logo for better legibility and brand fidelity. The image is held only in the current Streamlit session; use the PNG download to save it.

Add these to **Streamlit Community Cloud → App settings → Secrets** (keep your existing Supabase settings):

```toml
CLOUDFLARE_ACCOUNT_ID = "your-cloudflare-account-id"
CLOUDFLARE_API_TOKEN = "your-workers-ai-api-token"
```

Do **not** commit real credentials to GitHub. Your Cloudflare token needs permission to run Workers AI. Keep the Cloudflare **Workers Free** plan; do not upgrade to Paid if your budget must remain ₹0. Cloudflare enforces its daily allowance; the app also has a modest **12 attempts per UTC day per browser session** guard, which is *not* a global quota. For the authoritative allowance and eligibility, consult Cloudflare's pricing dashboard: https://developers.cloudflare.com/workers-ai/platform/pricing/

Select a saved post → Creative Studio → AI artwork → choose style → **Generate AI artwork** → review the composed branded preview → download PNG. On API errors, select the Free vector template. Regenerating uses another Cloudflare inference. No database migration is needed.

For privacy, remember that prompts (business descriptions, post title, and creative brief) are sent to Cloudflare for generation. Avoid inserting confidential business details.

---

## Phase 4.5 — Product intelligence and multi-format content calendar

**Run the new migration before opening the upgraded app:** Supabase SQL Editor → paste `database/004_phase45.sql` → Run. Do not rerun or delete older tables. This adds `business_products` (protected by user-specific RLS policies) and the optional `content_brief` JSON column on existing `content_posts`; it does not delete existing businesses, research or posts.

**Add product URLs:** Businesses → expand a saved business → Product and service URLs → enter one item per line, e.g. `IconACS | https://example.org/products/iconacs`, then **Add product/service URLs**. Add as many as needed in separate batches. URLs must be publicly reachable HTTP(S) addresses; private and local networks are blocked by the crawler. The existing single `product_url` field remains for backward compatibility.

**Research each product:** Website Research → select the business → choose a product URL → **Analyze selected product page**. The crawler reads at most one HTML page per click, checks robots.txt and applies request/time/size restrictions. It does not access private pages or automatically bypass blocked websites. Review the extracted title, meta description and headings. **Approve this product research for content planning** only when you have verified the information. Re-analyzing clears approval until reviewed again. The original source URL is retained.

**Generate multi-format content:** Content Calendar → choose business, platforms, posting frequency and any combination of the ten content formats → Generate monthly draft calendar. Approved product research is prioritized over broad website research. Each post includes a structured `content_brief`: slide-by-slide carousel outlines, infographic sections, video scenes and voiceover suggestions, poll options, story frames, document outlines, or image direction. Edit these briefs as JSON before or after saving; download them in CSV. The existing Creative Studio remains focused on static artwork; it does not render final videos or carousel pages automatically.

**Cost:** All new content generation is deterministic and does not call a paid AI API. Public site crawling consumes network resources and can fail due to robots.txt, firewalls, or hosting limits. No guarantee of unlimited crawling on free hosting.

**Testing:** Run `python -m pytest -q` in the repository. The Cloudflare integration and Streamlit secrets remain unchanged.
