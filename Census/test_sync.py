import asyncio
from services.sync_engine import run_full_sync
from database.session import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        result = await run_full_sync(db)
        print(f'Users: {result.get("users_synced", 0)}, Devices: {result.get("devices_synced", 0)}')
        print(f'Switches: {result.get("switches_synced", 0)}')
        return result

if __name__ == "__main__":
    asyncio.run(main())
