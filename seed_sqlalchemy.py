import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime, timezone
import sys
import os

# Add backend directory to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from src.models.user import User
from src.models.workshop import Workshop
from src.models.pit import Pit
from src.models.job import Job
from src.config.settings import get_settings

settings = get_settings()

async def async_main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # Create user
        print("Checking/Creating Owner User...")
        stmt = select(User).where(User.username == "sa_owner")
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                username="sa_owner", 
                email="sa@owner.com", 
                password_hash="fake", 
                role="owner"
            )
            session.add(user)
            await session.commit()
            print(f"Created User: {user.id}")
            
        # Create workshop
        print("Checking/Creating Workshop...")
        stmt = select(Workshop).where(Workshop.name == "SA Workshop")
        result = await session.execute(stmt)
        workshop = result.scalar_one_or_none()
        
        if not workshop:
            workshop = Workshop(name="SA Workshop", owner_id=user.id)
            session.add(workshop)
            await session.commit()
            print(f"Created Workshop: {workshop.id}")
            
            # Link user to workshop
            user.workshop_id = workshop.id
            session.add(user)
            await session.commit()

        # Create pit
        print("Checking/Creating Pit...")
        stmt = select(Pit).where(Pit.name == "SA Pit")
        result = await session.execute(stmt)
        pit = result.scalar_one_or_none()
        
        if not pit:
            pit = Pit(name="SA Pit", pit_number=99, workshop_id=workshop.id)
            session.add(pit)
            await session.commit()
            print(f"Created Pit: {pit.id}")

        # Create Job
        print("Checking/Creating Job...")
        stmt = select(Job).where(Job.customer_view_token == "SA_TOKEN")
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
             job = Job(
                 workshop_id=workshop.id,
                 pit_id=pit.id,
                 work_type="PPF",
                 status="in_progress",
                 customer_view_token="SA_TOKEN",
                 scheduled_start_time=datetime.now(timezone.utc)
             )
             session.add(job)
             await session.commit()
             print(f"Created Job: {job.id} with token SA_TOKEN")
        else:
             print("Job SA_TOKEN already exists")

        print("Done!")

if __name__ == "__main__":
    asyncio.run(async_main())
