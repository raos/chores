import streamlit as st
from datetime import date, timedelta
from db.queries.children import list_children, create_child, update_child, delete_child
from db.queries.wallets import get_balance, is_week_finalized
from logic.allowance import finalize_week


def render_child_manager():
    st.header("Children & Wallets")

    if st.button("+ Add Child", type="primary"):
        st.session_state["_show_add_child"] = True

    if st.session_state.get("_show_add_child"):
        with st.form("add_child_form"):
            name = st.text_input("Child's name")
            budget = st.number_input("Weekly allowance budget ($)", min_value=0.0, step=0.5)
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("Add", type="primary", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)
            if submitted:
                if name.strip():
                    create_child(name.strip(), budget)
                    st.session_state.pop("_show_add_child", None)
                    st.rerun()
                else:
                    st.error("Name is required.")
            if cancelled:
                st.session_state.pop("_show_add_child", None)
                st.rerun()

    st.divider()
    children = list_children()
    if not children:
        st.info("No children yet.")
        return

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    for child in children:
        with st.container(border=True):
            col_name, col_edit, col_del = st.columns([3, 1, 1])
            with col_name:
                st.subheader(child["name"])
            with col_edit:
                if st.button("Edit", key=f"edit_child_{child['id']}", use_container_width=True):
                    st.session_state[f"_edit_child_{child['id']}"] = True
                    st.rerun()
            with col_del:
                if st.button("Remove", key=f"del_child_{child['id']}", use_container_width=True):
                    st.session_state[f"_confirm_del_{child['id']}"] = True
                    st.rerun()

            if st.session_state.get(f"_confirm_del_{child['id']}"):
                st.warning(f"Remove {child['name']} and all their data?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, Remove", key=f"yes_del_{child['id']}", type="primary"):
                        delete_child(child["id"])
                        st.session_state.pop(f"_confirm_del_{child['id']}", None)
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key=f"no_del_{child['id']}"):
                        st.session_state.pop(f"_confirm_del_{child['id']}", None)
                        st.rerun()

            if st.session_state.get(f"_edit_child_{child['id']}"):
                with st.form(f"edit_child_form_{child['id']}"):
                    new_name = st.text_input("Name", value=child["name"])
                    new_budget = st.number_input(
                        "Weekly budget ($)",
                        min_value=0.0,
                        step=0.5,
                        value=float(child["weekly_allowance_budget"]),
                    )
                    col_s, col_c = st.columns(2)
                    with col_s:
                        saved = st.form_submit_button("Save", type="primary", use_container_width=True)
                    with col_c:
                        canc = st.form_submit_button("Cancel", use_container_width=True)
                    if saved and new_name.strip():
                        update_child(child["id"], new_name.strip(), new_budget)
                        st.session_state.pop(f"_edit_child_{child['id']}", None)
                        st.rerun()
                    if canc:
                        st.session_state.pop(f"_edit_child_{child['id']}", None)
                        st.rerun()
            else:
                col_budget, col_money, col_screen = st.columns(3)
                with col_budget:
                    st.metric("Weekly Budget", f"${child['weekly_allowance_budget']:.2f}")
                with col_money:
                    bal = get_balance(child["id"], "monetary")
                    st.metric("Money Earned", f"${bal:.2f}")
                with col_screen:
                    screen = get_balance(child["id"], "screen_time")
                    st.metric("Screen Time Banked", f"{screen:.0f} min")

                already_finalized = is_week_finalized(child["id"], week_start.isoformat())
                if already_finalized:
                    st.caption(f"Week of {week_start.isoformat()} already finalized.")
                else:
                    if st.button(
                        f"Finalize This Week's Weighted Allowance",
                        key=f"finalize_{child['id']}",
                    ):
                        result = finalize_week(
                            child_id=child["id"],
                            week_start=week_start.isoformat(),
                            week_end=week_end.isoformat(),
                        )
                        if result["status"] == "finalized":
                            st.success(
                                f"Finalized! Total payout: ${result['total_payout']:.2f}"
                            )
                            st.rerun()
                        elif result["status"] == "no_weighted_chores":
                            st.info("No approved weighted chores this week.")
                        elif result["status"] == "zero_weight":
                            st.warning("All chore weights are zero — nothing to distribute.")
