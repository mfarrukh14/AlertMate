"""Enhanced fire and disaster service with hybrid data sources and real-time capabilities."""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from datetime import datetime

from app.services.hybrid_service_discovery import HybridServiceDiscovery

logger = logging.getLogger(__name__)


class EnhancedFireService:
    """Enhanced fire and disaster service with hybrid data sources."""
    
    def __init__(self):
        self.discovery = HybridServiceDiscovery()
    
    async def dispatch_fire_units(self, userid: str, location: str, lat: float = None, lon: float = None, emergency_type: str = "fire") -> Dict[str, Any]:
        """Create enhanced fire/disaster dispatch with real-time data."""
        
        try:
            # If coordinates provided, use them; otherwise try to geocode location
            if lat is None or lon is None:
                lat, lon = await self._geocode_location(location)
            
            # Find nearby fire stations
            search_result = await self.discovery.find_emergency_services(
                lat=lat,
                lon=lon,
                service_type="fire",
                radius_km=40,
                max_results=5
            )
            
            if not search_result.services:
                logger.warning("No fire stations found, using fallback")
                return self._create_fallback_dispatch(userid, location, emergency_type)
            
            # Select best fire station
            best_station = search_result.services[0]
            
            # Calculate real-time ETA
            eta_minutes = await self.discovery.calculate_real_eta(
                (lat, lon),
                (best_station.lat, best_station.lon)
            )
            
            # Create enhanced dispatch packet
            dispatch_packet = {
                "dispatch_id": f"FIRE-{userid[:4].upper()}-{best_station.name.split()[0].upper()}",
                "eta_minutes": eta_minutes,
                "units": [f"Fire-Rescue-{userid[:4].upper()}", f"Emergency-Response-{userid[:4].upper()}"],
                "emergency_type": emergency_type,
                "destination": {
                    "name": best_station.name,
                    "lat": best_station.lat,
                    "lon": best_station.lon,
                    "address": best_station.address,
                    "phone": best_station.phone,
                    "rating": best_station.rating,
                    "emergency_capability": best_station.emergency_capability,
                    "verified": best_station.verified,
                    "place_id": best_station.place_id
                },
                "distance_km": best_station.distance_km,
                "backup_stations": [
                    {
                        "name": station.name,
                        "lat": station.lat,
                        "lon": station.lon,
                        "phone": station.phone,
                        "distance_km": station.distance_km,
                        "eta_minutes": await self.discovery.calculate_real_eta(
                            (lat, lon),
                            (station.lat, station.lon)
                        ),
                        "emergency_capability": station.emergency_capability
                    }
                    for station in search_result.services[1:3]  # Next 2 backup stations
                ],
                "dispatch_metadata": {
                    "search_source": search_result.source,
                    "search_time_seconds": search_result.search_time,
                    "cache_hit": search_result.cache_hit,
                    "fallback_used": search_result.fallback_used,
                    "total_stations_found": len(search_result.services),
                    "dispatch_timestamp": datetime.now().isoformat(),
                    "location_string": location
                }
            }
            
            logger.info(
                f"Enhanced fire dispatch created: {dispatch_packet['dispatch_id']} "
                f"to {best_station.name} (ETA: {eta_minutes}min, Type: {emergency_type}, Source: {search_result.source})"
            )
            
            return dispatch_packet
            
        except Exception as e:
            logger.error(f"Enhanced fire dispatch failed: {e}")
            return self._create_fallback_dispatch(userid, location, emergency_type)
    
    async def create_disaster_response(self, userid: str, disaster_type: str, location: str, severity: int = 3) -> Dict[str, Any]:
        """Create disaster response with multiple agency coordination."""
        
        try:
            lat, lon = await self._geocode_location(location)
            
            # Coordinate multiple emergency services
            response_data = {
                "response_id": f"DIS-{userid[:4].upper()}-{disaster_type.upper()}",
                "disaster_type": disaster_type,
                "severity": severity,
                "location": {"name": location, "lat": lat, "lon": lon},
                "timestamp": datetime.now().isoformat(),
                "coordinated_services": []
            }
            
            # Find and dispatch appropriate services based on disaster type
            services_to_dispatch = self._get_services_for_disaster_type(disaster_type)
            
            for service_type in services_to_dispatch:
                try:
                    search_result = await self.discovery.find_emergency_services(
                        lat=lat,
                        lon=lon,
                        service_type=service_type,
                        radius_km=50,
                        max_results=3
                    )
                    
                    if search_result.services:
                        best_service = search_result.services[0]
                        eta = await self.discovery.calculate_real_eta(
                            (lat, lon),
                            (best_service.lat, best_service.lon)
                        )
                        
                        response_data["coordinated_services"].append({
                            "service_type": service_type,
                            "station": {
                                "name": best_service.name,
                                "phone": best_service.phone,
                                "distance_km": best_service.distance_km,
                                "eta_minutes": eta
                            },
                            "status": "dispatched"
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to dispatch {service_type} for disaster: {e}")
                    response_data["coordinated_services"].append({
                        "service_type": service_type,
                        "status": "failed",
                        "error": str(e)
                    })
            
            logger.info(f"Disaster response created: {response_data['response_id']} for {disaster_type}")
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to create disaster response: {e}")
            return {
                "response_id": f"DIS-{userid[:4].upper()}-ERROR",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_services_for_disaster_type(self, disaster_type: str) -> List[str]:
        """Get appropriate emergency services for disaster type."""
        
        disaster_service_mapping = {
            "fire": ["fire"],
            "earthquake": ["fire", "medical", "police"],
            "flood": ["fire", "medical", "police"],
            "storm": ["fire", "police"],
            "explosion": ["fire", "medical", "police"],
            "gas_leak": ["fire", "police"],
            "building_collapse": ["fire", "medical", "police"],
            "chemical_spill": ["fire", "medical", "police"],
            "power_outage": ["police"],
            "default": ["fire", "medical", "police"]
        }
        
        return disaster_service_mapping.get(disaster_type.lower(), disaster_service_mapping["default"])
    
    async def _geocode_location(self, location: str) -> tuple[float, float]:
        """Geocode a location string to coordinates."""
        
        try:
            # Try Google Geocoding API first
            geocoded = await self.discovery.google_maps.geocode(location)
            if geocoded:
                return geocoded["lat"], geocoded["lon"]
        except Exception as e:
            logger.warning(f"Google geocoding failed: {e}")
        
        # Fallback to hardcoded Karachi coordinates
        logger.warning(f"Using fallback coordinates for location: {location}")
        return 24.8607, 67.0011  # Karachi city center
    
    def _create_fallback_dispatch(self, userid: str, location: str, emergency_type: str) -> Dict[str, Any]:
        """Create fallback dispatch packet."""
        
        return {
            "dispatch_id": f"FIRE-{userid[:4].upper()}-FALLBACK",
            "eta_minutes": 20,
            "units": ["Emergency-Fire-Response"],
            "emergency_type": emergency_type,
            "destination": {
                "name": "Emergency Fire Services",
                "phone": "16",
                "emergency_capability": 8,
                "verified": False
            },
            "distance_km": 0,
            "backup_stations": [],
            "dispatch_metadata": {
                "search_source": "hardcoded_fallback",
                "fallback_used": True,
                "dispatch_timestamp": datetime.now().isoformat(),
                "location_string": location
            }
        }


# Create global instance for backward compatibility
enhanced_fire = EnhancedFireService()

# Backward compatibility functions
async def dispatch_fire_units(userid: str, location: str, lat: float = None, lon: float = None, emergency_type: str = "fire") -> Dict[str, Any]:
    """Backward compatible fire dispatch function."""
    return await enhanced_fire.dispatch_fire_units(userid, location, lat, lon, emergency_type)

async def create_disaster_response(userid: str, disaster_type: str, location: str, severity: int = 3) -> Dict[str, Any]:
    """Backward compatible disaster response function."""
    return await enhanced_fire.create_disaster_response(userid, disaster_type, location, severity)
