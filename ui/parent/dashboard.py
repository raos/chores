import streamlit as st
from db.queries.chore_instances import get_pending_approvals
from logic.wallet import approve_by_parent, reset_chore

STATUS_EMOJI = {
    "pending": "⬜",
    "completed_pending_approval": "🟡",
    "approved": "✅",
    "missed": "❌",
}


def render_parent_dashboard():
    st.header("Pending Approvals")

    pending = get_pending_approvals()

    if not pending:
        st.success("All caught up! No chores waiting for approval.")
        return

    # Group by child
    by_child: dict = {}
    for inst in pending:
        child_name = inst["child_name"] or "Unassigned"
        by_child.setdefault(child_name, []).append(inst)

    for child_name, instances in by_child.items():
        st.subheader(f"{child_name}")
        for inst in instances:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{inst['title']}**")
                    st.caption(f"Scheduled: {inst['scheduled_date']}")
                    if inst["description"]:
                        st.caption(inst["description"])
                    _render_allowance_info(inst)
                with col2:
                    if st.button(
                        "Approve",
                        key=f"approve_{inst['id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        approve_by_parent(inst["id"])
                        st.rerun()
                with col3:
                    if st.button(
                        "Reset",
                        key=f"reset_{inst['id']}",
                        use_container_width=True,
                    ):
                        reset_chore(inst["id"])
                        st.rerun()


def _render_allowance_info(inst):
    parts = []
    atype = inst["allowance_type"]
    if atype in ("fixed", "both") and inst["fixed_amount"]:
        parts.append(f"💰 ${inst['fixed_amount']:.2f}")
    if atype in ("weighted", "both") and inst["chore_weight"]:
        parts.append(f"⚖️ weight {inst['chore_weight']} (week-end)")
    if inst["screen_time_hours"] and inst["screen_time_hours"] > 0:
        parts.append(f"🎮 {inst['screen_time_hours']:.0f} min screen time")
    if parts:
        st.caption(" | ".join(parts))
