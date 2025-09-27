"""Mock disaster management service integrations."""

from __future__ import annotations

from typing import Dict, List

_SHELTERS: List[Dict[str, object]] = [
    {
        "name": "City Sports Complex Shelter",
        "distance_km": 2.0,
        "capacity": "available",
    },
    {
        "name": "Community Center Block 5",
        "distance_km": 3.4,
        "capacity": "limited",
    },
    {
        "name": "High School Gym Shelter",
        "distance_km": 5.1,
        "capacity": "available",
    },
]


def evacuation_guidance() -> Dict[str, object]:
    return {
        "shelters": _SHELTERS,
        "instructions": "Move to higher ground and avoid flooded roads.",
    }


def resource_request(resource: str) -> Dict[str, object]:
    return {
        "ticket_id": f"RES-{resource[:3].upper()}-{resource.__hash__() % 10000:04d}",
        "eta_hours": 4,
    }
