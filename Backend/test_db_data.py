"""Quick script to check if users exist and create test data if needed."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.db import get_session, engine
from app.db.models import User, AgentTask, ServiceEvent, AgentTaskStatus
from app.models.dispatch import ServiceType
from app.services.user_service import register_user
from app.models.user import UserRegistrationRequest
from datetime import datetime, timedelta
from sqlalchemy import text

def check_and_add_test_data():
    """Check existing data and add test data if needed."""
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
            user_count = result.fetchone().count
            print(f"Current users in database: {user_count}")
            
            result = conn.execute(text("SELECT COUNT(*) as count FROM agent_tasks"))  
            task_count = result.fetchone().count
            print(f"Current tasks in database: {task_count}")
            
            result = conn.execute(text("SELECT COUNT(*) as count FROM service_events"))
            event_count = result.fetchone().count
            print(f"Current service events in database: {event_count}")
            
            # If no users, add some test users
            if user_count == 0:
                print("No users found. Adding test users...")
                
                with next(get_session()) as session:
                    # Create test users
                    test_users = [
                        UserRegistrationRequest(
                            name="Ahmad Khan",
                            email="ahmad@test.com", 
                            password="password123",
                            city="Karachi",
                            lat=24.8607,
                            lon=67.0011
                        ),
                        UserRegistrationRequest(
                            name="Fatima Ali",
                            email="fatima@test.com",
                            password="password123", 
                            city="Lahore",
                            lat=31.5204,
                            lon=74.3587
                        )
                    ]
                    
                    for user_req in test_users:
                        try:
                            user = register_user(session, user_req)
                            print(f"Created user: {user.name}")
                        except Exception as e:
                            print(f"Error creating user: {e}")
                    
                    session.commit()
                    
            # Check if we need test tasks
            if task_count == 0:
                print("No tasks found. Adding test tasks...")
                
                with next(get_session()) as session:
                    users = session.query(User).all()
                    if users:
                        for i, user in enumerate(users[:3]):  # Create tasks for first 3 users
                            task = AgentTask(
                                user_id=user.user_id,
                                service_type=ServiceType.MEDICAL if i == 0 else ServiceType.POLICE,
                                status=AgentTaskStatus.PENDING if i == 0 else AgentTaskStatus.COMPLETED,
                                priority=2,
                                request_summary=f"Emergency request from {user.name}",
                                agent_response="Task processed" if i > 0 else None,
                                created_at=datetime.utcnow() - timedelta(hours=i),
                                updated_at=datetime.utcnow() - timedelta(hours=i-1) if i > 0 else datetime.utcnow()
                            )
                            session.add(task)
                        
                        session.commit()
                        print(f"Created {len(users)} test tasks")
                            
        print("\\n=== Final Counts ===")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
            print(f"Users: {result.fetchone().count}")
            
            result = conn.execute(text("SELECT COUNT(*) as count FROM agent_tasks"))
            print(f"Tasks: {result.fetchone().count}")
            
            result = conn.execute(text("SELECT COUNT(*) as count FROM service_events"))
            print(f"Events: {result.fetchone().count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_and_add_test_data()