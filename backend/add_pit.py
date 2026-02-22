import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://ppf_user:ppf_dev_password_2026@localhost:5432/ppf_monitoring')
    async with engine.begin() as conn:
        workshops = await conn.execute(text("SELECT id FROM workshops LIMIT 1"))
        workshop_id = workshops.scalar()
        if not workshop_id:
            print('Need a workshop first, creating...')
            await conn.execute(text("INSERT INTO workshops (name, slug, subscription_plan, subscription_status, is_active, max_users, max_pits) VALUES ('Pit 1 Demo', 'pit-1-demo', 'basic', 'active', true, 5, 1)"))
            workshops = await conn.execute(text("SELECT id FROM workshops LIMIT 1"))
            workshop_id = workshops.scalar()
            
        print(f"Using workshop_id: {workshop_id}")
        await conn.execute(text(f"INSERT INTO pits (workshop_id, pit_number, name, description, status, created_at, updated_at) VALUES ({workshop_id}, 1, 'Demo Pit 1', 'Main floor', 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) ON CONFLICT DO NOTHING"))
        await conn.commit()
        print('Pit added successfully')

asyncio.run(main())
