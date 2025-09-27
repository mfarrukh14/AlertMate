"""Medical service agent implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

from app.agents.base import AgentContext, BaseServiceAgent
from app.models.dispatch import FrontAgentOutput, ServiceAgentResponse, ServiceType
from app.services import medical
from app.services.enhanced_medical import enhanced_medical
from app.utils.llm_client import LLMError, llm_client

logger = logging.getLogger(__name__)


class MedicalServiceAgent(BaseServiceAgent):
    service_type = ServiceType.MEDICAL

    def register_subservices(self) -> Mapping[str, Any]:
        return {
            "ambulance_dispatch": "ambulance_dispatch",
            "nearest_hospital_lookup": "nearest_hospital_lookup",
            "appointment_booking": lambda *args, **kwargs: {
                "status": "appointment_requested",
                "department": "orthopedics",
            },
            "triage_advice": lambda *args, **kwargs: {
                "questions": [
                    "Is the patient conscious?",
                    "Is the patient breathing normally?",
                    "Is there severe bleeding?",
                ]
            },
            "prescription_refill": lambda *args, **kwargs: {
                "status": "refill_initiated",
                "eta_hours": 6,
            },
        }

    def run(self, context: AgentContext, front_output: FrontAgentOutput) -> ServiceAgentResponse:
        if llm_client.is_configured:
            try:
                return self._run_with_llm(context, front_output)
            except LLMError as exc:
                logger.warning("Medical agent LLM failed, using heuristics: %s", exc)
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
            "You are the MEDICAL agent. Choose exactly one subservice from the provided list"
            " based on the user's request and front agent analysis."
            "\nIf more information is required, set follow_up_required true and provide a concise question."
            "\nIf you can act, set follow_up_required false and describe the action_taken succinctly."
            "\nReturn strict JSON with keys: subservice (string), action_taken (string or null),"
            " follow_up_required (bool), follow_up_question (string or null), metadata (object)."
            "\nMetadata should include any additional context such as hospitals, eta, or instruction summaries."
            "\nOnly return JSON, no additional prose."
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
        keywords = set(front_output.keywords)

        if any(term in query for term in ["ambulance", "broke", "unconscious", "heavy bleeding"]):
            return "ambulance_dispatch"
        if "hospital" in query or "nearest" in query:
            return "nearest_hospital_lookup"
        if "appointment" in query or "schedule" in query:
            return "appointment_booking"
        if "prescription" in query or "refill" in query:
            return "prescription_refill"
        if "triage" in query or front_output.urgency == 1:
            return "triage_advice"
        if "ambulance" in keywords:
            return "ambulance_dispatch"
        return "triage_advice"

    async def perform_subservice_async(
        self, context: AgentContext, subservice: str, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        handler = self.subservices[subservice]
        if subservice == "ambulance_dispatch":
            # Use enhanced medical service with real-time data
            metadata = await enhanced_medical.ambulance_dispatch_packet(
                context.request.userid,
                context.request.lat,
                context.request.lon,
            )
            follow_up_required = True
            follow_up_question = "Is the patient conscious and breathing? Any heavy bleeding?"
            action = "dispatched_request_to_ambulance_provider"
        elif subservice == "nearest_hospital_lookup":
            # Use enhanced medical service for hospital lookup
            metadata = {
                "hospitals": await enhanced_medical.nearest_hospitals(
                    context.request.lat,
                    context.request.lon,
                )
            }
            follow_up_required = False
            follow_up_question = None
            action = "returned_nearest_hospitals"
        elif subservice == "appointment_booking":
            metadata = handler()
            follow_up_required = True
            follow_up_question = "Preferred date and specialist?"
            action = "appointment_request_created"
        elif subservice == "triage_advice":
            metadata = handler()
            follow_up_required = True
            follow_up_question = "Please answer the triage questions to proceed."
            action = "triage_questions_sent"
        elif subservice == "prescription_refill":
            metadata = handler()
            follow_up_required = True
            follow_up_question = "What medication needs a refill and dosage?"
            action = "prescription_refill_initiated"
        else:  # pragma: no cover - safeguard
            metadata = {}
            follow_up_required = True
            follow_up_question = "Provide additional medical details."
            action = None

        return ServiceAgentResponse(
            service=self.service_type,
            subservice=subservice,
            action_taken=action,
            follow_up_required=follow_up_required,
            follow_up_question=follow_up_question,
            metadata=metadata,
        )
