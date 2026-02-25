import asyncio
from src.config.database import get_db_context
from sqlalchemy import text

async def update_job():
    async with get_db_context() as session:
        await session.execute(text("UPDATE jobs SET car_model='Mahindra XUV700', car_plate='MH-12-AB-1234' WHERE id=999"))
        await session.commit()
        print("Updated car model successfully")

if __name__ == "__main__":
    asyncio.run(update_job())
