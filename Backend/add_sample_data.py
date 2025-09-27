"""Script to add reference data (hospitals, police stations, etc.) to the database."""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_session, init_db
from app.db.models import ServiceLocation
from app.models.dispatch import ServiceType

def add_service_locations():
    """Add reference data for hospitals, police stations, etc."""
    
    # Initialize database
    init_db()
    
    with next(get_session()) as session:
        # Check if we already have service locations
        existing_locations = session.query(ServiceLocation).count()
        
        if existing_locations > 0:
            print(f"Service locations already exist ({existing_locations} locations)")
            return
            
        print("Adding service location reference data...")
        
        # Karachi service locations
        karachi_services = [
            {"name": "Aga Khan University Hospital", "service": ServiceType.MEDICAL, "lat": 24.8829, "lon": 67.0653, "city": "Karachi"},
            {"name": "Jinnah Postgraduate Medical Centre", "service": ServiceType.MEDICAL, "lat": 24.8743, "lon": 67.0451, "city": "Karachi"},
            {"name": "Civil Hospital Karachi", "service": ServiceType.MEDICAL, "lat": 24.8615, "lon": 67.0099, "city": "Karachi"},
            {"name": "Karachi Police Station - Clifton", "service": ServiceType.POLICE, "lat": 24.8138, "lon": 67.0299, "city": "Karachi"},
            {"name": "Karachi Police Station - Gulshan", "service": ServiceType.POLICE, "lat": 24.9214, "lon": 67.0876, "city": "Karachi"},
        ]
        
        # Lahore service locations
        lahore_services = [
            {"name": "Services Hospital Lahore", "service": ServiceType.MEDICAL, "lat": 31.5497, "lon": 74.3436, "city": "Lahore"},
            {"name": "King Edward Medical University Hospital", "service": ServiceType.MEDICAL, "lat": 31.5804, "lon": 74.3287, "city": "Lahore"},
            {"name": "Lahore General Hospital", "service": ServiceType.MEDICAL, "lat": 31.5656, "lon": 74.3141, "city": "Lahore"},
            {"name": "Lahore Police Station - Model Town", "service": ServiceType.POLICE, "lat": 31.4697, "lon": 74.3436, "city": "Lahore"},
            {"name": "Lahore Police Station - Gulberg", "service": ServiceType.POLICE, "lat": 31.5203, "lon": 74.3587, "city": "Lahore"},
        ]
        
        # Islamabad service locations
        islamabad_services = [
            {"name": "Pakistan Institute of Medical Sciences", "service": ServiceType.MEDICAL, "lat": 33.6573, "lon": 72.9904, "city": "Islamabad"},
            {"name": "Shifa International Hospital", "service": ServiceType.MEDICAL, "lat": 33.6844, "lon": 73.0479, "city": "Islamabad"},
            {"name": "Islamabad Police Station - G-9", "service": ServiceType.POLICE, "lat": 33.6796, "lon": 73.0507, "city": "Islamabad"},
            {"name": "Islamabad Police Station - F-8", "service": ServiceType.POLICE, "lat": 33.7036, "lon": 73.0563, "city": "Islamabad"},
        ]
        
        # Disaster response centers
        disaster_centers = [
            {"name": "NDMA Emergency Response Center - Karachi", "service": ServiceType.DISASTER, "lat": 24.8607, "lon": 67.0011, "city": "Karachi"},
            {"name": "NDMA Emergency Response Center - Lahore", "service": ServiceType.DISASTER, "lat": 31.5204, "lon": 74.3587, "city": "Lahore"},
            {"name": "NDMA Emergency Response Center - Islamabad", "service": ServiceType.DISASTER, "lat": 33.6844, "lon": 73.0479, "city": "Islamabad"},
        ]
        
        all_services = karachi_services + lahore_services + islamabad_services + disaster_centers
        
        for service_data in all_services:
            location = ServiceLocation(
                name=service_data["name"],
                service_type=service_data["service"],
                latitude=service_data["lat"],
                longitude=service_data["lon"],
                city=service_data["city"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            session.add(location)
        
        session.commit()
        print(f"Added {len(all_services)} service locations")
        
        # Print summary by service type
        for service in [ServiceType.MEDICAL, ServiceType.POLICE, ServiceType.DISASTER]:
            count = session.query(ServiceLocation).filter(
                ServiceLocation.service_type == service
            ).count()
            print(f"{service.value.title()} locations: {count}")


if __name__ == "__main__":
    add_service_locations()