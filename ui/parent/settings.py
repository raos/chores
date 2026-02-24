import streamlit as st
from logic.auth import change_pin


def render_parent_settings():
    st.header("Settings")

    st.subheader("Change Parent PIN")
    with st.form("change_pin_form"):
        current = st.text_input("Current PIN", type="password", max_chars=10)
        new_pin = st.text_input("New PIN", type="password", max_chars=10)
        confirm = st.text_input("Confirm New PIN", type="password", max_chars=10)
        submitted = st.form_submit_button("Update PIN", type="primary")

        if submitted:
            if not current or not new_pin or not confirm:
                st.error("All fields are required.")
            elif new_pin != confirm:
                st.error("New PIN and confirmation do not match.")
            elif len(new_pin) < 4:
                st.error("PIN must be at least 4 characters.")
            elif change_pin(current, new_pin):
                st.success("PIN updated successfully.")
            else:
                st.error("Current PIN is incorrect.")
