"""Hybrid service discovery system combining local data and Google APIs."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from app.services.google_api_client import GooglePlacesAPI, GoogleMapsAPI, ServiceLocation
from app.services.medical import _haversine_km

logger = logging.getLogger(__name__)


@dataclass
class ServiceSearchResult:
    """Result from service discovery with metadata."""
    services: List[ServiceLocation]
    source: str
    search_time: float
    cache_hit: bool = False
    fallback_used: bool = False


class DataValidator:
    """Validate and clean service data."""
    
    @staticmethod
    def validate_service(service: Dict[str, Any]) -> bool:
        """Validate a service entry has required fields."""
        required_fields = ["name", "lat", "lon"]
        
        for field in required_fields:
            if not service.get(field):
                return False
                
        # Validate coordinates
        lat = service.get("lat")
        lon = service.get("lon")
        
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return False
            
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return False
            
        return True
    
    @staticmethod
    def clean_service_data(service: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize service data."""
        cleaned = service.copy()
        
        # Normalize phone numbers
        if cleaned.get("contact"):
            phone = cleaned["contact"]
            # Remove non-digit characters except +
            cleaned["phone"] = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Ensure name is string and clean
        if cleaned.get("name"):
            cleaned["name"] = str(cleaned["name"]).strip()
        
        # Convert coordinates to float
        for coord in ["lat", "lon"]:
            if cleaned.get(coord):
                try:
                    cleaned[coord] = float(cleaned[coord])
                except (ValueError, TypeError):
                    cleaned[coord] = None
        
        return cleaned


class LocalServicesLoader:
    """Load and manage local services data from services.json."""
    
    def __init__(self, data_file_path: str = "Backend/data/services.json"):
        self.data_file_path = data_file_path
        self._cached_data: Optional[Dict] = None
        self._last_loaded: Optional[datetime] = None
        self.validator = DataValidator()
    
    async def load_services_data(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load services data from JSON file with caching."""
        
        if (self._cached_data and not force_reload and 
            self._last_loaded and 
            datetime.now() - self._last_loaded < timedelta(hours=1)):
            return self._cached_data
        
        try:
            if not os.path.exists(self.data_file_path):
                logger.warning(f"Services data file not found: {self.data_file_path}")
                return {"health": {"candidates": []}}
            
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clean and validate data
            cleaned_data = await self._clean_and_validate_data(data)
            
            self._cached_data = cleaned_data
            self._last_loaded = datetime.now()
            
            logger.info(f"Loaded {sum(len(cat.get('candidates', [])) for cat in cleaned_data.values())} services from local data")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Failed to load services data: {e}")
            return {"health": {"candidates": []}}
    
    async def _clean_and_validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate the loaded services data."""
        cleaned_data = {}
        
        for category, category_data in data.items():
            if not isinstance(category_data, dict) or "candidates" not in category_data:
                continue
                
            cleaned_candidates = []
            
            for service in category_data["candidates"]:
                cleaned_service = self.validator.clean_service_data(service)
                
                if self.validator.validate_service(cleaned_service):
                    # Convert to ServiceLocation format
                    service_location = ServiceLocation(
                        name=cleaned_service["name"],
                        lat=cleaned_service["lat"],
                        lon=cleaned_service["lon"],
                        phone=cleaned_service.get("phone"),
                        address=cleaned_service.get("address"),
                        source="local_data",
                        verified=False,
                        emergency_capability=self._estimate_emergency_capability(cleaned_service)
                    )
                    cleaned_candidates.append(service_location)
            
            cleaned_data[category] = {"candidates": cleaned_candidates}
        
        return cleaned_data
    
    def _estimate_emergency_capability(self, service: Dict[str, Any]) -> int:
        """Estimate emergency capability for local services."""
        name = service.get("name", "").lower()
        
        emergency_keywords = {
            "emergency": 10,
            "hospital": 9,
            "medical": 8,
            "clinic": 6,
            "health": 7,
            "care": 5,
            "nursing": 6
        }
        
        max_score = 5  # Default capability
        
        for keyword, score in emergency_keywords.items():
            if keyword in name:
                max_score = max(max_score, score)
        
        return max_score
    
    def get_services_by_category(self, category: str, lat: float, lon: float, radius_km: float = 50) -> List[ServiceLocation]:
        """Get services from a specific category within radius."""
        if not self._cached_data:
            return []
        
        category_data = self._cached_data.get(category, {})
        candidates = category_data.get("candidates", [])
        
        nearby_services = []
        
        for service in candidates:
            distance = _haversine_km(lat, lon, service.lat, service.lon)
            
            if distance <= radius_km:
                service.distance_km = distance
                nearby_services.append(service)
        
        # Sort by distance
        nearby_services.sort(key=lambda x: x.distance_km)
        
        return nearby_services


class HybridServiceDiscovery:
    """Main hybrid service discovery system with multiple data sources."""
    
    def __init__(self):
        self.google_places = GooglePlacesAPI()
        self.google_maps = GoogleMapsAPI()
        self.local_loader = LocalServicesLoader()
        self.cache: Dict[str, Tuple[List[ServiceLocation], datetime]] = {}
        self.cache_ttl = {
            "hospitals": timedelta(hours=1),
            "police": timedelta(hours=2),
            "fire": timedelta(hours=2),
            "disaster": timedelta(hours=4)
        }
    
    async def find_emergency_services(
        self, 
        lat: float, 
        lon: float, 
        service_type: str,
        radius_km: float = 25,
        max_results: int = 10
    ) -> ServiceSearchResult:
        """Find emergency services using hybrid approach with fallbacks."""
        
        start_time = datetime.now()
        cache_key = f"{service_type}_{lat}_{lon}_{radius_km}"
        
        # Check cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return ServiceSearchResult(
                services=cached_result,
                source="cache",
                search_time=(datetime.now() - start_time).total_seconds(),
                cache_hit=True
            )
        
        services = []
        source = "hybrid"
        fallback_used = False
        
        try:
            # Primary: Try Google Places API
            google_services = await self._search_google_places(lat, lon, service_type, radius_km)
            if google_services:
                services.extend(google_services)
                source = "google_places"
                logger.info(f"Found {len(google_services)} {service_type} services via Google Places")
            
            # Secondary: Try local data
            local_services = await self._search_local_data(lat, lon, service_type, radius_km)
            if local_services:
                services.extend(local_services)
                if source == "hybrid":
                    source = "local_data"
                else:
                    source = "hybrid"
                logger.info(f"Found {len(local_services)} {service_type} services via local data")
            
            # Tertiary: Use hardcoded fallback if no services found
            if not services:
                services = await self._get_hardcoded_fallback(lat, lon, service_type)
                source = "hardcoded_fallback"
                fallback_used = True
                logger.warning(f"Using hardcoded fallback for {service_type} services")
            
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            services = await self._get_hardcoded_fallback(lat, lon, service_type)
            source = "hardcoded_fallback"
            fallback_used = True
        
        # Remove duplicates and rank services
        services = self._deduplicate_and_rank_services(services, lat, lon)
        
        # Limit results
        services = services[:max_results]
        
        # Cache results
        self._cache_results(cache_key, services)
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return ServiceSearchResult(
            services=services,
            source=source,
            search_time=search_time,
            fallback_used=fallback_used
        )
    
    async def _search_google_places(self, lat: float, lon: float, service_type: str, radius_km: float) -> List[ServiceLocation]:
        """Search Google Places API for services."""
        
        # Map service types to Google Places types
        place_type_mapping = {
            "medical": "hospital",
            "health": "hospital",
            "hospital": "hospital",
            "police": "police",
            "fire": "fire_station",
            "disaster": "fire_station"  # Use fire stations for disaster response
        }
        
        place_type = place_type_mapping.get(service_type, "hospital")
        radius_meters = int(radius_km * 1000)
        
        # Search for emergency services
        services = await self.google_places.nearby_search(
            location=f"{lat},{lon}",
            radius=radius_meters,
            type=place_type,
            keyword="emergency" if service_type in ["medical", "health", "hospital"] else None
        )
        
        # Enrich with place details
        enriched_services = []
        for service in services:
            if service.place_id:
                details = await self.google_places.get_place_details(service.place_id)
                if details:
                    service.address = details.get("formatted_address")
                    service.phone = details.get("formatted_phone_number")
                    service.opening_hours = details.get("opening_hours")
            
            enriched_services.append(service)
        
        return enriched_services
    
    async def _search_local_data(self, lat: float, lon: float, service_type: str, radius_km: float) -> List[ServiceLocation]:
        """Search local services data."""
        
        # Load local data
        local_data = await self.local_loader.load_services_data()
        
        # Map service types to local data categories
        category_mapping = {
            "medical": "health",
            "health": "health",
            "hospital": "health",
            "police": "police",
            "fire": "fire",
            "disaster": "disaster"
        }
        
        category = category_mapping.get(service_type, "health")
        
        if category in local_data:
            services = self.local_loader.get_services_by_category(category, lat, lon, radius_km)
            return services
        
        return []
    
    async def _get_hardcoded_fallback(self, lat: float, lon: float, service_type: str) -> List[ServiceLocation]:
        """Get hardcoded fallback services for critical situations."""
        
        fallback_services = {
            "medical": [
                ServiceLocation(
                    name="Karachi General Hospital",
                    lat=24.8615,
                    lon=67.0099,
                    phone="+92-21-1234567",
                    emergency_capability=10,
                    verified=False,
                    source="hardcoded_fallback"
                ),
                ServiceLocation(
                    name="Dow University Hospital",
                    lat=24.8864,
                    lon=67.0743,
                    phone="+92-21-5566778",
                    emergency_capability=9,
                    verified=False,
                    source="hardcoded_fallback"
                )
            ],
            "police": [
                ServiceLocation(
                    name="Karachi Police Emergency",
                    lat=24.8600,
                    lon=67.0100,
                    phone="15",
                    emergency_capability=10,
                    verified=False,
                    source="hardcoded_fallback"
                )
            ],
            "fire": [
                ServiceLocation(
                    name="Karachi Fire Department",
                    lat=24.8500,
                    lon=67.0000,
                    phone="16",
                    emergency_capability=10,
                    verified=False,
                    source="hardcoded_fallback"
                )
            ]
        }
        
        services = fallback_services.get(service_type, [])
        
        # Calculate distances
        for service in services:
            service.distance_km = _haversine_km(lat, lon, service.lat, service.lon)
        
        return services
    
    def _deduplicate_and_rank_services(self, services: List[ServiceLocation], lat: float, lon: float) -> List[ServiceLocation]:
        """Remove duplicates and rank services by relevance."""
        
        # Remove duplicates based on name and coordinates
        seen = set()
        unique_services = []
        
        for service in services:
            key = (service.name.lower().strip(), round(service.lat, 4), round(service.lon, 4))
            if key not in seen:
                seen.add(key)
                unique_services.append(service)
        
        # Calculate distance for all services
        for service in unique_services:
            if not hasattr(service, 'distance_km'):
                service.distance_km = _haversine_km(lat, lon, service.lat, service.lon)
        
        # Calculate ranking score
        for service in unique_services:
            score = (
                service.emergency_capability * 3 +  # Emergency capability weight
                (service.rating or 3.0) * 2 +       # Rating weight
                (10 - min(service.distance_km, 10)) +  # Distance weight (closer is better)
                (2 if service.verified else 0) +    # Verification bonus
                (1 if service.phone else 0)         # Contact info bonus
            )
            service.score = score
        
        # Sort by score (highest first), then by distance
        unique_services.sort(key=lambda x: (-x.score, x.distance_km))
        
        return unique_services
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[ServiceLocation]]:
        """Get services from cache if still valid."""
        
        if cache_key not in self.cache:
            return None
        
        cached_services, cached_time = self.cache[cache_key]
        
        # Determine TTL based on service type
        service_type = cache_key.split('_')[0]
        ttl = self.cache_ttl.get(service_type, timedelta(hours=1))
        
        if datetime.now() - cached_time > ttl:
            del self.cache[cache_key]
            return None
        
        return cached_services
    
    def _cache_results(self, cache_key: str, services: List[ServiceLocation]):
        """Cache search results."""
        self.cache[cache_key] = (services, datetime.now())
    
    async def calculate_real_eta(self, user_location: Tuple[float, float], service_location: Tuple[float, float]) -> int:
        """Calculate real-time ETA using Google Distance Matrix API."""
        
        try:
            origins = [f"{user_location[0]},{user_location[1]}"]
            destinations = [f"{service_location[0]},{service_location[1]}"]
            
            matrix = await self.google_maps.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode="driving",
                traffic_model="best_guess"
            )
            
            if matrix and matrix.get("rows"):
                duration = matrix["rows"][0]["elements"][0].get("duration_in_traffic", {})
                if duration:
                    eta_minutes = max(5, duration["value"] // 60)  # Minimum 5 minutes
                    return eta_minutes
            
        except Exception as e:
            logger.warning(f"Real-time ETA calculation failed: {e}")
        
        # Fallback to distance-based estimation
        distance = _haversine_km(user_location[0], user_location[1], service_location[0], service_location[1])
        return max(6, int(distance * 1.8))  # Rough estimate: 1.8 minutes per km
