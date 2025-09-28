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
            "\nAVAILABLE SUBSERVICES: ambulance_dispatch, nearest_hospital_lookup, appointment_booking, triage_advice, prescription_refill"
            "\nSELECTION RULES:"
            "\n- ambulance_dispatch: For emergencies requiring immediate medical transport (accidents, severe bleeding, unconscious, choking, seizures, heart attack, stroke, severe injuries, life-threatening conditions)"
            "\n- triage_advice: For medical questions, assessment, or when you need to gather more information about symptoms"
            "\n- nearest_hospital_lookup: When user asks for hospital locations or directions"
            "\n- appointment_booking: For scheduling non-emergency medical appointments"
            "\n- prescription_refill: For medication refill requests"
            "\nIMPORTANT: If the user_query is a short response (like a number, yes/no, brief answer, age, count, or brief description) and this appears to be a follow-up to a previous question, DO NOT ask for more information. Process the response and set follow_up_required false."
            "\nDO NOT ask for location - the system already has the user's location from user_location, lat, and lon fields."
            "\nDO NOT ask for basic emergency details that are already clear from the request."
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
            max_tokens=800,
            user_id=context.request.userid,
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

        # Check if this is a follow-up response (short query with numbers)
        is_followup = len(query.strip()) <= 10 and any(char.isdigit() for char in query)
        if is_followup:
            return "ambulance_dispatch"

        if any(term in query for term in ["ambulance", "broke", "unconscious", "heavy bleeding", "alot of bleeding", "lots of bleeding", "much bleeding", "severe bleeding", "excessive bleeding", "profuse bleeding", "choking", "choke", "emergency", "urgent", "critical", "fits", "seizure", "seizures", "convulsions", "accident", "crash", "collision"]):
            return "ambulance_dispatch"
        if "hospital" in query or "nearest" in query:
            return "nearest_hospital_lookup"
        if "appointment" in query or "schedule" in query:
            return "appointment_booking"
        if "prescription" in query or "refill" in query:
            return "prescription_refill"
        if "triage" in query or front_output.urgency == 1:
            return "triage_advice"
        if any(keyword in keywords for keyword in ["ambulance", "choking", "emergency", "fits", "seizure", "convulsions"]):
            return "ambulance_dispatch"
        return "triage_advice"

    def perform_subservice(
        self, context: AgentContext, subservice: str, front_output: FrontAgentOutput
    ) -> ServiceAgentResponse:
        """Synchronous version of perform_subservice."""
        handler = self.subservices[subservice]
        if subservice == "ambulance_dispatch":
            # For sync version, use basic ambulance dispatch without async calls
            metadata = handler() if callable(handler) else {}
            follow_up_required = True
            follow_up_question = "Is the patient conscious and breathing? Any heavy bleeding?"
            action = "dispatched_request_to_ambulance_provider"
        elif subservice == "nearest_hospital_lookup":
            metadata = handler() if callable(handler) else {}
            follow_up_required = False
            follow_up_question = None
            action = "returned_nearest_hospitals"
        elif subservice == "appointment_booking":
            metadata = handler() if callable(handler) else {}
            follow_up_required = True
            follow_up_question = "Preferred date and specialist?"
            action = "appointment_booking_guidance_shared"
        elif subservice == "prescription_refill":
            metadata = handler() if callable(handler) else {}
            follow_up_required = True
            follow_up_question = "Which medications need refilling?"
            action = "prescription_refill_guidance_provided"
        elif subservice == "triage_advice":
            metadata = handler() if callable(handler) else {}
            follow_up_required = True
            follow_up_question = "Describe the symptoms in detail."
            action = "triage_advice_provided"
        else:  # pragma: no cover
            metadata = {}
            follow_up_required = True
            follow_up_question = "Please provide more medical details."
            action = "medical_assessment_requested"

        return ServiceAgentResponse(
            service=self.service_type,
            subservice=subservice,
            action_taken=action,
            follow_up_required=follow_up_required,
            follow_up_question=follow_up_question,
            metadata=metadata,
        )

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
