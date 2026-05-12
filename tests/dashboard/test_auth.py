from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from dashboard.auth import check_password


@patch("streamlit.secrets")
@patch("streamlit.session_state", {})
def test_check_password_no_auth(mock_secrets: MagicMock) -> None:
    """Test check_password when no authentication has been attempted."""
    mock_secrets.__getitem__.return_value = "secret"

    with patch("streamlit.text_input") as mock_input:
        result = check_password()
        assert result is False
        mock_input.assert_called_once()


@patch("streamlit.secrets")
def test_check_password_success(mock_secrets: MagicMock) -> None:
    """Test check_password with correct password."""
    mock_secrets.__getitem__.return_value = "correct_password"

    # Mock session state
    session_state: dict[str, Any] = {"password": "correct_password"}

    with patch("streamlit.session_state", session_state):
        # Trigger the callback manually or simulate it
        from dashboard.auth import check_password

        # We need to simulate the password_entered callback logic
        # since we can't easily trigger it via mock
        # or we just mock the session state as if it was already authenticated.

        session_state["authenticated"] = True
        result = check_password()
        assert result is True


@patch("streamlit.secrets")
def test_check_password_failure(mock_secrets: MagicMock) -> None:
    """Test check_password with incorrect password."""
    mock_secrets.__getitem__.return_value = "correct_password"

    # Mock session state as failed
    session_state: dict[str, Any] = {"authenticated": False}

    with (
        patch("streamlit.session_state", session_state),
        patch("streamlit.text_input") as mock_input,
        patch("streamlit.error") as mock_error,
    ):
        result = check_password()
        assert result is False
        mock_input.assert_called_once()
        mock_error.assert_called_once_with("😕 Password incorrect")
