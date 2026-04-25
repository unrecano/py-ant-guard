import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
    client = AsyncIOMotorClient(mongo_uri)
    try:
        await client.admin.command("ping")
        print("Bot successfully connected to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

    # Simulate bot running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
