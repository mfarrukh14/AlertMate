"""Disaster management service agent implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

from app.agents.base import AgentContext, BaseServiceAgent
from app.models.dispatch import FrontAgentOutput, ServiceAgentResponse, ServiceType
from app.services import disaster
from app.services.enhanced_fire import enhanced_fire
from app.utils.llm_client import LLMError, llm_client

logger = logging.getLogger(__name__)


class DisasterServiceAgent(BaseServiceAgent):
    service_type = ServiceType.DISASTER

    def register_subservices(self) -> Mapping[str, Any]:
        return {
            "evacuation_guidance": disaster.evacuation_guidance,
            "resource_request": disaster.resource_request,
            "infrastructure_alert": lambda *args, **kwargs: {
                "status": "alert_forwarded",
                "department": "city_infrastructure",
            },
            "situation_monitor": lambda *args, **kwargs: {
                "questions": [
                    "Is water level rising?",
                    "Are there trapped individuals?",
                    "Any power outages?",
                ]
            },
            "mass_casualty_triage": lambda *args, **kwargs: {
                "guidance": "Prioritize airway, breathing, circulation; tag patients by severity.",
            },
        }

    def run(self, context: AgentContext, front_output: FrontAgentOutput) -> ServiceAgentResponse:
        if llm_client.is_configured:
            try:
                return self._run_with_llm(context, front_output)
            except LLMError as exc:
                logger.warning("Disaster agent LLM failed, using heuristics: %s", exc)
        return super().run(context, front_output)

    def _run_with_llm(
        self, context: AgentContext, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        payload = {
            "request": context.request.model_dump(),
            "front_agent": front_output.model_dump(),
            "allowed_subservices": list(self.subservices.keys()),
            "service": self.service_type.value,
        }
        system_prompt = (
            "You are the DISASTER response agent. Select the best subservice from the provided list"
            " based on the scenario and urgency."
            "\nIf immediate information is missing, set follow_up_required true with a focused question."
            "\nIf action can proceed, set follow_up_required false and describe the action in action_taken."
            "\nReturn strict JSON with keys: subservice, action_taken, follow_up_required, follow_up_question, metadata."
            "\nMetadata should include shelter info, resource tickets, or monitoring items as relevant."
            "\nOutput JSON only."
        )

        result = llm_client.structured_completion(
            system_prompt=system_prompt,
            payload=payload,
            temperature=0.2,
            max_tokens=500,
        )

        subservice = str(result.get("subservice", "")).strip()
        if subservice not in self.subservices:
            raise LLMError(f"Invalid subservice '{subservice}' returned by LLM")

        base_response = self.perform_subservice(context, subservice, front_output)

        metadata_update = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        updates = {
            "action_taken": result.get("action_taken", base_response.action_taken),
            "follow_up_required": bool(result.get("follow_up_required", base_response.follow_up_required)),
            "follow_up_question": result.get("follow_up_question", base_response.follow_up_question),
            "metadata": {**base_response.metadata, **metadata_update},
        }

        if not updates["follow_up_required"]:
            updates["follow_up_question"] = None

        return base_response.model_copy(update=updates)

    def classify_subservice(
        self, context: AgentContext, front_output: FrontAgentOutput
    ) -> str:
        query = context.request.user_query.lower()

        if any(term in query for term in ["evacuate", "shelter", "flood", "safe place"]):
            return "evacuation_guidance"
        if any(term in query for term in ["water", "food", "supplies", "aid"]):
            return "resource_request"
        if any(term in query for term in ["bridge", "road", "infrastructure", "damage"]):
            return "infrastructure_alert"
        if "casualty" in query or "injured" in query:
            return "mass_casualty_triage"
        return "situation_monitor"

    async def perform_subservice_async(
        self, context: AgentContext, subservice: str, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        handler = self.subservices[subservice]
        if subservice == "evacuation_guidance":
            # Enhanced evacuation with real-time coordination
            disaster_type = self._extract_disaster_type(context.request.user_query)
            metadata = await enhanced_fire.create_disaster_response(
                context.request.userid,
                disaster_type,
                context.request.user_location,
                front_output.urgency
            )
            follow_up_required = True
            follow_up_question = "How many people need evacuation assistance?"
            action = "evacuation_guidance_shared"
        elif subservice == "resource_request":
            metadata = handler("essential supplies")
            follow_up_required = True
            follow_up_question = "What specific resources and quantities are needed?"
            action = "resource_request_logged"
        elif subservice == "infrastructure_alert":
            metadata = handler()
            follow_up_required = False
            follow_up_question = None
            action = "infrastructure_team_alerted"
        elif subservice == "situation_monitor":
            metadata = handler()
            follow_up_required = True
            follow_up_question = "Provide status updates for each monitoring question."
            action = "situation_monitoring_engaged"
        elif subservice == "mass_casualty_triage":
            # Enhanced mass casualty response
            disaster_type = self._extract_disaster_type(context.request.user_query)
            metadata = await enhanced_fire.create_disaster_response(
                context.request.userid,
                disaster_type,
                context.request.user_location,
                1  # High severity for mass casualty
            )
            follow_up_required = True
            follow_up_question = "Number of injured individuals and their conditions?"
            action = "mass_casualty_guidance_provided"
        else:  # pragma: no cover
            metadata = {}
            follow_up_required = True
            follow_up_question = "Provide additional disaster details."
            action = None

        return ServiceAgentResponse(
            service=self.service_type,
            subservice=subservice,
            action_taken=action,
            follow_up_required=follow_up_required,
            follow_up_question=follow_up_question,
            metadata=metadata,
        )
    
    def _extract_disaster_type(self, user_query: str) -> str:
        """Extract disaster type from user query."""
        query_lower = user_query.lower()
        
        disaster_types = {
            "fire": ["fire", "burning", "flame", "smoke"],
            "earthquake": ["earthquake", "quake", "tremor", "shaking"],
            "flood": ["flood", "flooding", "water", "rain"],
            "storm": ["storm", "hurricane", "tornado", "wind"],
            "explosion": ["explosion", "explode", "blast", "bomb"],
            "gas_leak": ["gas", "leak", "smell"],
            "building_collapse": ["collapse", "building", "structure"],
            "chemical_spill": ["chemical", "spill", "toxic"],
            "power_outage": ["power", "electricity", "outage", "blackout"]
        }
        
        for disaster_type, keywords in disaster_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return disaster_type
        
        return "general_disaster"
