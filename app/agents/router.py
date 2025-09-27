"""Coordinator that emulates LangGraph routing between agents."""

from __future__ import annotations

import logging
from typing import Dict

from app.agents.base import AgentContext, AgentError, BaseServiceAgent
from app.agents.disaster_agent import DisasterServiceAgent
from app.agents.front_agent import FrontDispatcherAgent
from app.agents.medical_agent import MedicalServiceAgent
from app.agents.police_agent import PoliceServiceAgent
from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceAgentResponse, ServiceType

logger = logging.getLogger(__name__)


class DispatchRouter:
    """High-level orchestrator matching the LangGraph topology requirements."""

    def __init__(self) -> None:
        self.front_agent = FrontDispatcherAgent()
        self.service_agents: Dict[ServiceType, BaseServiceAgent] = {
            ServiceType.MEDICAL: MedicalServiceAgent(),
            ServiceType.POLICE: PoliceServiceAgent(),
            ServiceType.DISASTER: DisasterServiceAgent(),
        }

    def process(self, request: DispatchRequest, trace_id: str) -> tuple[FrontAgentOutput, ServiceAgentResponse]:
        logger.info("Processing dispatch request", extra={"trace_id": trace_id, "userid": request.userid})
        front_output = self.front_agent.run(request)
        logger.info(
            "Front agent output",
            extra={
                "trace_id": trace_id,
                "selected_service": front_output.selected_service.value,
                "urgency": front_output.urgency,
            },
        )

        agent = self.service_agents.get(front_output.selected_service)
        if not agent:
            raise AgentError(f"Unsupported service: {front_output.selected_service}")

        context = AgentContext(request=request, trace_id=trace_id, front_output=front_output)
        service_response = agent.run(context, front_output)
        logger.info(
            "Service agent response",
            extra={
                "trace_id": trace_id,
                "service": service_response.service.value,
                "subservice": service_response.subservice,
            },
        )
        return front_output, service_response
