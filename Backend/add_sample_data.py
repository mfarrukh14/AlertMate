"""Script to add sample data to the database for testing admin dashboard."""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_session, init_db
from app.db.models import User, AgentTask, ServiceEvent, AgentTaskStatus
from app.models.dispatch import ServiceType
from app.services.user_service import register_user
from app.models.user import UserRegistrationRequest

def add_sample_data():
    """Add sample data for testing the admin dashboard."""
    
    # Initialize database
    init_db()
    
    with next(get_session()) as session:
        # Create sample users if they don't exist
        existing_users = session.query(User).count()
        
        if existing_users == 0:
            print("Adding sample users...")
            sample_users = [
                {
                    "name": "Ahmad Khan",
                    "email": "ahmad@example.com",
                    "password": "password123",
                    "city": "Karachi",
                    "lat": 24.8607,
                    "lon": 67.0011
                },
                {
                    "name": "Fatima Ali", 
                    "email": "fatima@example.com",
                    "password": "password123",
                    "city": "Lahore",
                    "lat": 31.5204,
                    "lon": 74.3587
                },
                {
                    "name": "Hassan Sheikh",
                    "email": "hassan@example.com", 
                    "password": "password123",
                    "city": "Islamabad",
                    "lat": 33.6844,
                    "lon": 73.0479
                },
                {
                    "name": "Aisha Malik",
                    "email": "aisha@example.com",
                    "password": "password123", 
                    "city": "Faisalabad",
                    "lat": 31.4504,
                    "lon": 73.1350
                },
            ]
            
            for user_data in sample_users:
                try:
                    register_user(session, UserRegistrationRequest(**user_data))
                    print(f"Created user: {user_data['name']}")
                except Exception as e:
                    print(f"Error creating user {user_data['name']}: {e}")
        
        # Get users for creating tasks
        users = session.query(User).all()
        
        if not users:
            print("No users found, cannot create tasks")
            return
            
        print(f"Found {len(users)} users")
        
        # Create sample tasks
        existing_tasks = session.query(AgentTask).count()
        
        if existing_tasks < 10:  # Only add if we don't have enough tasks
            print("Adding sample tasks...")
            
            services = [ServiceType.MEDICAL, ServiceType.POLICE, ServiceType.DISASTER]
            statuses = [AgentTaskStatus.PENDING, AgentTaskStatus.IN_PROGRESS, AgentTaskStatus.COMPLETED]
            
            for i in range(15):
                user = random.choice(users)
                service = random.choice(services)
                status = random.choice(statuses)
                
                # Create task with random timestamp in last 24 hours
                created_time = datetime.utcnow() - timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                updated_time = created_time + timedelta(
                    minutes=random.randint(1, 120)
                )
                
                task = AgentTask(
                    user_id=user.user_id,
                    service_type=service,
                    status=status,
                    priority=random.randint(1, 4),
                    created_at=created_time,
                    updated_at=updated_time,
                    request_summary=f"Emergency request for {service.value} service",
                    agent_response=f"Response for {service.value} emergency" if status == AgentTaskStatus.COMPLETED else None
                )
                
                session.add(task)
            
            session.commit()
            print("Created sample tasks")
        
        # Create sample service events for dispatch locations
        existing_events = session.query(ServiceEvent).count()
        
        if existing_events < 5:
            print("Adding sample service events...")
            
            for i in range(8):
                user = random.choice(users)
                service = random.choice(services)
                
                event_time = datetime.utcnow() - timedelta(
                    hours=random.randint(0, 12),
                    minutes=random.randint(0, 59)
                )
                
                event = ServiceEvent(
                    user_id=user.user_id,
                    service_type=service,
                    latitude=user.lat + random.uniform(-0.1, 0.1),  # Add some variation
                    longitude=user.lon + random.uniform(-0.1, 0.1),
                    event_details=f"Dispatched {service.value} service to {user.city}",
                    created_at=event_time
                )
                
                session.add(event)
            
            session.commit()
            print("Created sample service events")
        
        # Print summary
        total_users = session.query(User).count()
        total_tasks = session.query(AgentTask).count()
        total_events = session.query(ServiceEvent).count()
        active_tasks = session.query(AgentTask).filter(
            AgentTask.status.in_([AgentTaskStatus.PENDING, AgentTaskStatus.IN_PROGRESS])
        ).count()
        
        print("\n=== Database Summary ===")
        print(f"Total Users: {total_users}")
        print(f"Total Tasks: {total_tasks}")
        print(f"Active Tasks: {active_tasks}")
        print(f"Total Service Events: {total_events}")
        print("======================")


if __name__ == "__main__":
    add_sample_data()