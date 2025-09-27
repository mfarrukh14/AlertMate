"""Base agent structures for AlertMate's LangGraph-inspired flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceAgentResponse, ServiceType


@dataclass
class AgentContext:
    request: DispatchRequest
    trace_id: str
    front_output: Optional[FrontAgentOutput] = None
    history: Optional[List[dict]] = None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "trace_id": self.trace_id,
            "request": self.request.model_dump(),
        }
        if self.front_output:
            payload["front_output"] = self.front_output.model_dump()
        if self.history:
            payload["history"] = self.history
        return payload


class AgentError(RuntimeError):
    """Raised when an agent fails to complete its task."""


class BaseServiceAgent:
    service_type: ServiceType

    def __init__(self) -> None:
        self.subservices = self.register_subservices()

    def register_subservices(self) -> Mapping[str, Any]:
        raise NotImplementedError("Service agents must register subservices")

    def classify_subservice(
        self, context: AgentContext, front_output: FrontAgentOutput
    ) -> str:
        raise NotImplementedError

    def perform_subservice(
        self, context: AgentContext, subservice: str, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        raise NotImplementedError

    async def perform_subservice_async(
        self, context: AgentContext, subservice: str, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        # Default implementation calls sync method
        return self.perform_subservice(context, subservice, front_output)

    def run(self, context: AgentContext, front_output: FrontAgentOutput) -> ServiceAgentResponse:
        subservice = self.classify_subservice(context, front_output)
        if subservice not in self.subservices:
            raise AgentError(f"Unsupported subservice '{subservice}' for {self.service_type}")
        return self.perform_subservice(context, subservice, front_output)
    
    async def run_async(self, context: AgentContext, front_output: FrontAgentOutput) -> ServiceAgentResponse:
        subservice = self.classify_subservice(context, front_output)
        if subservice not in self.subservices:
            raise AgentError(f"Unsupported subservice '{subservice}' for {self.service_type}")
        return await self.perform_subservice_async(context, subservice, front_output)
