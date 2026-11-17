import streamlit as st
from supabase import create_client


def client():
    url = st.secrets.get('SUPABASE_URL', '')
    key = st.secrets.get('SUPABASE_ANON_KEY', '')
    if not url or not key:
        return None
    return create_client(url, key)


def user_client():
    db = client()
    if db and st.session_state.get('access_token'):
        db.postgrest.auth(st.session_state.access_token)
    return db
