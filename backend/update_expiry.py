import asyncio
from sqlalchemy import text
from src.config.database import async_session_maker

async def update_expiry():
    try:
        async with async_session_maker() as session:
            # Check current row
            result = await session.execute(text("SELECT id, customer_view_token, customer_view_expires_at FROM jobs WHERE customer_view_token = 'GT3RSX'"))
            row = result.fetchone()
            print("Before UPDATE:", row)
            
            # Update row
            await session.execute(text("UPDATE jobs SET customer_view_expires_at = NOW() + INTERVAL '30 days' WHERE customer_view_token = 'GT3RSX'"))
            await session.commit()
            
            # Check new row
            result = await session.execute(text("SELECT id, customer_view_token, customer_view_expires_at FROM jobs WHERE customer_view_token = 'GT3RSX'"))
            row = result.fetchone()
            print("After UPDATE:", row)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(update_expiry())
