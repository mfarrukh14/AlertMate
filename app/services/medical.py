"""Mock medical service integrations."""

from __future__ import annotations

from typing import Dict, List

_HOSPITAL_DIRECTORY: List[Dict[str, object]] = [
    {
        "name": "Karachi General Hospital",
        "distance_km": 1.2,
        "phone": "+92-21-1234567",
        "capacity_ok": True,
    },
    {
        "name": "Clifton Care Clinic",
        "distance_km": 2.5,
        "phone": "+92-21-7654321",
        "capacity_ok": True,
    },
    {
        "name": "Seaview Medical Center",
        "distance_km": 3.1,
        "phone": "+92-21-1112223",
        "capacity_ok": False,
    },
]


def ambulance_dispatch_packet(userid: str, location: str) -> Dict[str, object]:
    hospital = _HOSPITAL_DIRECTORY[0]
    return {
        "dispatch_reference": f"AMB-{userid[:4].upper()}-{hospital['name'].split()[0].upper()}",
        "destination": hospital,
        "eta_minutes": 12,
        "instructions": "Keep patient stable; monitor breathing",
    }


def nearest_hospitals(limit: int = 3) -> List[Dict[str, object]]:
    return _HOSPITAL_DIRECTORY[:limit]
