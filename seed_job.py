import sys
import os

# Add the src directory to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from models.user import User
from models.pit import Pit
from models.job import Job
from config.settings import get_settings
from database.session import engine, SessionLocal
from datetime import datetime, timedelta

def seed_job():
    db = SessionLocal()
    try:
        # Create workshop owner
        owner = db.query(User).filter(User.email == "demo_owner@example.com").first()
        if not owner:
            owner = User(
                email="demo_owner@example.com",
                username="demo_owner",
                first_name="Demo",
                last_name="Owner",
                hashed_password="ignored",
                role="owner",
                workshop_name="Demo Workshop"
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)

        # Create pit
        pit = db.query(Pit).filter(Pit.name == "Demo Bay").first()
        if not pit:
            pit = Pit(
                name="Demo Bay",
                pit_number=99,
                workshop_id=owner.id,
                description="Live stream demo bay"
            )
            db.add(pit)
            db.commit()
            db.refresh(pit)
            
        # Create customer
        customer = db.query(User).filter(User.email == "demo_customer@example.com").first()
        if not customer:
            customer = User(
                email="demo_customer@example.com",
                username="demo_customer",
                first_name="Demo",
                last_name="Customer",
                hashed_password="ignored",
                role="customer",
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

        # Create job
        job = db.query(Job).filter(Job.customer_view_token == "GT3RSX").first()
        if not job:
            job = Job(
                customer_id=customer.id,
                pit_id=pit.id,
                workshop_id=owner.id,
                car_model="Porsche 911 GT3 RS",
                car_plate="M-PPF001",
                car_color="Guards Red",
                car_year=2024,
                work_type="Full Body Stealth PPF",
                work_description="Applying Xpel stealth to full exterior. Customer waiting on updates.",
                status="in_progress",
                customer_view_token="GT3RSX",
                estimated_duration_minutes=360,
                scheduled_start_time=datetime.utcnow() - timedelta(hours=2)
            )
            db.add(job)
            db.commit()
            print("Successfully created test job with token GT3RSX")
        else:
            job.status = "in_progress"
            db.commit()
            print("Job already exists, updated status to in_progress")

    finally:
        db.close()

if __name__ == "__main__":
    seed_job()
