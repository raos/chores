import json
import streamlit as st
from datetime import date, timedelta
from db.queries.chores import create_chore
from logic.recurrence import ensure_instances_for_window

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_MAP = {name: i for i, name in enumerate(DAYS_OF_WEEK)}


def render_chore_add(child_id: int):
    st.header("Add a Chore")
    st.caption("You can add chores here. A parent will need to approve them once done.")

    with st.form("child_add_chore_form"):
        title = st.text_input("Chore name")
        description = st.text_area("Description (optional)")

        rec_type = st.selectbox(
            "How often?",
            options=["once", "daily", "weekly"],
            format_func=lambda x: {"once": "Just once", "daily": "Certain days each week", "weekly": "Once a week"}[x],
        )

        selected_days = []
        if rec_type == "daily":
            selected_days = st.multiselect(
                "Which days?",
                options=DAYS_OF_WEEK,
                default=DAYS_OF_WEEK[:5],
            )
        elif rec_type == "weekly":
            weekly_day = st.selectbox("Which day?", options=DAYS_OF_WEEK)
            selected_days = [weekly_day]

        start_date = st.date_input("Starting from", value=date.today())

        submitted = st.form_submit_button("Add Chore", type="primary")

        if submitted:
            if not title.strip():
                st.error("Please enter a chore name.")
            elif rec_type in ("daily", "weekly") and not selected_days:
                st.error("Please select at least one day.")
            else:
                rec_days_json = None
                if rec_type in ("daily", "weekly"):
                    rec_days_json = json.dumps([DAY_MAP[d] for d in selected_days])

                create_chore(
                    title=title.strip(),
                    description=description.strip() or None,
                    assigned_to=child_id,
                    created_by_role="child",
                    recurrence_type=rec_type,
                    recurrence_days=rec_days_json,
                    start_date=start_date.isoformat(),
                    end_date=None,
                    allowance_type=None,
                    fixed_amount=None,
                    chore_weight=None,
                    screen_time_hours=0.0,
                )

                today = date.today()
                ensure_instances_for_window(today, today + timedelta(days=30))
                st.success(f"Chore '{title.strip()}' added!")
                st.rerun()
