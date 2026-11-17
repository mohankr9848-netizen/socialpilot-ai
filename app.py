import re
from io import BytesIO
import streamlit as st
from PIL import Image
from modules.database import client, user_client
from modules.branding import extract_colors

st.set_page_config(page_title='SocialPilot AI', page_icon='📅', layout='wide')
st.title('SocialPilot AI')
st.caption('Your free social media marketing workspace — Phase 1')

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
    section = st.radio('Navigation', ['Dashboard', 'Businesses', 'Settings'])
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
    b.metric('Posts', 'Coming in Phase 3')
    c.metric('Graphics', 'Coming in Phase 4')
    st.info('Open Businesses in the sidebar to create your first brand profile.')
elif section == 'Businesses':
    st.subheader('Business profiles')
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
else:
    st.subheader('Settings')
    st.write('Phase 1 uses Supabase authentication and private business records.')
    st.caption('AI generation, social connections, and automatic publishing will be added in later phases.')
