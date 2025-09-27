"""Google Cloud Platform API client for emergency services integration."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from app import config

logger = logging.getLogger(__name__)


@dataclass
class ServiceLocation:
    """Standardized service location data structure."""
    name: str
    lat: float
    lon: float
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    place_id: Optional[str] = None
    types: List[str] = None
    opening_hours: Optional[Dict] = None
    emergency_capability: int = 5  # 1-10 scale
    verified: bool = False
    source: str = "google_places"
    last_updated: str = None

    def __post_init__(self):
        if self.types is None:
            self.types = []
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()


class GooglePlacesAPI:
    """Google Places API client for emergency services discovery."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(config, 'GOOGLE_PLACES_API_KEY', None)
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = httpx.AsyncClient(timeout=10.0)
        
    async def nearby_search(
        self, 
        location: str, 
        radius: int = 10000, 
        type: str = "hospital",
        keyword: Optional[str] = None
    ) -> List[ServiceLocation]:
        """Search for nearby places using Google Places API."""
        
        if not self.api_key:
            logger.warning("Google Places API key not configured")
            return []
            
        params = {
            "location": location,
            "radius": radius,
            "type": type,
            "key": self.api_key
        }
        
        if keyword:
            params["keyword"] = keyword
            
        try:
            url = f"{self.base_url}/nearbysearch/json"
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "OK":
                logger.error(f"Google Places API error: {data.get('status')}")
                return []
                
            return self._parse_places_response(data.get("results", []))
            
        except Exception as e:
            logger.error(f"Google Places API request failed: {e}")
            return []
    
    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a place."""
        
        if not self.api_key:
            return None
            
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,rating,opening_hours,types",
            "key": self.api_key
        }
        
        try:
            url = f"{self.base_url}/details/json"
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "OK":
                logger.error(f"Google Places Details API error: {data.get('status')}")
                return None
                
            return data.get("result")
            
        except Exception as e:
            logger.error(f"Google Places Details API request failed: {e}")
            return None
    
    def _parse_places_response(self, results: List[Dict]) -> List[ServiceLocation]:
        """Parse Google Places API response into ServiceLocation objects."""
        
        services = []
        
        for place in results:
            try:
                geometry = place.get("geometry", {})
                location = geometry.get("location", {})
                
                if not location.get("lat") or not location.get("lng"):
                    continue
                    
                service = ServiceLocation(
                    name=place.get("name", "Unknown"),
                    lat=float(location["lat"]),
                    lon=float(location["lng"]),
                    place_id=place.get("place_id"),
                    rating=place.get("rating"),
                    types=place.get("types", []),
                    verified=True,
                    source="google_places"
                )
                
                # Determine emergency capability based on types
                service.emergency_capability = self._calculate_emergency_capability(place.get("types", []))
                
                services.append(service)
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse place data: {e}")
                continue
                
        return services
    
    def _calculate_emergency_capability(self, types: List[str]) -> int:
        """Calculate emergency capability score based on place types."""
        
        emergency_keywords = {
            "hospital": 10,
            "emergency": 10,
            "health": 8,
            "medical": 8,
            "clinic": 6,
            "pharmacy": 4,
            "police": 10,
            "fire_station": 10,
            "ambulance": 9
        }
        
        max_score = 1
        for place_type in types:
            for keyword, score in emergency_keywords.items():
                if keyword in place_type.lower():
                    max_score = max(max_score, score)
                    
        return max_score


class GoogleMapsAPI:
    """Google Maps API client for distance and routing calculations."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(config, 'GOOGLE_MAPS_API_KEY', None)
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.session = httpx.AsyncClient(timeout=15.0)
    
    async def distance_matrix(
        self, 
        origins: List[str], 
        destinations: List[str],
        mode: str = "driving",
        traffic_model: str = "best_guess"
    ) -> Optional[Dict[str, Any]]:
        """Calculate distance and travel time between origins and destinations."""
        
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return None
            
        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "traffic_model": traffic_model,
            "departure_time": "now",
            "key": self.api_key
        }
        
        try:
            url = f"{self.base_url}/distancematrix/json"
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "OK":
                logger.error(f"Google Distance Matrix API error: {data.get('status')}")
                return None
                
            return data
            
        except Exception as e:
            logger.error(f"Google Distance Matrix API request failed: {e}")
            return None
    
    async def geocode(self, address: str) -> Optional[Dict[str, float]]:
        """Geocode an address to get latitude and longitude."""
        
        if not self.api_key:
            return None
            
        params = {
            "address": address,
            "key": self.api_key
        }
        
        try:
            url = f"{self.base_url}/geocode/json"
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") != "OK" or not data.get("results"):
                return None
                
            location = data["results"][0]["geometry"]["location"]
            return {
                "lat": float(location["lat"]),
                "lon": float(location["lng"])
            }
            
        except Exception as e:
            logger.error(f"Google Geocoding API request failed: {e}")
            return None


class GoogleAPIError(Exception):
    """Custom exception for Google API errors."""
    pass
