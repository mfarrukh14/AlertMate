"""Enhanced police service with hybrid data sources and real-time capabilities."""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from datetime import datetime

from app.services.hybrid_service_discovery import HybridServiceDiscovery

logger = logging.getLogger(__name__)


class EnhancedPoliceService:
    """Enhanced police service with hybrid data sources."""
    
    def __init__(self):
        self.discovery = HybridServiceDiscovery()
    
    async def dispatch_unit(self, userid: str, location: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """Create enhanced police dispatch with real-time data."""
        
        try:
            # If coordinates provided, use them; otherwise try to geocode location
            if lat is None or lon is None:
                lat, lon = await self._geocode_location(location)
            
            # Find nearby police stations
            search_result = await self.discovery.find_emergency_services(
                lat=lat,
                lon=lon,
                service_type="police",
                radius_km=30,
                max_results=5
            )
            
            if not search_result.services:
                logger.warning("No police stations found, using fallback")
                return self._create_fallback_dispatch(userid, location)
            
            # Select best police station
            best_station = search_result.services[0]
            
            # Calculate real-time ETA
            eta_minutes = await self.discovery.calculate_real_eta(
                (lat, lon),
                (best_station.lat, best_station.lon)
            )
            
            # Create enhanced dispatch packet
            dispatch_packet = {
                "dispatch_id": f"POL-{userid[:4].upper()}-{best_station.name.split()[0].upper()}",
                "eta_min": eta_minutes,
                "units": [f"RapidResponse-{userid[:4].upper()}"],
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
                f"Enhanced police dispatch created: {dispatch_packet['dispatch_id']} "
                f"to {best_station.name} (ETA: {eta_minutes}min, Source: {search_result.source})"
            )
            
            return dispatch_packet
            
        except Exception as e:
            logger.error(f"Enhanced police dispatch failed: {e}")
            return self._create_fallback_dispatch(userid, location)
    
    async def create_incident_report(self, userid: str, narrative: str, location: str = None) -> Dict[str, Any]:
        """Create enhanced incident report with location data."""
        
        try:
            report_data = {
                "report_number": f"IR-{userid[:4].upper()}-{abs(hash(narrative)) % 10000:04d}",
                "status": "submitted",
                "narrative": narrative,
                "location": location,
                "timestamp": datetime.now().isoformat(),
                "user_id": userid
            }
            
            # If location provided, try to geocode it
            if location:
                try:
                    lat, lon = await self._geocode_location(location)
                    report_data["coordinates"] = {"lat": lat, "lon": lon}
                    
                    # Find nearest police station for report assignment
                    search_result = await self.discovery.find_emergency_services(
                        lat=lat,
                        lon=lon,
                        service_type="police",
                        radius_km=50,
                        max_results=1
                    )
                    
                    if search_result.services:
                        nearest_station = search_result.services[0]
                        report_data["assigned_station"] = {
                            "name": nearest_station.name,
                            "phone": nearest_station.phone,
                            "distance_km": nearest_station.distance_km
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to geocode location for incident report: {e}")
            
            logger.info(f"Incident report created: {report_data['report_number']}")
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to create incident report: {e}")
            return {
                "report_number": f"IR-{userid[:4].upper()}-ERROR",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
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
    
    def _create_fallback_dispatch(self, userid: str, location: str) -> Dict[str, Any]:
        """Create fallback dispatch packet using original system."""
        
        try:
            from app.services.police import dispatch_unit
            return dispatch_unit(userid, location)
        except Exception:
            # Ultimate fallback
            return {
                "dispatch_id": f"POL-{userid[:4].upper()}-FALLBACK",
                "eta_min": 15,
                "units": ["Emergency-Response"],
                "destination": {
                    "name": "Emergency Police Services",
                    "phone": "15",
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
enhanced_police = EnhancedPoliceService()

# Backward compatibility functions
async def dispatch_unit(userid: str, location: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
    """Backward compatible police dispatch function."""
    return await enhanced_police.dispatch_unit(userid, location, lat, lon)

async def create_incident_report(userid: str, narrative: str, location: str = None) -> Dict[str, Any]:
    """Backward compatible incident report function."""
    return await enhanced_police.create_incident_report(userid, narrative, location)
