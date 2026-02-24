import json
import streamlit as st
from datetime import date
from db.queries.chores import list_chores, get_chore, create_chore, update_chore, deactivate_chore, prune_future_instances
from db.queries.children import list_children
from logic.recurrence import ensure_instances_for_window

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_MAP = {name: i for i, name in enumerate(DAYS_OF_WEEK)}
# Explicit session state key for the "Assign to" selectbox, shared across add/edit forms.
# Must be cleared whenever the form is opened so `index` picks the correct default.
_ASSIGN_KEY = "chore_form_assign_to"


def render_chore_manager():
    st.header("Manage Chores")

    edit_id = st.session_state.get("chore_edit_id")

    if st.button("+ Add New Chore", type="primary"):
        st.session_state.chore_edit_id = -1  # -1 = new chore form
        st.session_state.pop(_ASSIGN_KEY, None)  # reset so index=0 takes effect
        st.rerun()

    if edit_id is not None:
        if edit_id == -1:
            _render_chore_form(chore=None)
        else:
            chore = get_chore(edit_id)
            if chore:
                _render_chore_form(chore=chore)

    st.divider()

    chores = list_chores(active_only=True)
    if not chores:
        st.info("No chores yet. Add one above.")
        return

    for chore in chores:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{chore['title']}**")
                child_label = f"For: {chore['child_name']}" if chore['child_name'] else "Unassigned"
                rec_label = _recurrence_label(chore)
                st.caption(f"{child_label} | {rec_label}")
                _render_allowance_badge(chore)
            with col2:
                if st.button("Edit", key=f"edit_{chore['id']}", use_container_width=True):
                    st.session_state.chore_edit_id = chore["id"]
                    st.session_state.pop(_ASSIGN_KEY, None)  # reset so correct child loads
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"del_{chore['id']}", use_container_width=True):
                    deactivate_chore(chore["id"])
                    prune_future_instances(chore["id"], date.today().isoformat())
                    st.session_state.pop("chore_edit_id", None)
                    st.rerun()


def _render_chore_form(chore):
    is_new = chore is None
    title = "Add Chore" if is_new else "Edit Chore"
    st.subheader(title)

    children = list_children()
    child_options = {c["name"]: c["id"] for c in children}
    child_options["Unassigned"] = None

    with st.form("chore_form"):
        form_title = st.text_input(
            "Title", value="" if is_new else chore["title"]
        )
        form_desc = st.text_area(
            "Description (optional)", value="" if is_new else (chore["description"] or "")
        )

        selected_child_name = st.selectbox(
            "Assign to",
            options=list(child_options.keys()),
            index=_child_index(chore, child_options) if not is_new else 0,
            key=_ASSIGN_KEY,
        )

        rec_type = st.selectbox(
            "Recurrence",
            options=["once", "daily", "weekly"],
            index=0 if is_new else ["once", "daily", "weekly"].index(chore["recurrence_type"]),
        )

        selected_days = []
        if rec_type == "daily":
            current_days = []
            if not is_new and chore["recurrence_days"]:
                current_days = [DAYS_OF_WEEK[d] for d in json.loads(chore["recurrence_days"])]
            selected_days = st.multiselect(
                "Days of week",
                options=DAYS_OF_WEEK,
                default=current_days if current_days else DAYS_OF_WEEK[:5],
            )
        elif rec_type == "weekly":
            current_day = DAYS_OF_WEEK[0]
            if not is_new and chore["recurrence_days"]:
                current_day = DAYS_OF_WEEK[json.loads(chore["recurrence_days"])[0]]
            weekly_day = st.selectbox(
                "Day of week",
                options=DAYS_OF_WEEK,
                index=DAYS_OF_WEEK.index(current_day),
            )
            selected_days = [weekly_day]

        start_date = st.date_input(
            "Start date",
            value=date.today() if is_new else date.fromisoformat(chore["start_date"]),
        )

        has_end = st.checkbox(
            "Set end date",
            value=False if is_new else (chore["end_date"] is not None),
        )
        end_date = None
        if has_end:
            end_date = st.date_input(
                "End date",
                value=date.today() if is_new else (
                    date.fromisoformat(chore["end_date"]) if chore["end_date"] else date.today()
                ),
            )

        st.divider()
        st.subheader("Allowance")

        allowance_type = st.selectbox(
            "Monetary allowance type",
            options=["None", "fixed", "weighted", "both"],
            index=0 if is_new else _allowance_index(chore),
        )

        fixed_amount = None
        chore_weight = None
        if allowance_type in ("fixed", "both"):
            fixed_amount = st.number_input(
                "Fixed amount ($)",
                min_value=0.0,
                step=0.25,
                value=0.0 if is_new else (chore["fixed_amount"] or 0.0),
            )
        if allowance_type in ("weighted", "both"):
            chore_weight = st.number_input(
                "Chore weight (for weekly split)",
                min_value=0.1,
                step=0.5,
                value=1.0 if is_new else (chore["chore_weight"] or 1.0),
            )

        screen_time = st.number_input(
            "Screen time earned (minutes)",
            min_value=0.0,
            step=5.0,
            value=0.0 if is_new else (chore["screen_time_hours"] or 0.0),
        )

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("Save", type="primary", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.pop("chore_edit_id", None)
            st.session_state.pop(_ASSIGN_KEY, None)
            st.rerun()

        if submitted:
            if not form_title.strip():
                st.error("Title is required.")
            elif rec_type in ("daily", "weekly") and not selected_days:
                st.error("Select at least one day.")
            else:
                rec_days_json = None
                if rec_type in ("daily", "weekly"):
                    rec_days_json = json.dumps([DAY_MAP[d] for d in selected_days])

                atype = None if allowance_type == "None" else allowance_type
                assigned_to = child_options[selected_child_name]

                if is_new:
                    new_id = create_chore(
                        title=form_title.strip(),
                        description=form_desc.strip() or None,
                        assigned_to=assigned_to,
                        created_by_role="parent",
                        recurrence_type=rec_type,
                        recurrence_days=rec_days_json,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat() if end_date else None,
                        allowance_type=atype,
                        fixed_amount=fixed_amount,
                        chore_weight=chore_weight,
                        screen_time_hours=screen_time,
                    )
                else:
                    update_chore(
                        chore_id=chore["id"],
                        title=form_title.strip(),
                        description=form_desc.strip() or None,
                        assigned_to=assigned_to,
                        recurrence_type=rec_type,
                        recurrence_days=rec_days_json,
                        start_date=start_date.isoformat(),
                        end_date=end_date.isoformat() if end_date else None,
                        allowance_type=atype,
                        fixed_amount=fixed_amount,
                        chore_weight=chore_weight,
                        screen_time_hours=screen_time,
                    )
                    if end_date:
                        prune_future_instances(chore["id"], end_date.isoformat())

                today = date.today()
                from datetime import timedelta
                ensure_instances_for_window(today, today + timedelta(days=30))

                st.session_state.pop("chore_edit_id", None)
                st.session_state.pop(_ASSIGN_KEY, None)
                st.rerun()


def _child_index(chore, child_options):
    if not chore or not chore["child_name"]:
        return list(child_options.keys()).index("Unassigned")
    try:
        return list(child_options.keys()).index(chore["child_name"])
    except ValueError:
        return list(child_options.keys()).index("Unassigned")


def _allowance_index(chore):
    options = ["None", "fixed", "weighted", "both"]
    atype = chore["allowance_type"] if chore["allowance_type"] else "None"
    try:
        return options.index(atype)
    except ValueError:
        return 0


def _recurrence_label(chore) -> str:
    rec = chore["recurrence_type"]
    if rec == "once":
        return f"Once on {chore['start_date']}"
    if rec in ("daily", "weekly") and chore["recurrence_days"]:
        days = [DAYS_OF_WEEK[d] for d in json.loads(chore["recurrence_days"])]
        return f"{rec.title()}: {', '.join(days)}"
    return rec.title()


def _render_allowance_badge(chore):
    parts = []
    atype = chore["allowance_type"]
    if atype in ("fixed", "both") and chore["fixed_amount"]:
        parts.append(f"💰 ${chore['fixed_amount']:.2f}")
    if atype in ("weighted", "both") and chore["chore_weight"]:
        parts.append(f"⚖️ weight {chore['chore_weight']}")
    if chore["screen_time_hours"] and chore["screen_time_hours"] > 0:
        parts.append(f"🎮 {chore['screen_time_hours']:.0f} min")
    if parts:
        st.caption(" | ".join(parts))
