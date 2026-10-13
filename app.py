import streamlit as st

st.set_page_config(page_title="Streamlit Placeholder", page_icon="🧪")

st.title("🧪 Streamlit Placeholder")
st.write("This app is a placeholder for testing. Nothing to see here yet.")

name = st.text_input("Your name", placeholder="Type something…")
if st.button("Say hello"):
    st.success(f"Hello, {name or 'world'}!")
