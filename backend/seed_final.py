import asyncio
from datetime import datetime, timedelta, timezone
from src.config.database import get_db_context
from src.models.workshop import Workshop
from src.models.pit import Pit
from src.models.job import Job
from src.models.user import User
from src.models.device import Device, SensorType
from src.models.sensor_data import SensorData
from src.models.alert import Alert
from src.models.subscription import Subscription
from src.models.device_command import DeviceCommand
from src.models.audit_log import AuditLog

async def seed():
    try:
        async with get_db_context() as session:
            # 1. Workshop
            w = Workshop(id=999, name="Test Tracking Workshop", slug="test-workshop-999")
            session.add(w)
            
            # 2. Pit
            p = Pit(id=999, workshop_id=999, pit_number=99, name="Tracking Pit", description="Demo", status="active", camera_is_online=False)
            session.add(p)
            
            # 3. Job
            j = Job(
                id=999, 
                workshop_id=999, 
                pit_id=999, 
                work_type="PPF", 
                status="in_progress", 
                car_model="Mahindra XUV700", 
                car_plate="MH-12-AB-1234", 
                customer_view_token="GT3RSX", 
                customer_view_expires_at=datetime.now(timezone.utc) + timedelta(days=30), 
                scheduled_start_time=datetime.now(timezone.utc) - timedelta(hours=2), 
                actual_start_time=datetime.now(timezone.utc) - timedelta(hours=1), 
                estimated_duration_minutes=480, 
                currency="USD"
            )
            session.add(j)
            
            await session.commit()
            print("Successfully seeded via ORM models inside container")
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(seed())
