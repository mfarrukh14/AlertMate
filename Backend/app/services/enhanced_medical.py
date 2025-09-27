"""Enhanced medical service with hybrid data sources and real-time capabilities."""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime

from app.services.hybrid_service_discovery import HybridServiceDiscovery
from app.services.google_api_client import ServiceLocation

logger = logging.getLogger(__name__)


class EnhancedMedicalService:
    """Enhanced medical service with hybrid data sources."""
    
    def __init__(self):
        self.discovery = HybridServiceDiscovery()
    
    async def ambulance_dispatch_packet(self, userid: str, user_lat: float, user_lon: float) -> Dict[str, Any]:
        """Create enhanced ambulance dispatch packet with real-time data."""
        
        try:
            # Find nearby hospitals using hybrid discovery
            search_result = await self.discovery.find_emergency_services(
                lat=user_lat,
                lon=user_lon,
                service_type="medical",
                radius_km=25,
                max_results=5
            )
            
            if not search_result.services:
                logger.warning("No hospitals found, using fallback")
                return self._create_fallback_dispatch(userid, user_lat, user_lon)
            
            # Select best hospital
            best_hospital = search_result.services[0]
            
            # Calculate real-time ETA
            eta_minutes = await self.discovery.calculate_real_eta(
                (user_lat, user_lon),
                (best_hospital.lat, best_hospital.lon)
            )
            
            # Create enhanced dispatch packet
            dispatch_packet = {
                "dispatch_reference": f"AMB-{userid[:4].upper()}-{best_hospital.name.split()[0].upper()}",
                "destination": {
                    "name": best_hospital.name,
                    "lat": best_hospital.lat,
                    "lon": best_hospital.lon,
                    "address": best_hospital.address,
                    "phone": best_hospital.phone,
                    "rating": best_hospital.rating,
                    "emergency_capability": best_hospital.emergency_capability,
                    "verified": best_hospital.verified,
                    "place_id": best_hospital.place_id
                },
                "eta_minutes": eta_minutes,
                "distance_km": best_hospital.distance_km,
                "ranked_options": [
                    {
                        "name": hospital.name,
                        "lat": hospital.lat,
                        "lon": hospital.lon,
                        "phone": hospital.phone,
                        "distance_km": hospital.distance_km,
                        "eta_minutes": await self.discovery.calculate_real_eta(
                            (user_lat, user_lon),
                            (hospital.lat, hospital.lon)
                        ),
                        "rating": hospital.rating,
                        "emergency_capability": hospital.emergency_capability,
                        "verified": hospital.verified
                    }
                    for hospital in search_result.services[1:4]  # Next 3 options
                ],
                "instructions": self._get_medical_instructions(best_hospital.emergency_capability),
                "dispatch_metadata": {
                    "search_source": search_result.source,
                    "search_time_seconds": search_result.search_time,
                    "cache_hit": search_result.cache_hit,
                    "fallback_used": search_result.fallback_used,
                    "total_hospitals_found": len(search_result.services),
                    "dispatch_timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(
                f"Enhanced ambulance dispatch created: {dispatch_packet['dispatch_reference']} "
                f"to {best_hospital.name} (ETA: {eta_minutes}min, Source: {search_result.source})"
            )
            
            return dispatch_packet
            
        except Exception as e:
            logger.error(f"Enhanced ambulance dispatch failed: {e}")
            return self._create_fallback_dispatch(userid, user_lat, user_lon)
    
    async def nearest_hospitals(self, user_lat: float, user_lon: float, limit: int = 3) -> List[Dict[str, Any]]:
        """Get nearest hospitals with enhanced data."""
        
        try:
            search_result = await self.discovery.find_emergency_services(
                lat=user_lat,
                lon=user_lon,
                service_type="medical",
                radius_km=50,
                max_results=limit
            )
            
            hospitals = []
            for hospital in search_result.services[:limit]:
                hospital_data = {
                    "name": hospital.name,
                    "lat": hospital.lat,
                    "lon": hospital.lon,
                    "address": hospital.address,
                    "phone": hospital.phone,
                    "distance_km": hospital.distance_km,
                    "rating": hospital.rating,
                    "emergency_capability": hospital.emergency_capability,
                    "verified": hospital.verified,
                    "source": hospital.source,
                    "eta_minutes": await self.discovery.calculate_real_eta(
                        (user_lat, user_lon),
                        (hospital.lat, hospital.lon)
                    )
                }
                hospitals.append(hospital_data)
            
            return hospitals
            
        except Exception as e:
            logger.error(f"Failed to get nearest hospitals: {e}")
            return self._get_fallback_hospitals(user_lat, user_lon, limit)
    
    def _create_fallback_dispatch(self, userid: str, user_lat: float, user_lon: float) -> Dict[str, Any]:
        """Create fallback dispatch packet using hardcoded data."""
        
        # Use original hardcoded hospitals as fallback
        from app.services.medical import select_best_hospital, ambulance_dispatch_packet
        
        try:
            return ambulance_dispatch_packet(userid, user_lat, user_lon)
        except Exception:
            # Ultimate fallback
            return {
                "dispatch_reference": f"AMB-{userid[:4].upper()}-FALLBACK",
                "destination": {
                    "name": "Emergency Medical Services",
                    "lat": user_lat,
                    "lon": user_lon,
                    "phone": "1122",
                    "emergency_capability": 8,
                    "verified": False
                },
                "eta_minutes": 15,
                "distance_km": 0,
                "ranked_options": [],
                "instructions": "Emergency medical services have been notified. Please stay calm and provide first aid if possible.",
                "dispatch_metadata": {
                    "search_source": "hardcoded_fallback",
                    "fallback_used": True,
                    "dispatch_timestamp": datetime.now().isoformat()
                }
            }
    
    def _get_fallback_hospitals(self, user_lat: float, user_lon: float, limit: int) -> List[Dict[str, Any]]:
        """Get fallback hospitals using original system."""
        
        try:
            from app.services.medical import nearest_hospitals
            return nearest_hospitals(user_lat, user_lon, limit)
        except Exception:
            # Ultimate fallback
            return [
                {
                    "name": "Emergency Medical Services",
                    "lat": user_lat,
                    "lon": user_lon,
                    "phone": "1122",
                    "distance_km": 0,
                    "eta_minutes": 15,
                    "emergency_capability": 8,
                    "verified": False,
                    "source": "hardcoded_fallback"
                }
            ]
    
    def _get_medical_instructions(self, emergency_capability: int) -> str:
        """Get medical instructions based on hospital capability."""
        
        if emergency_capability >= 9:
            return "Advanced emergency facility. Keep patient stable; monitor breathing and vital signs. Do not move patient unless in immediate danger."
        elif emergency_capability >= 7:
            return "Medical facility with emergency capabilities. Keep patient stable; monitor breathing. Apply pressure to any bleeding."
        else:
            return "Medical facility. Keep patient comfortable and stable. Monitor breathing. Call 1122 for emergency services if condition worsens."


# Create global instance for backward compatibility
enhanced_medical = EnhancedMedicalService()

# Backward compatibility functions
async def ambulance_dispatch_packet(userid: str, user_lat: float, user_lon: float) -> Dict[str, Any]:
    """Backward compatible ambulance dispatch function."""
    return await enhanced_medical.ambulance_dispatch_packet(userid, user_lat, user_lon)

async def nearest_hospitals(user_lat: float, user_lon: float, limit: int = 3) -> List[Dict[str, Any]]:
    """Backward compatible nearest hospitals function."""
    return await enhanced_medical.nearest_hospitals(user_lat, user_lon, limit)
