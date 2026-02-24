from __future__ import annotations

import hashlib
import streamlit as st
from db.queries.settings import get_setting, set_setting


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin: str) -> bool:
    stored_hash = get_setting("pin_hash")
    if not stored_hash:
        return False
    return hash_pin(pin) == stored_hash


def change_pin(current_pin: str, new_pin: str) -> bool:
    if not verify_pin(current_pin):
        return False
    set_setting("pin_hash", hash_pin(new_pin))
    return True


def is_parent() -> bool:
    return st.session_state.get("role") == "parent"


def is_child() -> bool:
    return st.session_state.get("role") == "child"


def current_child_id() -> int | None:
    return st.session_state.get("child_id")


def logout():
    for key in ("role", "child_id", "pin_verified"):
        st.session_state.pop(key, None)
