# frontend/streamlit_app.py
import requests
import streamlit as st

st.set_page_config(page_title="Onboarding Assistant", page_icon="👋")

BACKEND = "http://localhost:8000/chat"

if "history" not in st.session_state:
    st.session_state.history = []

st.title("👋 Onboarding Assistant")

# Hiển thị hội thoại cũ
for role, content in st.session_state.history:
    with st.chat_message(role):
        st.markdown(content)

prompt = st.chat_input("Ask about new-hire processes, policies, tasks…")
if prompt:
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # gọi backend
    resp = requests.post(BACKEND, json={"message": prompt})
    data = resp.json()
    answer = data.get("answer", "No response")
    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.history.append(("assistant", answer))
