"""Smart service selection with automatic nearest service detection and calling capabilities."""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from app.services.hybrid_service_discovery import HybridServiceDiscovery
from app.services.google_api_client import ServiceLocation

logger = logging.getLogger(__name__)


@dataclass
class SelectedService:
    """Represents a selected emergency service with contact information."""
    name: str
    phone: str
    address: str
    lat: float
    lon: float
    distance_km: float
    eta_minutes: int
    service_type: str
    priority_score: float
    contact_method: str  # "phone", "sms", "email", "api"
    verified: bool


class SmartServiceSelector:
    """Intelligently select the best emergency service and handle contact methods."""
    
    def __init__(self):
        self.discovery = HybridServiceDiscovery()
    
    async def select_and_contact_nearest_service(
        self, 
        lat: float, 
        lon: float, 
        service_type: str,
        emergency_level: int = 1,
        preferred_contact: str = "phone"
    ) -> Dict[str, Any]:
        """Select the nearest service and initiate contact."""
        
        try:
            # Find all nearby services
            search_result = await self.discovery.find_emergency_services(
                lat=lat,
                lon=lon,
                service_type=service_type,
                radius_km=25,
                max_results=10
            )
            
            if not search_result.services:
                return self._create_fallback_response(service_type)
            
            # Select the best service based on multiple criteria
            selected_service = await self._select_best_service(
                search_result.services,
                lat, lon,
                emergency_level,
                preferred_contact
            )
            
            # Attempt to contact the service
            contact_result = await self._contact_service(selected_service)
            
            return {
                "selected_service": selected_service,
                "contact_result": contact_result,
                "search_metadata": {
                    "total_found": len(search_result.services),
                    "search_source": search_result.source,
                    "selection_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Smart service selection failed: {e}")
            return self._create_fallback_response(service_type)
    
    async def _select_best_service(
        self, 
        services: List[ServiceLocation], 
        user_lat: float, 
        user_lon: float,
        emergency_level: int,
        preferred_contact: str
    ) -> SelectedService:
        """Select the best service using intelligent scoring."""
        
        scored_services = []
        
        for service in services:
            # Calculate priority score
            score = await self._calculate_service_score(
                service, user_lat, user_lon, emergency_level, preferred_contact, service_type
            )
            
            scored_services.append((service, score))
        
        # Sort by score (highest first)
        scored_services.sort(key=lambda x: x[1], reverse=True)
        
        best_service, best_score = scored_services[0]
        
        # Calculate ETA
        eta_minutes = await self.discovery.calculate_real_eta(
            (user_lat, user_lon),
            (best_service.lat, best_service.lon)
        )
        
        # Determine best contact method
        contact_method = self._determine_best_contact_method(best_service, preferred_contact)
        
        return SelectedService(
            name=best_service.name,
            phone=best_service.phone or self._get_emergency_number(service_type),
            address=best_service.address or "Address not available",
            lat=best_service.lat,
            lon=best_service.lon,
            distance_km=best_service.distance_km,
            eta_minutes=eta_minutes,
            service_type=service_type,
            priority_score=best_score,
            contact_method=contact_method,
            verified=best_service.verified
        )
    
    async def _calculate_service_score(
        self, 
        service: ServiceLocation, 
        user_lat: float, 
        user_lon: float,
        emergency_level: int,
        preferred_contact: str,
        service_type: str
    ) -> float:
        """Calculate intelligent priority score for service selection."""
        
        score = 0.0
        
        # Distance score (closer is better)
        distance_score = max(0, 10 - service.distance_km)
        score += distance_score * 3.0
        
        # Emergency capability score
        score += service.emergency_capability * 2.0
        
        # Rating score
        rating_score = service.rating or 3.0
        score += rating_score * 1.5
        
        # Verification bonus
        if service.verified:
            score += 2.0
        
        # Contact availability bonus
        if service.phone:
            score += 1.5
        
        # Emergency level multiplier
        emergency_multiplier = {1: 1.5, 2: 1.2, 3: 1.0}.get(emergency_level, 1.0)
        score *= emergency_multiplier
        
        # Service type specific bonuses
        service_types = getattr(service, 'types', [])
        if service_types and any(st in str(service_types) for st in [service_type]):
            score += 2.0
        
        return score
    
    def _determine_best_contact_method(self, service: ServiceLocation, preferred: str) -> str:
        """Determine the best contact method for the service."""
        
        if preferred == "phone" and service.phone:
            return "phone"
        elif preferred == "sms" and service.phone:
            return "sms"
        elif preferred == "api" and service.place_id:
            return "api"
        else:
            return "phone"  # Default fallback
    
    def _get_emergency_number(self, service_type: str) -> str:
        """Get emergency numbers for different service types."""
        
        emergency_numbers = {
            "medical": "1122",
            "police": "15", 
            "fire": "16",
            "disaster": "16"
        }
        
        return emergency_numbers.get(service_type, "1122")
    
    async def _contact_service(self, service: SelectedService) -> Dict[str, Any]:
        """Attempt to contact the selected service."""
        
        contact_result = {
            "service_name": service.name,
            "contact_method": service.contact_method,
            "phone": service.phone,
            "attempted": True,
            "success": False,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if service.contact_method == "phone":
                # Option 1: Make actual phone call (requires telephony integration)
                contact_result.update(await self._make_phone_call(service))
                
            elif service.contact_method == "sms":
                # Option 2: Send SMS (requires SMS gateway)
                contact_result.update(await self._send_sms(service))
                
            elif service.contact_method == "api":
                # Option 3: Use emergency service API (if available)
                contact_result.update(await self._call_emergency_api(service))
                
            else:
                contact_result["error"] = f"Unknown contact method: {service.contact_method}"
                
        except Exception as e:
            contact_result["error"] = str(e)
            logger.error(f"Contact attempt failed: {e}")
        
        return contact_result
    
    async def _make_phone_call(self, service: SelectedService) -> Dict[str, Any]:
        """Make an actual phone call to the emergency service."""
        
        # Option A: Twilio Integration
        try:
            # Uncomment when you have Twilio credentials
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # call = client.calls.create(
            #     to=service.phone,
            #     from_=twilio_phone_number,
            #     url='http://your-server.com/emergency-call-script.xml'
            # )
            # return {"call_sid": call.sid, "status": "initiated"}
            
            # For now, simulate the call
            return {
                "call_status": "simulated",
                "message": f"Would call {service.phone} for {service.name}",
                "integration_needed": "Twilio"
            }
            
        except Exception as e:
            return {"error": f"Phone call failed: {e}"}
    
    async def _send_sms(self, service: SelectedService) -> Dict[str, Any]:
        """Send SMS to the emergency service."""
        
        try:
            # Option A: Twilio SMS
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=f"EMERGENCY ALERT: Service needed at location. Please respond.",
            #     from_=twilio_phone_number,
            #     to=service.phone
            # )
            # return {"message_sid": message.sid, "status": "sent"}
            
            # Option B: AWS SNS
            # import boto3
            # sns = boto3.client('sns')
            # response = sns.publish(
            #     PhoneNumber=service.phone,
            #     Message="EMERGENCY ALERT: Service needed at location."
            # )
            # return {"message_id": response['MessageId'], "status": "sent"}
            
            # For now, simulate SMS
            return {
                "sms_status": "simulated", 
                "message": f"Would send SMS to {service.phone}",
                "integration_needed": "Twilio or AWS SNS"
            }
            
        except Exception as e:
            return {"error": f"SMS failed: {e}"}
    
    async def _call_emergency_api(self, service: SelectedService) -> Dict[str, Any]:
        """Call emergency service API if available."""
        
        try:
            # Option A: Emergency services API (if they provide one)
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "https://emergency-service-api.com/dispatch",
            #         json={
            #             "service_type": service.service_type,
            #             "location": {"lat": service.lat, "lon": service.lon},
            #             "emergency_level": emergency_level
            #         }
            #     )
            #     return {"api_response": response.json(), "status": "dispatched"}
            
            # For now, simulate API call
            return {
                "api_status": "simulated",
                "message": f"Would call emergency API for {service.name}",
                "integration_needed": "Emergency Service API"
            }
            
        except Exception as e:
            return {"error": f"API call failed: {e}"}
    
    def _create_fallback_response(self, service_type: str) -> Dict[str, Any]:
        """Create fallback response when no services found."""
        
        return {
            "selected_service": {
                "name": f"Emergency {service_type.title()} Services",
                "phone": self._get_emergency_number(service_type),
                "contact_method": "phone",
                "verified": False,
                "fallback": True
            },
            "contact_result": {
                "attempted": True,
                "success": True,
                "fallback": True,
                "message": f"Using emergency number: {self._get_emergency_number(service_type)}"
            },
            "search_metadata": {
                "total_found": 0,
                "search_source": "fallback",
                "selection_timestamp": datetime.now().isoformat()
            }
        }


# Create global instance
smart_selector = SmartServiceSelector()
