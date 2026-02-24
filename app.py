import streamlit as st
from datetime import date, timedelta

from db.schema import initialize_db, seed_defaults
from db.queries.chore_instances import sweep_missed_chores
from logic.recurrence import ensure_instances_for_window
from ui.auth_gate import render_auth_gate


def _bootstrap():
    """Run once per session: DB init, sweep missed chores, expand instances."""
    if st.session_state.get("_bootstrapped"):
        return
    initialize_db()
    seed_defaults()
    today = date.today()
    sweep_missed_chores(today.isoformat())
    ensure_instances_for_window(today - timedelta(days=14), today + timedelta(days=30))
    st.session_state["_bootstrapped"] = True


def _render_parent_app():
    from ui.parent.dashboard import render_parent_dashboard
    from ui.parent.chore_manager import render_chore_manager
    from ui.parent.child_manager import render_child_manager
    from ui.parent.settings import render_parent_settings

    st.title("Parent Dashboard")

    tab_approvals, tab_chores, tab_children, tab_settings = st.tabs(
        ["Approvals", "Chores", "Children", "Settings"]
    )

    with tab_approvals:
        render_parent_dashboard()

    with tab_chores:
        render_chore_manager()

    with tab_children:
        render_child_manager()

    with tab_settings:
        render_parent_settings()


def _render_child_app(child_id: int):
    from ui.child.dashboard import render_child_dashboard
    from ui.child.chore_add import render_chore_add

    tab_home, tab_add = st.tabs(["My Chores", "Add a Chore"])

    with tab_home:
        render_child_dashboard(child_id)

    with tab_add:
        render_chore_add(child_id)


def main():
    st.set_page_config(
        page_title="Family Chores",
        page_icon="✅",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _bootstrap()
    render_auth_gate()

    role = st.session_state.get("role")

    if role is None:
        st.title("Family Chores")
        st.markdown(
            "Use the sidebar to log in as a **Parent** or select a **Child** to get started."
        )
        return

    if role == "parent":
        _render_parent_app()
    elif role == "child":
        child_id = st.session_state.get("child_id")
        if child_id:
            _render_child_app(child_id)
        else:
            st.error("No child selected.")


if __name__ == "__main__":
    main()
