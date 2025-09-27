"""Police service agent implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

from app.agents.base import AgentContext, BaseServiceAgent
from app.models.dispatch import FrontAgentOutput, ServiceAgentResponse, ServiceType
from app.services import police
from app.services.enhanced_police import enhanced_police
from app.utils.llm_client import LLMError, llm_client

logger = logging.getLogger(__name__)


class PoliceServiceAgent(BaseServiceAgent):
    service_type = ServiceType.POLICE

    def register_subservices(self) -> Mapping[str, Any]:
        return {
            "emergency_response": police.dispatch_unit,
            "report_incident": police.create_incident_report,
            "suspect_tracking": lambda *args, **kwargs: {
                "status": "suspect_description_requested"
            },
            "evidence_advice": lambda *args, **kwargs: {
                "guidance": "Preserve CCTV footage and avoid touching the scene."
            },
            "non_emergency_guidance": lambda *args, **kwargs: {
                "steps": [
                    "File an online complaint",
                    "Visit the nearest police station with ID",
                ]
            },
        }

    def run(self, context: AgentContext, front_output: FrontAgentOutput) -> ServiceAgentResponse:
        if llm_client.is_configured:
            try:
                return self._run_with_llm(context, front_output)
            except LLMError as exc:
                logger.warning("Police agent LLM failed, using heuristics: %s", exc)
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
            "You are the POLICE agent. Choose one subservice from the provided list based on"
            " the user's situation and urgency."
            "\nSet follow_up_required true only if more information is essential, and craft a concise question."
            "\nIf action can proceed, set follow_up_required false and describe the action_taken briefly."
            "\nReturn strict JSON with keys: subservice, action_taken, follow_up_required, follow_up_question, metadata."
            "\nMetadata should include reference numbers, dispatch details, or key guidance."
            "\nRespond with JSON only."
        )

        result = llm_client.structured_completion(
            system_prompt=system_prompt,
            payload=payload,
            temperature=0.2,
            max_tokens=450,
        )

        subservice = str(result.get("subservice", "")).strip()
        if subservice not in self.subservices:
            raise LLMError(f"Invalid subservice '{subservice}' returned by LLM")

        base_response = self.perform_subservice(context, subservice, front_output)

        metadata_update = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        updates: Dict[str, Any] = {
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

        if front_output.urgency == 1 or any(term in query for term in ["immediate", "now", "armed", "attack"]):
            return "emergency_response"
        if any(term in query for term in ["report", "stole", "robbery", "theft"]):
            return "report_incident"
        if "suspect" in query or "description" in query:
            return "suspect_tracking"
        if "evidence" in query or "camera" in query:
            return "evidence_advice"
        return "non_emergency_guidance"

    async def perform_subservice_async(
        self, context: AgentContext, subservice: str, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        handler = self.subservices[subservice]
        if subservice == "emergency_response":
            # Use enhanced police service with real-time data
            metadata = await enhanced_police.dispatch_unit(
                context.request.userid, 
                context.request.user_location,
                context.request.lat,
                context.request.lon
            )
            follow_up_required = True
            follow_up_question = "Are you currently safe and sheltered?"
            action = "emergency_units_dispatched"
        elif subservice == "report_incident":
            # Use enhanced police service for incident reporting
            metadata = await enhanced_police.create_incident_report(
                context.request.userid, 
                context.request.user_query,
                context.request.user_location
            )
            follow_up_required = True
            follow_up_question = "Provide suspect description or distinguishing features."
            action = "incident_report_created"
        elif subservice == "suspect_tracking":
            metadata = handler()
            follow_up_required = True
            follow_up_question = "Describe the suspect's appearance and direction of travel."
            action = "suspect_information_requested"
        elif subservice == "evidence_advice":
            metadata = handler()
            follow_up_required = False
            follow_up_question = None
            action = "evidence_preservation_guidance_shared"
        elif subservice == "non_emergency_guidance":
            metadata = handler()
            follow_up_required = False
            follow_up_question = None
            action = "non_emergency_guidance_sent"
        else:  # pragma: no cover
            metadata = {}
            follow_up_required = True
            follow_up_question = "Provide additional details for police assistance."
            action = None

        return ServiceAgentResponse(
            service=self.service_type,
            subservice=subservice,
            action_taken=action,
            follow_up_required=follow_up_required,
            follow_up_question=follow_up_question,
            metadata=metadata,
        )
