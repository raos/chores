import streamlit as st
from datetime import date
from db.queries.children import get_child
from db.queries.wallets import get_balance
from db.queries.chore_instances import get_instances_for_date
from ui.child.calendar import render_calendar


def render_child_dashboard(child_id: int):
    child = get_child(child_id)
    if not child:
        st.error("Child not found.")
        return

    st.title(f"Hi, {child['name']}!")

    # Wallet summary
    col1, col2 = st.columns(2)
    with col1:
        money = get_balance(child_id, "monetary")
        st.metric("Money Earned", f"${money:.2f}")
    with col2:
        screen = get_balance(child_id, "screen_time")
        st.metric("Screen Time Banked", f"{screen:.0f} min")

    st.divider()
    render_calendar(child_id)
