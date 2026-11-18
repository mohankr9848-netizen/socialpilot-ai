import re
from io import BytesIO
import streamlit as st
from PIL import Image
from modules.database import client, user_client
from modules.branding import extract_colors

st.set_page_config(page_title='SocialPilot AI', page_icon='📅', layout='wide')
st.title('SocialPilot AI')
st.caption('Your free social media marketing workspace — Phase 4.5')

if not client():
    st.info('Connect Supabase to begin. See README.md for the exact setup steps.')
    st.stop()

if 'access_token' not in st.session_state:
    tab_login, tab_register, tab_reset = st.tabs(['Log in', 'Create account', 'Reset password'])
    with tab_login:
        with st.form('login'):
            email = st.text_input('Email', key='login_email')
            password = st.text_input('Password', type='password', key='login_password')
            submit = st.form_submit_button('Log in')
        if submit:
            try:
                response = client().auth.sign_in_with_password({'email': email, 'password': password})
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                st.session_state.user_id = response.user.id
                st.rerun()
            except Exception:
                st.error('Login failed. Check your email, password, and email confirmation.')
    with tab_register:
        with st.form('register'):
            email = st.text_input('Email', key='register_email')
            password = st.text_input('Password (at least 8 characters)', type='password', key='register_password')
            submit = st.form_submit_button('Create account')
        if submit:
            if len(password) < 8:
                st.error('Choose a password of at least 8 characters.')
            else:
                try:
                    client().auth.sign_up({'email': email, 'password': password})
                    st.success('Account request submitted. Confirm your email if Supabase requires it, then log in.')
                except Exception:
                    st.error('Could not create account. Check Supabase authentication settings.')
    with tab_reset:
        email = st.text_input('Account email', key='reset_email')
        if st.button('Send reset email'):
            try:
                client().auth.reset_password_email(email)
                st.info('If the email is registered, a reset message will be sent. Complete password recovery through Supabase authentication.')
            except Exception:
                st.error('Could not request a reset email.')
    st.stop()

with st.sidebar:
    st.success('Signed in')
    section = st.radio('Navigation', ['Dashboard', 'Businesses', 'Website Research', 'Content Calendar', 'Creative Studio', 'Settings'])
    if st.button('Log out'):
        st.session_state.clear()
        st.rerun()

try:
    db = user_client()
    user_id = st.session_state.user_id
    businesses = db.table('businesses').select('*').eq('user_id', user_id).order('created_at', desc=True).execute().data
except Exception:
    st.error('Database request failed. Check your Supabase SQL migration and sign in again if your session has expired.')
    st.stop()

if section == 'Dashboard':
    st.subheader('Overview')
    a, b, c = st.columns(3)
    a.metric('Businesses', len(businesses))
    b.metric('Posts', 'Open Content Calendar')
    c.metric('Graphics', 'Open Creative Studio')
    st.info('Open Businesses in the sidebar to create your first brand profile.')
elif section == 'Businesses':
    from modules.product_intelligence import parse_product_lines
    st.subheader('Business profiles')
    st.caption('After creating a business, expand its profile to add any number of product/service URLs.')
    with st.expander('Add a new business', expanded=not bool(businesses)):
        with st.form('new_business'):
            name = st.text_input('Business name')
            website = st.text_input('Website URL (optional)')
            product_url = st.text_input('Product URL (optional)')
            description = st.text_area('Business description')
            product_description = st.text_area('Product description')
            industry = st.text_input('Industry')
            audience = st.text_area('Target audience')
            market = st.text_input('Geographic market')
            voice = st.selectbox('Brand voice', ['Professional', 'Friendly', 'Bold', 'Educational'])
            logo = st.file_uploader('Logo (PNG, JPG, WEBP; up to 2 MB)', type=['png', 'jpg', 'jpeg', 'webp'])
            save = st.form_submit_button('Save business')
        if save:
            if not name.strip():
                st.error('Business name is required.')
            elif website and not re.match(r'^https?://[^\s/]+', website):
                st.error('Website must begin with https:// or http://')
            else:
                try:
                    colors = ['#24468F', '#C62229']
                    logo_bytes = None
                    if logo:
                        logo_bytes = logo.getvalue()
                        if len(logo_bytes) > 2_000_000:
                            raise ValueError('Logo exceeds 2 MB')
                        im = Image.open(BytesIO(logo_bytes))
                        im.verify()
                        colors = extract_colors(logo_bytes)
                    record = {'user_id': user_id, 'name': name.strip(), 'website': website, 'product_url': product_url, 'description': description, 'product_description': product_description, 'industry': industry, 'audience': audience, 'market': market, 'voice': voice, 'colors': colors}
                    created = db.table('businesses').insert(record).execute().data[0]
                    if logo_bytes:
                        ext = 'png' if logo.type == 'image/png' else 'jpg' if logo.type == 'image/jpeg' else 'webp'
                        path = f'{user_id}/{created["id"]}.{ext}'
                        db.storage.from_('brand-logos').upload(path, logo_bytes, {'content-type': logo.type, 'upsert': 'true'})
                        db.table('businesses').update({'logo_path': path}).eq('id', created['id']).execute()
                    st.success('Business saved!')
                    st.rerun()
                except Exception as e:
                    st.error(f'Could not save business: {e}')
    for item in businesses:
        with st.expander(item['name']):
            with st.form('edit_' + item['id']):
                name = st.text_input('Business name', value=item['name'])
                website = st.text_input('Website URL', value=item.get('website') or '')
                description = st.text_area('Description', value=item.get('description') or '')
                audience = st.text_area('Target audience', value=item.get('audience') or '')
                colors = st.text_input('Brand colors (comma separated HEX)', value=', '.join(item.get('colors') or []))
                update = st.form_submit_button('Save changes')
            if update:
                try:
                    parsed = [v.strip().upper() for v in colors.split(',') if v.strip()]
                    if not parsed or any(not re.fullmatch(r'#[0-9A-F]{6}', v) for v in parsed):
                        st.error('Use HEX colors such as #24468F, #C62229')
                    else:
                        db.table('businesses').update({'name': name, 'website': website, 'description': description, 'audience': audience, 'colors': parsed}).eq('id', item['id']).eq('user_id', user_id).execute()
                        st.success('Updated')
                        st.rerun()
                except Exception:
                    st.error('Could not update business.')
            st.markdown('#### Product and service URLs')
            st.caption('One per line: Product name | https://example.com/product . You can add more URLs at any time.')
            url_lines = st.text_area('Add product/service URLs', key='product_urls_' + item['id'], placeholder='IconRadius | https://example.com/iconradius\nIconACS | https://example.com/iconacs', height=105)
            if st.button('Add product/service URLs', key='add_product_urls_' + item['id']):
                try:
                    entries = parse_product_lines(url_lines)
                    existing = db.table('business_products').select('url').eq('business_id',item['id']).eq('user_id',user_id).execute().data
                    existing_urls = {r['url'].rstrip('/').casefold() for r in existing}
                    records = [{'user_id':user_id,'business_id':item['id'], **e} for e in entries if e['url'].rstrip('/').casefold() not in existing_urls]
                    if records:
                        db.table('business_products').insert(records).execute()
                    st.success(f'Added {len(records)} new product/service URLs.')
                    st.rerun()
                except Exception as exc:
                    st.error(f'Could not add URLs: {exc}. Run database/004_phase45.sql first.')
            try:
                product_rows = db.table('business_products').select('*').eq('business_id',item['id']).eq('user_id',user_id).order('created_at').execute().data
                for pr in product_rows:
                    cols = st.columns([4,1])
                    cols[0].write(f"**{pr['name']}** — {pr['url']}")
                    if cols[1].button('Remove', key='rmprod_'+pr['id']):
                        db.table('business_products').delete().eq('id',pr['id']).eq('user_id',user_id).execute()
                        st.rerun()
            except Exception:
                st.info('Product URL storage will be available after running database/004_phase45.sql.')
            if item.get('logo_path'):
                try:
                    data = db.storage.from_('brand-logos').download(item['logo_path'])
                    st.image(data, width=180)
                except Exception:
                    st.warning('Logo could not be loaded.')
            st.write('Colors:', ', '.join(item.get('colors') or []))
            confirm = st.checkbox('Confirm deletion', key='confirm_' + item['id'])
            if st.button('Delete business', key='delete_' + item['id'], disabled=not confirm):
                try:
                    if item.get('logo_path'):
                        db.storage.from_('brand-logos').remove([item['logo_path']])
                    db.table('businesses').delete().eq('id', item['id']).eq('user_id', user_id).execute()
                    st.rerun()
                except Exception:
                    st.error('Could not delete business.')
elif section == 'Website Research':
    from modules.crawler import crawl_website
    from modules.ai_provider import get_provider
    st.subheader('Website Research & Business Intelligence')
    st.caption('Read public website pages and create an editable research profile. Website claims must be reviewed before use.')
    if not businesses:
        st.info('Create a business under Businesses first.')
        st.stop()
    business_map = {b['id']: b for b in businesses}
    business_id = st.selectbox('Choose business', list(business_map), format_func=lambda key: business_map[key]['name'])
    business = business_map[business_id]
    research_url = st.text_input('Website to research', value=business.get('website') or '', key='research_url_' + business_id)
    max_pages = st.slider('Maximum pages to inspect', 1, 8, 4)
    if st.button('Analyze Website', type='primary'):
        if not research_url.strip():
            st.error('Enter a public website URL. Add https:// at the beginning.')
        else:
            with st.spinner('Reading accessible public pages...'):
                try:
                    crawl = crawl_website(research_url, max_pages)
                    report = get_provider().generate(business, crawl)
                    st.session_state['research_draft_' + business_id] = {'website': research_url, **report}
                    if not crawl['pages']:
                        st.warning('No accessible pages found. You can still edit the research using the saved business details.')
                    else:
                        st.success(f"Read {len(crawl['pages'])} page(s). Review the report before saving.")
                except Exception as exc:
                    st.error(f'Website research could not complete: {exc}')
                    st.info('You can use your existing business details by clicking Generate from saved business details below.')
    st.markdown('#### Product and service page research')
    st.caption('Crawl one selected product URL at a time (one public HTML page). Review extracted information before approving it for calendar topics.')
    try:
        product_rows = db.table('business_products').select('*').eq('business_id',business_id).eq('user_id',user_id).order('created_at').execute().data
    except Exception:
        product_rows = []
        st.warning('Product research requires database/004_phase45.sql in Supabase.')
    if product_rows:
        selected_product = st.selectbox('Product/service to analyze', product_rows, format_func=lambda p: f"{p['name']} — {p['url']}", key='research_product')
        if st.button('Analyze selected product page'):
            from modules.product_intelligence import crawl_product
            try:
                with st.spinner('Reading the public product page...'):
                    facts = crawl_product(selected_product)
                    db.table('business_products').update({'facts': facts, 'approved': False}).eq('id',selected_product['id']).eq('user_id',user_id).execute()
                st.success('Product page analyzed. Review the extracted facts below and approve separately.')
                st.rerun()
            except Exception as exc:
                st.error(f'Could not analyze product URL: {exc}')
        facts = selected_product.get('facts') or {}
        if facts:
            st.write('Extracted source:', facts.get('source_url') or selected_product['url'])
            st.write('Page title:', facts.get('title') or '(not found)')
            st.write('Description:', facts.get('description') or '(not found)')
            st.write('Headings:', facts.get('headings') or [])
            for warning in facts.get('warnings', []):
                st.warning(warning)
            if st.button('Approve this product research for content planning', key='approve_prod_'+selected_product['id'], disabled=not bool(facts.get('source_url'))):
                db.table('business_products').update({'approved':True}).eq('id',selected_product['id']).eq('user_id',user_id).execute()
                st.success('Product research approved.')
                st.rerun()
            if selected_product.get('approved'):
                st.success('This product research is approved for calendar topics.')
    if st.button('Generate from saved business details'):
        st.session_state['research_draft_' + business_id] = {'website': research_url, **get_provider().generate(business, {'pages': [], 'warnings': ['No website pages were analyzed.']})}
    try:
        stored_rows = db.table('business_research').select('*').eq('business_id', business_id).eq('user_id', user_id).limit(1).execute().data
    except Exception:
        st.error('Research table unavailable. Run database/002_phase2.sql in Supabase SQL Editor first.')
        st.stop()

    stored = stored_rows[0] if stored_rows else None

    if st.session_state.pop('research_saved_' + business_id, False):
        st.success('Research profile saved successfully to Supabase!')

    draft = st.session_state.get('research_draft_' + business_id)
    if draft is None and stored:
        draft = {'website': stored['website'], 'facts': stored['facts'], 'suggestions': stored['suggestions'], 'warnings': stored.get('warnings') or []}
    if draft:
        st.markdown('#### Verified source material')
        st.caption('These are extracted snippets and URLs, not independently verified claims. Check the source pages.')
        facts = draft.get('facts', {})
        st.write('Pages:', ', '.join(facts.get('source_urls', [])) or 'None (manual business profile only)')
        with st.expander('Website headings, titles and descriptions'):
            st.json(facts)
        for warning in draft.get('warnings', []):
            st.warning(str(warning))
        st.markdown('#### Editable business intelligence profile')
        st.caption('Draft suggestions are not verified facts. Edit and approve them before using them in future content.')
        fields = [('business_overview', 'Business overview'), ('target_audience', 'Target audience'),
                  ('product_positioning', 'Product positioning'), ('unique_selling_propositions', 'Unique selling propositions'),
                  ('customer_pain_points', 'Customer pain points'), ('content_opportunities', 'Content opportunities'),
                  ('content_pillars', 'Recommended content pillars'), ('social_strategy', 'Suggested social strategy')]
        with st.form('research_edit_' + business_id):
            edits = {}
            for key, label in fields:
                edits[key] = st.text_area(label, value=draft.get('suggestions', {}).get(key, ''), height=90)
            approve = st.checkbox('I have reviewed this profile and approve it for future content planning', value=bool(stored and stored.get('approved')))
            save_research = st.form_submit_button('Save research profile')
        if save_research:
            record = {'user_id': user_id, 'business_id': business_id, 'website': draft['website'],
                      'facts': facts, 'suggestions': edits, 'warnings': draft.get('warnings', []), 'approved': approve}
            try:
                if stored:
                    db.table('business_research').update(record).eq('id', stored['id']).eq('user_id', user_id).execute()
                else:
                    db.table('business_research').insert(record).execute()
                st.session_state.pop('research_draft_' + business_id, None)
                st.session_state['research_saved_' + business_id] = True
                st.rerun()
            except Exception as exc:
                st.error(f'Could not save research profile: {exc}')
    else:
        st.info('Choose a business and analyze its website, or generate a profile from saved business details.')
elif section == 'Content Calendar':
    import calendar
    import csv
    from datetime import date
    from io import StringIO
    from modules.content_planner import make_plan, topic_sources, PLATFORMS, FORMATS

    st.subheader('Content Strategy & Monthly Calendar')
    st.caption('Business-aware offline planner: builds topics from your business details and approved website research. No AI API, automatic posting or invented product claims.')
    if not businesses:
        st.info('Create a business under Businesses first.')
        st.stop()
    business_map = {b['id']: b for b in businesses}
    business_id = st.selectbox('Business', list(business_map), format_func=lambda k: business_map[k]['name'], key='calendar_business')
    business = business_map[business_id]
    today = date.today()
    a, b = st.columns(2)
    with a:
        year = st.number_input('Year', min_value=2025, max_value=2100, value=today.year, step=1)
    with b:
        month = st.selectbox('Month', list(range(1,13)), index=today.month-1, format_func=lambda m: calendar.month_name[m])
    platforms = st.multiselect('Platforms', list(PLATFORMS), default=['LinkedIn','Instagram','Facebook'])
    frequency = st.slider('Posts per week (across all selected platforms)', 1, 7, 3)
    selected_formats = st.multiselect('Content formats to include', list(FORMATS), default=list(FORMATS), help='Mix videos, carousels, infographics, polls, text posts and more.')
    hour = st.selectbox('Draft posting hour (your intended local time)', list(range(24)), index=10, format_func=lambda h: f'{h:02d}:00')
    try:
        research_rows = db.table('business_research').select('suggestions,facts,approved').eq('business_id',business_id).eq('user_id',user_id).limit(1).execute().data
        research = research_rows[0] if research_rows and research_rows[0].get('approved') else None
    except Exception:
        research = None
    if research:
        st.success('Using your approved Phase 2 research profile.')
    else:
        st.warning('No approved research profile found. Drafts will use saved business details only.')
    try:
        approved_products = db.table('business_products').select('*').eq('business_id',business_id).eq('user_id',user_id).eq('approved',True).execute().data
    except Exception:
        approved_products = []
    if approved_products:
        st.success(f'Using {len(approved_products)} approved product/service research profiles.')
    sources = topic_sources(business, research, products=approved_products)
    st.markdown('#### Specific topics identified from your business')
    if sources:
        st.dataframe([{'Source': item['source'], 'Extracted topic': item['topic']} for item in sources], hide_index=True, use_container_width=True)
        st.caption('Source phrases are planning inputs, not independently verified product claims. To improve topics, edit product positioning and content opportunities in Website Research.')
    else:
        st.warning('No specific topics found. Add detailed product features, use cases and customer problems in Businesses or approved Website Research before generating.')
    draft_key = f'calendar_drafts_{business_id}_{year}_{month}'
    if st.button('Generate monthly draft calendar', type='primary'):
        try:
            st.session_state[draft_key] = make_plan(business, research, int(year), int(month), platforms, frequency, hour, products=approved_products, selected_formats=selected_formats)
            st.success('Draft calendar generated. Review before saving.')
        except Exception as exc:
            st.error(f'Could not generate drafts: {exc}')
    drafts = st.session_state.get(draft_key, [])
    if drafts:
        st.markdown('#### Generated drafts (not saved yet)')
        st.dataframe([{'Date':p['scheduled_date'],'Platform':p['platform'],'Topic':p['title'],'Format':p['content_type'], 'Product':(p.get('content_brief') or {}).get('product','')} for p in drafts], hide_index=True, use_container_width=True)
        with st.expander('Review and edit generated drafts', expanded=False):
            for i, p in enumerate(drafts):
                with st.form(f'draft_edit_{business_id}_{year}_{month}_{i}'):
                    st.markdown(f"**{p['scheduled_date']} · {p['platform']}**")
                    title = st.text_input('Title', p['title'])
                    caption = st.text_area('Caption', p['caption'])
                    hashtags = st.text_input('Hashtags', p['hashtags'])
                    graphic_prompt = st.text_area('Visual / production prompt', p['graphic_prompt'])
                    import json
                    brief_input = st.text_area('Production brief (editable JSON)', json.dumps(p.get('content_brief') or {}, indent=2), height=210)
                    if st.form_submit_button('Apply changes to this draft'):
                        try:
                            parsed_brief = json.loads(brief_input)
                            if not isinstance(parsed_brief, dict):
                                raise ValueError('Brief must be a JSON object')
                            p.update(title=title,caption=caption,hashtags=hashtags,graphic_prompt=graphic_prompt,content_brief=parsed_brief)
                            st.success('Draft updated locally.')
                        except (ValueError, TypeError) as exc:
                            st.error(f'Invalid production brief JSON: {exc}')
        if st.button('Save all drafts to Supabase'):
            try:
                records = [{'user_id':user_id,'business_id':business_id,**p} for p in drafts]
                db.table('content_posts').insert(records).execute()
                st.session_state.pop(draft_key,None)
                st.session_state['calendar_saved_notice'] = True
                st.rerun()
            except Exception as exc:
                st.error(f'Could not save calendar. Run database/003_phase3.sql first. Details: {exc}')
    if st.session_state.pop('calendar_saved_notice',False):
        st.success('Calendar drafts saved to Supabase!')
    try:
        start = f'{int(year):04d}-{int(month):02d}-01'
        end = f'{int(year)+1:04d}-01-01' if int(month)==12 else f'{int(year):04d}-{int(month)+1:02d}-01'
        posts = db.table('content_posts').select('*').eq('user_id',user_id).eq('business_id',business_id).gte('scheduled_date',start).lt('scheduled_date',end).order('scheduled_date').execute().data
    except Exception as exc:
        st.error(f'Content calendar table unavailable. Run database/003_phase3.sql. Details: {exc}')
        st.stop()
    st.markdown(f'#### Saved posts — {calendar.month_name[int(month)]} {year} ({len(posts)})')
    if posts:
        st.dataframe([{'Date':p['scheduled_date'],'Time':p['scheduled_time'],'Platform':p['platform'],'Format':p['content_type'],'Title':p['title'],'Status':p['status']} for p in posts], hide_index=True, use_container_width=True)
        csv_fields = ['scheduled_date','scheduled_time','platform','content_type','content_pillar','category','title','caption','hashtags','cta','graphic_prompt','content_brief','status']
        stream = StringIO()
        writer = csv.DictWriter(stream, fieldnames=csv_fields)
        writer.writeheader()
        for p in posts:
            import json
            writer.writerow({k:(json.dumps(p.get(k) or {}, ensure_ascii=False) if k=='content_brief' else p.get(k,'')) for k in csv_fields})
        st.download_button('Download saved posts as CSV', stream.getvalue().encode('utf-8-sig'), file_name=f'content_calendar_{year}_{int(month):02d}.csv', mime='text/csv')
        st.markdown('#### Edit, approve or delete a saved post')
        selected = st.selectbox('Choose a post', posts, format_func=lambda p:f"{p['scheduled_date']} | {p['platform']} | {p['title'][:65]}")
        st.markdown('#### Production brief for selected post')
        st.json(selected.get('content_brief') or {})
        with st.form('edit_saved_post'):
            title = st.text_input('Title', selected['title'])
            caption = st.text_area('Caption', selected['caption'],height=160)
            hashtags = st.text_input('Hashtags', selected['hashtags'])
            prompt = st.text_area('Visual / production prompt', selected['graphic_prompt'],height=130)
            import json
            brief_json = st.text_area('Editable production brief (JSON)', json.dumps(selected.get('content_brief') or {}, indent=2), height=240)
            status = st.selectbox('Review status', ['draft','approved'],index=1 if selected['status']=='approved' else 0)
            update = st.form_submit_button('Save post changes')
        if update:
            try:
                parsed_brief = json.loads(brief_json)
                if not isinstance(parsed_brief, dict):
                    raise ValueError('Production brief must be a JSON object')
                db.table('content_posts').update({'title':title,'caption':caption,'hashtags':hashtags,'graphic_prompt':prompt,'content_brief':parsed_brief,'status':status}).eq('id',selected['id']).eq('user_id',user_id).eq('business_id',business_id).execute()
                st.session_state['calendar_updated_notice'] = True
                st.rerun()
            except Exception as exc:
                st.error(f'Update failed: {exc}')
        if st.session_state.pop('calendar_updated_notice',False):
            st.success('Saved post updated.')
        confirm_delete = st.checkbox('Confirm deletion of selected saved post')
        if st.button('Delete selected post',disabled=not confirm_delete):
            try:
                db.table('content_posts').delete().eq('id',selected['id']).eq('user_id',user_id).eq('business_id',business_id).execute()
                st.rerun()
            except Exception as exc:
                st.error(f'Delete failed: {exc}')
    else:
        st.info('No saved posts for this month yet. Generate drafts above and save them.')
elif section == 'Creative Studio':
    from modules.creative_studio import SIZES, TEMPLATES, render_post, design_prompt, suggest_graphic_copy
    st.subheader('Creative Studio — Branded Social Graphics')
    st.caption('Generate free template graphics or optional AI artwork with Cloudflare Workers AI. No automatic publishing.')
    if not businesses:
        st.info('Add a business under Businesses first.')
        st.stop()
    business_map = {item['id']: item for item in businesses}
    business_id = st.selectbox('Business', list(business_map), format_func=lambda k: business_map[k]['name'], key='studio_business')
    business = business_map[business_id]
    try:
        saved_posts = db.table('content_posts').select('*').eq('user_id', user_id).eq('business_id', business_id).order('scheduled_date', desc=True).limit(250).execute().data
    except Exception as exc:
        st.error(f'Could not load calendar posts: {exc}')
        st.stop()
    if not saved_posts:
        st.info('Save at least one post in Content Calendar, then return to Creative Studio.')
        st.stop()
    post = st.selectbox('Choose a saved calendar post', saved_posts, format_func=lambda p: f"{p['scheduled_date']} · {p['platform']} · {p['title'][:70]}", key='studio_post')
    suggested_headline, suggested_subtitle = suggest_graphic_copy(post)
    left, right = st.columns(2)
    with left:
        template = st.selectbox('Design template', TEMPLATES)
        size_label = st.selectbox('Graphic size', list(SIZES))
    with right:
        headline = st.text_area('Graphic headline', value=suggested_headline, height=100, key=f"studio_head_{post['id']}")
        subtitle = st.text_input('Supporting line (optional)', value=suggested_subtitle, key=f"studio_sub_{post['id']}")
    st.caption('Review the headline and claims before publishing. AI creates the artwork only; the app adds exact text and logo.')
    from modules.cloudflare_ai import build_art_prompt, generate_artwork, compose_social_graphic, ImageGenerationError
    mode = st.radio('Graphic generation mode', ['AI artwork (Cloudflare free tier)', 'Free vector template'], horizontal=True)
    if mode == 'AI artwork (Cloudflare free tier)':
        styles = ['Clean editorial illustration', 'Professional realistic technology scene', 'Flat 2D vector infographic illustration', 'Modern product-inspired conceptual artwork']
        style = st.selectbox('AI artwork style', styles)
        steps = st.slider('Generation quality (steps)', 4, 8, 6)
        prompt_text = build_art_prompt(business, post, style)
        prompt_text = st.text_area('AI artwork prompt (editable)', prompt_text, height=175, key=f'ai_prompt_{post["id"]}_{style}')
        st.caption('Artwork only: no text or logo is generated by AI. One API call per click. Cloudflare Free plan quota applies.')
        credentials_ready = bool(st.secrets.get('CLOUDFLARE_ACCOUNT_ID') and st.secrets.get('CLOUDFLARE_API_TOKEN'))
        if not credentials_ready:
            st.warning('Cloudflare credentials missing. Add CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN to Streamlit Secrets.')
        if st.button('Generate AI artwork', disabled=not credentials_ready, type='primary'):
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            counter_key = f'cf_daily_count_{today}'
            # Session-local guard only: Cloudflare enforces the actual account quota.
            if st.session_state.get(counter_key, 0) >= 12:
                st.warning('This session has reached its safety limit of 12 requests today. Try again tomorrow or use the free template.')
            else:
                st.session_state[counter_key] = st.session_state.get(counter_key, 0) + 1
                with st.spinner('Generating artwork with Cloudflare Workers AI...'):
                    try:
                        artwork = generate_artwork(st.secrets['CLOUDFLARE_ACCOUNT_ID'], st.secrets['CLOUDFLARE_API_TOKEN'], prompt_text, steps=steps)
                        st.session_state['cf_artwork'] = artwork
                        st.session_state['cf_artwork_post'] = post['id']
                        st.success('AI artwork generated! Review the branded graphic below.')
                    except ImageGenerationError as exc:
                        st.error(str(exc))
        if st.session_state.get('cf_artwork_post') == post['id'] and st.session_state.get('cf_artwork') is not None:
            st.image(st.session_state['cf_artwork'], caption='Original AI artwork (without text or logo)', width=380)

    logo_bytes = None
    if business.get('logo_path'):
        try:
            logo_bytes = db.storage.from_('brand-logos').download(business['logo_path'])
        except Exception:
            st.warning('Could not load your saved logo. The graphic will use the business name instead.')
    try:
        if mode == 'AI artwork (Cloudflare free tier)' and st.session_state.get('cf_artwork_post') == post['id'] and st.session_state.get('cf_artwork') is not None:
            png = compose_social_graphic(st.session_state['cf_artwork'], business, post, SIZES[size_label], headline, subtitle, logo_bytes)
            label = 'Cloudflare AI artwork + branded overlay'
        else:
            png = render_post(business, post, template, SIZES[size_label], logo_bytes, headline, subtitle)
            label = f'{template} · Free template fallback'
        st.image(png, caption=f'{label} · {size_label}', width=500)
        st.download_button('Download graphic as PNG', png, file_name=f"socialpilot_{post['id'][:8]}_{SIZES[size_label][0]}x{SIZES[size_label][1]}.png", mime='image/png')
    except Exception as exc:
        st.error(f'Graphic rendering failed: {exc}')
    prompt = design_prompt(business, post, template, SIZES[size_label], headline, subtitle)
    st.markdown('#### Detailed image-generation prompt')
    st.code(prompt, language=None)
    st.download_button('Download design prompt as TXT', prompt.encode('utf-8'), file_name=f"socialpilot_prompt_{post['id'][:8]}.txt", mime='text/plain')
    st.info('Phase 4.3 generates graphics on demand. AI artwork is held in the current Streamlit session only, not stored in Supabase or automatically published. Cloudflare Free plan usage is enforced by Cloudflare.')
else:
    st.subheader('Settings')
    st.write('Phase 1 uses Supabase authentication and private business records.')
    st.caption('AI generation, social connections, and automatic publishing will be added in later phases.')
