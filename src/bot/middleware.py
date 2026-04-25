from __future__ import annotations

import logging
import os

from .models import Update

logger = logging.getLogger(__name__)


def verify_user(update: Update) -> bool:
    """Verifies if the update comes from the authorized user.

    Args:
        update: The Telegram Update object to verify.

    Returns:
        True if authorized, False otherwise.
    """
    if not update.message or not update.message.from_user:
        return False

    authorized_id_str = os.getenv("AUTHORIZED_USER_ID")
    if not authorized_id_str:
        logger.error("AUTHORIZED_USER_ID environment variable is not set.")
        return False

    try:
        authorized_id = int(authorized_id_str)
    except ValueError:
        logger.error("AUTHORIZED_USER_ID is not a valid integer.")
        return False

    if update.message.from_user.id != authorized_id:
        logger.warning(
            "Unauthorized access attempt from user_id: %s", update.message.from_user.id
        )
        return False

    return True
