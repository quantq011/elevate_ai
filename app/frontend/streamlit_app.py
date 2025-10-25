# frontend/streamlit_app.py
import requests
import streamlit as st

st.set_page_config(page_title="Onboarding Assistant", page_icon="👋")

BACKEND = "http://localhost:8000"

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
    resp = requests.post(f"{BACKEND}/chat", json={"message": prompt})
    data = resp.json()
    answer = data.get("answer", "No response")
    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.history.append(("assistant", answer))


st.sidebar.header("Chroma DB (dev)")
if st.sidebar.button("Seed mock Chroma data"):
    try:
        resp = requests.post(f"{BACKEND}/chroma/seed", json={})
        res = resp.json()
        st.sidebar.write(res)
        # add assistant message confirming seed
        msg = f"Chroma seed: {res}"
        st.session_state.history.append(("assistant", msg))
        with st.chat_message("assistant"):
            st.markdown(msg)
    except Exception as e:
        st.sidebar.error(str(e))

st.sidebar.markdown("---")
q = st.sidebar.text_input("Chroma search", "how do i request it access")
top_k = st.sidebar.slider("Top K", 1, 10, 5)
if st.sidebar.button("Search Chroma"):
    try:
        resp = requests.get(f"{BACKEND}/chroma/search", params={"q": q, "top_k": top_k})
        data = resp.json()
        if data.get("error"):
            st.sidebar.error(data.get("error"))
        else:
            hits = data.get("results", [])
            if not hits:
                msg = "No Chroma hits found."
                st.session_state.history.append(("assistant", msg))
                with st.chat_message("assistant"):
                    st.markdown(msg)
            else:
                # build markdown message
                md = "### Chroma search results\n"
                for h in hits:
                    md += f"**id:** {h.get('id')}  \n"
                    md += f"**score:** {h.get('score')}  \n"
                    md += f"{h.get('document')}\n\n---\n\n"
                st.session_state.history.append(("assistant", md))
                with st.chat_message("assistant"):
                    st.markdown(md)
    except Exception as e:
        st.sidebar.error(str(e))
