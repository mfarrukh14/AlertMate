"""Mock police service integrations."""

from __future__ import annotations

from typing import Dict


def dispatch_unit(userid: str, location: str) -> Dict[str, object]:
    return {
        "dispatch_id": f"POL-{userid[:4].upper()}-01",
        "eta_min": 8,
        "units": ["RapidResponse-7"],
    }


def create_incident_report(userid: str, narrative: str) -> Dict[str, object]:
    return {
        "report_number": f"IR-{userid[:4].upper()}-{abs(hash(narrative)) % 10000:04d}",
        "status": "submitted",
    }
