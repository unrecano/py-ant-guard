from __future__ import annotations

import streamlit as st


def check_password() -> bool:
    """Returns `True` if the user had the correct password.

    This function uses `st.secrets` to validate the password provided by the user
    via a simple text input.

    Returns:
        bool: True if authenticated, False otherwise.
    """

    def password_entered() -> None:
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["DASHBOARD_PASSWORD"]:
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False

    if not st.session_state["authenticated"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False

    # Password correct.
    return True
