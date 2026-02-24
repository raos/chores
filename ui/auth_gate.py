import streamlit as st
from db.queries.children import list_children
from logic.auth import verify_pin, logout


def render_auth_gate():
    if "role" not in st.session_state:
        st.session_state.role = None
        st.session_state.child_id = None
        st.session_state.pin_verified = False

    role = st.session_state.get("role")

    with st.sidebar:
        st.title("Family Chores")
        st.divider()

        if role is not None:
            if role == "parent":
                st.success("Logged in as Parent")
            else:
                children = list_children()
                child = next((c for c in children if c["id"] == st.session_state.child_id), None)
                name = child["name"] if child else "Child"
                st.success(f"Logged in as {name}")

            if st.button("Switch User", use_container_width=True):
                logout()
                st.rerun()
            return

        st.subheader("Who are you?")

        if st.button("Parent", use_container_width=True, type="primary"):
            st.session_state["_show_pin"] = True

        if st.session_state.get("_show_pin"):
            with st.form("pin_form"):
                pin = st.text_input("Enter PIN", type="password", max_chars=10)
                submitted = st.form_submit_button("Unlock")
                if submitted:
                    if verify_pin(pin):
                        st.session_state.role = "parent"
                        st.session_state.child_id = None
                        st.session_state.pin_verified = True
                        st.session_state.pop("_show_pin", None)
                        st.rerun()
                    else:
                        st.error("Incorrect PIN")

        children = list_children()
        if children:
            st.divider()
            st.subheader("Children")
            for child in children:
                if st.button(child["name"], use_container_width=True, key=f"child_{child['id']}"):
                    st.session_state.role = "child"
                    st.session_state.child_id = child["id"]
                    st.session_state.pin_verified = False
                    st.session_state.pop("_show_pin", None)
                    st.rerun()
        else:
            st.info("No children added yet. Log in as Parent to add children.")
