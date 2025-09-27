"""Mock medical service integrations."""

from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Dict, List, Literal, Tuple


HospitalService = Literal["general", "cardiology", "orthopedics", "emergency"]


_HOSPITAL_DIRECTORY: List[Dict[str, object]] = [
    {
        "name": "Karachi General Hospital",
        "lat": 24.8615,
        "lon": 67.0099,
        "phone": "+92-21-1234567",
        "services": {"general", "orthopedics", "emergency"},
        "rating": 4.5,
        "beds_available": 14,
    },
    {
        "name": "Clifton Care Clinic",
        "lat": 24.8128,
        "lon": 67.0334,
        "phone": "+92-21-7654321",
        "services": {"general", "cardiology"},
        "rating": 4.2,
        "beds_available": 6,
    },
    {
        "name": "Seaview Medical Center",
        "lat": 24.8141,
        "lon": 67.0479,
        "phone": "+92-21-1112223",
        "services": {"emergency", "general"},
        "rating": 3.8,
        "beds_available": 2,
    },
    {
        "name": "Dow University Hospital",
        "lat": 24.8864,
        "lon": 67.0743,
        "phone": "+92-21-5566778",
        "services": {"general", "orthopedics", "cardiology", "emergency"},
        "rating": 4.7,
        "beds_available": 18,
    },
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(r * c, 2)


def rank_hospitals(user_lat: float, user_lon: float, *, limit: int = 3) -> List[Dict[str, object]]:
    ranked = []
    for hospital in _HOSPITAL_DIRECTORY:
        distance = _haversine_km(user_lat, user_lon, hospital["lat"], hospital["lon"])
        score = hospital["rating"] * 2 + hospital["beds_available"] - distance
        ranked.append({**hospital, "distance_km": distance, "score": round(score, 2)})

    ranked.sort(key=lambda item: (-item["score"], item["distance_km"]))
    return ranked[:limit]


def select_best_hospital(user_lat: float, user_lon: float, service: HospitalService = "general") -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    ranked = rank_hospitals(user_lat, user_lon, limit=len(_HOSPITAL_DIRECTORY))
    for hospital in ranked:
        if service in hospital["services"] and hospital["beds_available"] > 0:
            return hospital, ranked
    return ranked[0], ranked


def ambulance_dispatch_packet(userid: str, user_lat: float, user_lon: float) -> Dict[str, object]:
    hospital, ranked = select_best_hospital(user_lat, user_lon, "emergency")
    return {
        "dispatch_reference": f"AMB-{userid[:4].upper()}-{hospital['name'].split()[0].upper()}",
        "destination": hospital,
        "eta_minutes": max(6, int(hospital["distance_km"] * 1.8) or 8),
        "ranked_options": ranked[:3],
        "instructions": "Keep patient stable; monitor breathing",
    }


def nearest_hospitals(user_lat: float, user_lon: float, limit: int = 3) -> List[Dict[str, object]]:
    return rank_hospitals(user_lat, user_lon, limit=limit)
