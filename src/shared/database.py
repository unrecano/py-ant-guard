"""Motor async client and database setup for AntGuard."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def create_client(uri: str) -> AsyncIOMotorClient[dict[str, object]]:
    """Create an async Motor client from a MongoDB URI.

    Args:
        uri: MongoDB connection string (local or Atlas).

    Returns:
        A configured ``AsyncIOMotorClient`` instance.
    """
    return AsyncIOMotorClient(uri)


async def ensure_indexes(db: AsyncIOMotorDatabase[dict[str, object]]) -> None:
    """Create required indexes on MongoDB collections.

    Idempotent — safe to call on every application startup. MongoDB will
    skip creation if the index already exists with matching options.

    Args:
        db: The Motor database instance to apply indexes to.
    """
    await db["transactions"].create_index("category")
    await db["transactions"].create_index("created_at")
    await db["budgets"].create_index("category", unique=True)


async def init_db(uri: str) -> AsyncIOMotorDatabase[dict[str, object]]:
    """Initialize the Motor client and return the application database.

    Creates the client, selects the database embedded in the URI path,
    and ensures all required indexes exist before returning.

    Args:
        uri: MongoDB connection string. The database name must be
             embedded in the URI path (e.g. ``mongodb://host/ant_guard``).
             Both local and Atlas URIs are supported.

    Returns:
        The Motor database instance, ready to use for queries.

    Raises:
        ``pymongo.errors.ConfigurationError``: If the URI does not include
            a default database name in its path segment.
    """
    client = create_client(uri)
    db = client.get_default_database()
    await ensure_indexes(db)
    return db
