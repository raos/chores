import streamlit as st
from datetime import date, timedelta

from db.schema import initialize_db, seed_defaults
from db.queries.chore_instances import sweep_missed_chores
from logic.recurrence import ensure_instances_for_window
from ui.auth_gate import render_auth_gate


_MOBILE_CSS = """
<style>
/* ── Touch targets ──────────────────────────────────────────────────────────
   Give every button a comfortable minimum tap height on all screen sizes.   */
.stButton > button,
.stFormSubmitButton > button {
    min-height: 2.75rem;
}

/* ── Compact sidebar ────────────────────────────────────────────────────────
   Cap sidebar width so it doesn't crowd the viewport on small tablets.      */
@media (max-width: 768px) {
    [data-testid="stSidebar"] > div:first-child {
        width: 240px !important;
        min-width: 240px !important;
    }
}

/* ── Main content padding ───────────────────────────────────────────────────
   Streamlit's default side-padding is generous; tighten it on phones.       */
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 0.75rem !important;
        max-width: 100% !important;
    }
}

/* ── Heading scale ──────────────────────────────────────────────────────────
   Large headings overflow on small screens; scale them down.                */
@media (max-width: 480px) {
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1.1rem !important; }
}

/* ── Metric cards ───────────────────────────────────────────────────────────
   Tighten internal padding so three metrics fit side-by-side on phones.     */
@media (max-width: 640px) {
    [data-testid="stMetric"] {
        padding: 0.4rem 0.5rem !important;
    }
    [data-testid="stMetricLabel"] p {
        font-size: 0.75rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
}

/* ── Week calendar: horizontal scroll ──────────────────────────────────────
   The 7-column week grid is too narrow to render vertically on a phone.
   Make it scroll horizontally instead, with a fixed minimum column width.
   :has(> column:nth-child(7)) targets only the 7-col block, leaving all
   other multi-column layouts untouched.
   :has() is supported on Safari 15.4+, Chrome 105+, Firefox 121+.          */
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"]:has(
        > [data-testid="column"]:nth-child(7)
    ) {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        flex-wrap: nowrap !important;
        scroll-snap-type: x proximity;
        gap: 2px !important;
        padding-bottom: 6px !important;
    }

    [data-testid="stHorizontalBlock"]:has(
        > [data-testid="column"]:nth-child(7)
    ) > [data-testid="column"] {
        flex: 0 0 108px !important;
        min-width: 108px !important;
        scroll-snap-align: start;
    }
}

/* ── Tab bar ────────────────────────────────────────────────────────────────
   Enlarge tab touch targets and allow horizontal scroll if tabs overflow.   */
@media (max-width: 768px) {
    [data-testid="stTabs"] [data-testid="stTabBar"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
    button[data-baseweb="tab"] {
        min-height: 2.75rem !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.85rem !important;
        white-space: nowrap !important;
    }
}
</style>
"""


def _inject_mobile_css():
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)


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

    _inject_mobile_css()
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
