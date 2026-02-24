import streamlit as st
from datetime import date, timedelta
from db.queries.chore_instances import get_instances_for_week, get_instances_for_date
from logic.wallet import mark_done_by_child, reset_chore

STATUS_COLOR = {
    "pending": "🔘",
    "completed_pending_approval": "🟡",
    "approved": "🟢",
    "missed": "🔴",
}

STATUS_LABEL = {
    "pending": "To Do",
    "completed_pending_approval": "Waiting",
    "approved": "Done!",
    "missed": "Missed",
}


def render_calendar(child_id: int):
    if "calendar_view" not in st.session_state:
        st.session_state.calendar_view = "week"
    if "calendar_week_offset" not in st.session_state:
        st.session_state.calendar_week_offset = 0
    if "calendar_selected_date" not in st.session_state:
        st.session_state.calendar_selected_date = date.today().isoformat()

    # Header nav
    col_week, col_day = st.columns(2)
    with col_week:
        if st.button("Week View", use_container_width=True,
                     type="primary" if st.session_state.calendar_view == "week" else "secondary"):
            st.session_state.calendar_view = "week"
            st.rerun()
    with col_day:
        if st.button("Day View", use_container_width=True,
                     type="primary" if st.session_state.calendar_view == "day" else "secondary"):
            st.session_state.calendar_view = "day"
            st.rerun()

    if st.session_state.calendar_view == "week":
        _render_week_view(child_id)
    else:
        _render_day_view(child_id)


def _render_week_view(child_id: int):
    today = date.today()
    offset = st.session_state.calendar_week_offset
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    week_end = week_start + timedelta(days=6)

    # Navigation
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    with nav_col1:
        if st.button("◀ Prev", use_container_width=True):
            st.session_state.calendar_week_offset -= 1
            st.rerun()
    with nav_col2:
        st.markdown(
            f"<h4 style='text-align:center'>{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}</h4>",
            unsafe_allow_html=True,
        )
    with nav_col3:
        if st.button("Next ▶", use_container_width=True):
            st.session_state.calendar_week_offset += 1
            st.rerun()

    instances = get_instances_for_week(
        week_start.isoformat(), week_end.isoformat(), child_id=child_id
    )

    # Group by date
    by_date: dict[str, list] = {}
    for inst in instances:
        by_date.setdefault(inst["scheduled_date"], []).append(inst)

    # Render 7 columns
    day_cols = st.columns(7)
    for i, col in enumerate(day_cols):
        current_day = week_start + timedelta(days=i)
        day_str = current_day.isoformat()
        is_today = current_day == today

        with col:
            header_style = "**" if is_today else ""
            day_label = current_day.strftime("%a\n%d")
            if is_today:
                st.markdown(f"**:blue[{current_day.strftime('%a')}]**\n\n**:blue[{current_day.strftime('%d')}]**")
            else:
                st.markdown(f"**{current_day.strftime('%a')}**\n\n{current_day.strftime('%d')}")

            if st.button("View", key=f"view_day_{day_str}", use_container_width=True):
                st.session_state.calendar_view = "day"
                st.session_state.calendar_selected_date = day_str
                st.rerun()

            day_instances = by_date.get(day_str, [])
            if day_instances:
                for inst in day_instances:
                    emoji = STATUS_COLOR.get(inst["status"], "⬜")
                    st.caption(f"{emoji} {inst['title']}")
            else:
                st.caption("—")


def _render_day_view(child_id: int):
    today = date.today()
    selected = date.fromisoformat(st.session_state.calendar_selected_date)

    # Date navigation
    nav1, nav2, nav3 = st.columns([1, 4, 1])
    with nav1:
        if st.button("◀ Prev", use_container_width=True, key="day_prev"):
            st.session_state.calendar_selected_date = (selected - timedelta(days=1)).isoformat()
            st.rerun()
    with nav2:
        is_today = selected == today
        label = selected.strftime("%A, %B %d %Y")
        if is_today:
            st.markdown(f"#### :blue[{label}] (Today)")
        else:
            st.markdown(f"#### {label}")
    with nav3:
        if st.button("Next ▶", use_container_width=True, key="day_next"):
            st.session_state.calendar_selected_date = (selected + timedelta(days=1)).isoformat()
            st.rerun()

    instances = get_instances_for_date(selected.isoformat(), child_id=child_id)

    if not instances:
        st.info("No chores for this day.")
        return

    for inst in instances:
        _render_chore_card(inst, child_id, show_actions=True)


def _render_chore_card(inst, child_id: int, show_actions: bool = True):
    status = inst["status"]
    emoji = STATUS_COLOR.get(status, "⬜")
    label = STATUS_LABEL.get(status, status)

    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"{emoji} **{inst['title']}** — {label}")
            if inst["description"]:
                st.caption(inst["description"])
            _render_allowance_chips(inst)
        with col2:
            if show_actions and status == "pending":
                if st.button(
                    "Mark Done",
                    key=f"done_{inst['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    mark_done_by_child(inst["id"])
                    st.rerun()
            elif show_actions and status == "completed_pending_approval":
                if st.button(
                    "Undo",
                    key=f"undo_{inst['id']}",
                    use_container_width=True,
                ):
                    reset_chore(inst["id"])
                    st.rerun()


def _render_allowance_chips(inst):
    parts = []
    atype = inst["allowance_type"]
    if atype in ("fixed", "both") and inst["fixed_amount"]:
        parts.append(f"💰 ${inst['fixed_amount']:.2f}")
    if atype in ("weighted", "both") and inst["chore_weight"]:
        parts.append(f"⚖️ weighted")
    if inst["screen_time_hours"] and inst["screen_time_hours"] > 0:
        parts.append(f"🎮 {inst['screen_time_hours']:.0f} min")
    if parts:
        st.caption(" | ".join(parts))
