"""Emergency calling simulator for PoC demonstration."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CallStatus(Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    DISPATCHED = "dispatched"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class CallResult:
    """Result of an emergency service call."""
    service_name: str
    phone_number: str
    call_status: CallStatus
    call_duration: int  # seconds
    response_time: int  # seconds to answer
    dispatched: bool
    eta_minutes: int
    call_id: str
    timestamp: datetime
    notes: str


class EmergencyCallingSimulator:
    """Simulates emergency service calling for PoC demonstration."""
    
    def __init__(self):
        self.call_logs: List[CallResult] = []
        self.call_counter = 1
    
    async def simulate_emergency_call(
        self,
        service_name: str,
        phone_number: str,
        service_type: str,
        emergency_level: int = 1,
        location: Dict[str, float] = None,
        emergency_details: str = ""
    ) -> CallResult:
        """Simulate calling an emergency service."""
        
        call_id = f"CALL-{self.call_counter:04d}"
        self.call_counter += 1
        
        logger.info(f"Simulating emergency call to {service_name} ({phone_number})")
        
        # Simulate call progression
        call_result = await self._simulate_call_progression(
            service_name, phone_number, service_type, emergency_level, call_id
        )
        
        self.call_logs.append(call_result)
        
        return call_result
    
    async def _simulate_call_progression(
        self, 
        service_name: str, 
        phone_number: str, 
        service_type: str, 
        emergency_level: int,
        call_id: str
    ) -> CallResult:
        """Simulate the progression of an emergency call."""
        
        start_time = datetime.now()
        
        # Simulate call initiation
        await asyncio.sleep(0.5)  # Simulate network delay
        logger.info(f"[{call_id}] Call initiated to {service_name}")
        
        # Simulate ringing
        await asyncio.sleep(random.uniform(2, 8))  # Ringing time
        ring_time = datetime.now()
        logger.info(f"[{call_id}] Phone ringing...")
        
        # Determine if call is answered (higher success rate for emergency services)
        answer_probability = 0.85 if emergency_level == 1 else 0.75
        is_answered = random.random() < answer_probability
        
        if is_answered:
            # Call answered
            response_time = (ring_time - start_time).seconds
            logger.info(f"[{call_id}] Call answered after {response_time} seconds")
            
            # Simulate dispatch decision
            await asyncio.sleep(random.uniform(1, 3))  # Conversation time
            
            # High probability of dispatch for emergency services
            dispatch_probability = 0.95 if emergency_level == 1 else 0.85
            is_dispatched = random.random() < dispatch_probability
            
            if is_dispatched:
                # Calculate realistic ETA based on service type and emergency level
                eta_minutes = self._calculate_realistic_eta(service_type, emergency_level)
                
                logger.info(f"[{call_id}] Emergency units dispatched! ETA: {eta_minutes} minutes")
                
                # Simulate call completion
                await asyncio.sleep(random.uniform(0.5, 1.5))
                call_duration = (datetime.now() - start_time).seconds
                
                return CallResult(
                    service_name=service_name,
                    phone_number=phone_number,
                    call_status=CallStatus.DISPATCHED,
                    call_duration=call_duration,
                    response_time=response_time,
                    dispatched=True,
                    eta_minutes=eta_minutes,
                    call_id=call_id,
                    timestamp=start_time,
                    notes=f"Emergency units dispatched. ETA: {eta_minutes} minutes."
                )
            else:
                # Call answered but no dispatch
                logger.info(f"[{call_id}] Call answered but no dispatch (busy/other reasons)")
                
                return CallResult(
                    service_name=service_name,
                    phone_number=phone_number,
                    call_status=CallStatus.ANSWERED,
                    call_duration=(datetime.now() - start_time).seconds,
                    response_time=response_time,
                    dispatched=False,
                    eta_minutes=0,
                    call_id=call_id,
                    timestamp=start_time,
                    notes="Service contacted but no units available for dispatch."
                )
        else:
            # Call not answered
            logger.info(f"[{call_id}] Call not answered - trying backup options")
            
            return CallResult(
                service_name=service_name,
                phone_number=phone_number,
                call_status=CallStatus.FAILED,
                call_duration=(datetime.now() - start_time).seconds,
                response_time=0,
                dispatched=False,
                eta_minutes=0,
                call_id=call_id,
                timestamp=start_time,
                notes="Call not answered. Will try backup services or SMS."
            )
    
    def _calculate_realistic_eta(self, service_type: str, emergency_level: int) -> int:
        """Calculate realistic ETA based on service type and emergency level."""
        
        base_etas = {
            "medical": {"high": (5, 12), "medium": (8, 18), "low": (12, 25)},
            "police": {"high": (3, 8), "medium": (5, 12), "low": (8, 20)},
            "fire": {"high": (4, 10), "medium": (6, 15), "low": (10, 25)},
            "disaster": {"high": (5, 15), "medium": (8, 20), "low": (15, 35)}
        }
        
        level_map = {1: "high", 2: "medium", 3: "low"}
        level = level_map.get(emergency_level, "medium")
        
        if service_type in base_etas:
            min_eta, max_eta = base_etas[service_type][level]
            return random.randint(min_eta, max_eta)
        
        return random.randint(8, 20)  # Default range
    
    async def simulate_sms_notification(
        self,
        service_name: str,
        phone_number: str,
        emergency_details: str
    ) -> Dict[str, Any]:
        """Simulate sending SMS to emergency service."""
        
        logger.info(f"Simulating SMS to {service_name} ({phone_number})")
        
        # Simulate SMS delivery delay
        await asyncio.sleep(random.uniform(1, 3))
        
        # High delivery success rate for SMS
        delivery_success = random.random() < 0.92
        
        if delivery_success:
            logger.info(f"SMS delivered successfully to {service_name}")
            
            # Simulate response time
            response_time = random.randint(30, 180)  # 30 seconds to 3 minutes
            
            return {
                "status": "delivered",
                "message_id": f"SMS-{random.randint(1000, 9999)}",
                "delivery_time": datetime.now(),
                "response_expected": response_time,
                "success": True
            }
        else:
            logger.info(f"SMS delivery failed to {service_name}")
            return {
                "status": "failed",
                "message_id": None,
                "delivery_time": None,
                "response_expected": 0,
                "success": False
            }
    
    async def simulate_multi_service_coordination(
        self,
        services: List[Dict[str, Any]],
        emergency_type: str,
        emergency_level: int
    ) -> Dict[str, Any]:
        """Simulate coordinating multiple emergency services."""
        
        logger.info(f"Simulating multi-service coordination for {emergency_type} emergency")
        
        coordination_results = {}
        
        for service in services:
            service_name = service["name"]
            phone_number = service["phone"]
            service_type = service["type"]
            
            # Simulate calling each service
            call_result = await self.simulate_emergency_call(
                service_name=service_name,
                phone_number=phone_number,
                service_type=service_type,
                emergency_level=emergency_level
            )
            
            coordination_results[service_type] = call_result
        
        # Calculate overall coordination success
        successful_dispatches = sum(1 for result in coordination_results.values() if result.dispatched)
        total_services = len(coordination_results)
        
        coordination_success_rate = successful_dispatches / total_services
        
        return {
            "coordination_id": f"COORD-{random.randint(1000, 9999)}",
            "emergency_type": emergency_type,
            "emergency_level": emergency_level,
            "services_contacted": total_services,
            "services_dispatched": successful_dispatches,
            "success_rate": coordination_success_rate,
            "results": coordination_results,
            "overall_status": "successful" if coordination_success_rate >= 0.5 else "partial",
            "timestamp": datetime.now()
        }
    
    def get_call_statistics(self) -> Dict[str, Any]:
        """Get statistics about all calls made."""
        
        if not self.call_logs:
            return {"total_calls": 0, "message": "No calls made yet"}
        
        total_calls = len(self.call_logs)
        successful_calls = sum(1 for call in self.call_logs if call.dispatched)
        avg_response_time = sum(call.response_time for call in self.call_logs) / total_calls
        avg_call_duration = sum(call.call_duration for call in self.call_logs) / total_calls
        
        return {
            "total_calls": total_calls,
            "successful_dispatches": successful_calls,
            "success_rate": successful_calls / total_calls,
            "average_response_time": round(avg_response_time, 1),
            "average_call_duration": round(avg_call_duration, 1),
            "recent_calls": self.call_logs[-5:]  # Last 5 calls
        }


# Create global instance
calling_simulator = EmergencyCallingSimulator()
