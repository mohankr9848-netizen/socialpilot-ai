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
