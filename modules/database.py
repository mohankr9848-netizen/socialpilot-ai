
import streamlit as st
from supabase import create_client, Client


def client():
    url = st.secrets.get("SUPABASE_URL", "").rstrip("/")
    key = st.secrets.get("SUPABASE_ANON_KEY", "")

    if not url or not key:
        return None

    return create_client(url, key)


def user_client():
    db = client()

    if db is None:
        return None

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token:
        return None

    if refresh_token:
        response = db.auth.set_session(
            access_token,
            refresh_token
        )

        st.session_state.access_token = (
            response.session.access_token
        )
        st.session_state.refresh_token = (
            response.session.refresh_token
        )

    else:
        db.postgrest.auth(access_token)

    return db
