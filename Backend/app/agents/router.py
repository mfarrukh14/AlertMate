"""LangGraph-powered coordinator between the front and service agents."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.base import AgentContext, AgentError, BaseServiceAgent
from app.agents.disaster_agent import DisasterServiceAgent
from app.agents.front_agent import FrontDispatcherAgent
from app.agents.medical_agent import MedicalServiceAgent
from app.agents.police_agent import PoliceServiceAgent
from app.db import session_scope
from app.db.models import ConversationRole
from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceAgentResponse, ServiceType
from app.services.memory import ensure_user, get_recent_messages, record_message
from app.services.queue_service import enqueue_task
from app.services.dispatch_events import record_dispatch_event
from app.models.dispatch_events import DispatchEventCreate

logger = logging.getLogger(__name__)


class DispatchState(TypedDict, total=False):
    request: DispatchRequest
    trace_id: str
    history: List[dict]
    front_output: FrontAgentOutput
    service_response: ServiceAgentResponse


class DispatchRouter:
    """High-level orchestrator implemented as a LangGraph workflow."""

    def __init__(self) -> None:
        self.front_agent = FrontDispatcherAgent()
        self.service_agents: Dict[ServiceType, BaseServiceAgent] = {
            ServiceType.MEDICAL: MedicalServiceAgent(),
            ServiceType.POLICE: PoliceServiceAgent(),
            ServiceType.DISASTER: DisasterServiceAgent(),
        }
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(DispatchState)

        def run_front(state: DispatchState) -> Dict[str, Any]:
            request = state["request"]
            trace_id = state["trace_id"]
            history = state.get("history") or []
            logger.info(
                "Front agent dispatch",
                extra={"trace_id": trace_id, "userid": request.userid},
            )
            front_output = self.front_agent.run(request, history)
            logger.info(
                "Front agent output",
                extra={
                    "trace_id": trace_id,
                    "selected_service": front_output.selected_service.value,
                    "urgency": front_output.urgency,
                },
            )
            front_summary = self._format_front_message(front_output)
            updated_history = list(history)
            if front_summary:
                updated_history.append(
                    {
                        "role": ConversationRole.AGENT.value,
                        "content": front_summary,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            return {"front_output": front_output, "history": updated_history}

        def route_service(state: DispatchState) -> str:
            service = state.get("front_output")
            if not service:
                raise AgentError("Front agent did not produce an output")
            if service.selected_service == ServiceType.GENERAL:
                return ServiceType.GENERAL.value
            if service.selected_service not in self.service_agents:
                raise AgentError(f"Unsupported service: {service.selected_service}")
            return service.selected_service.value

        def make_service_node(service_type: ServiceType):
            def _run_service(state: DispatchState) -> Dict[str, Any]:
                front_output = state.get("front_output")
                if not front_output:
                    raise AgentError("Missing front agent output before service routing")
                agent = self.service_agents.get(service_type)
                if not agent:
                    raise AgentError(f"Unsupported service: {service_type}")

                context = AgentContext(
                    request=state["request"],
                    trace_id=state["trace_id"],
                    front_output=front_output,
                    history=state.get("history"),
                )
                # Use async run if available, otherwise fallback to sync
                if hasattr(agent, 'run_async'):
                    import asyncio
                    service_response = asyncio.run(agent.run_async(context, front_output))
                else:
                    service_response = agent.run(context, front_output)
                logger.info(
                    "Service agent response",
                    extra={
                        "trace_id": state["trace_id"],
                        "service": service_response.service.value,
                        "subservice": service_response.subservice,
                    },
                )
                return {"service_response": service_response}

            return _run_service

        workflow.add_node("front_agent", run_front)
        for service_type in (ServiceType.MEDICAL, ServiceType.POLICE, ServiceType.DISASTER):
            workflow.add_node(f"{service_type.value}_agent", make_service_node(service_type))
            workflow.add_edge(f"{service_type.value}_agent", END)

        def handle_general(state: DispatchState) -> Dict[str, Any]:
            front_output = state.get("front_output")
            if not front_output:
                raise AgentError("General handler missing front agent output")

            follow_up = front_output.follow_up_reason or "Could you describe the emergency or assistance you need?"
            service_response = ServiceAgentResponse(
                service=ServiceType.GENERAL,
                subservice="awaiting_details",
                action_taken=None,
                follow_up_required=True,
                follow_up_question=follow_up,
                metadata={
                    "note": "Front agent awaiting additional context",
                },
            )
            return {"service_response": service_response}

        workflow.add_node("general_handler", handle_general)
        workflow.add_edge("general_handler", END)

        workflow.set_entry_point("front_agent")
        workflow.add_conditional_edges(
            "front_agent",
            route_service,
            {
                ServiceType.MEDICAL.value: "medical_agent",
                ServiceType.POLICE.value: "police_agent",
                ServiceType.DISASTER.value: "disaster_agent",
                ServiceType.GENERAL.value: "general_handler",
            },
        )

        return workflow.compile()

    def process(self, request: DispatchRequest, trace_id: str) -> tuple[FrontAgentOutput, ServiceAgentResponse]:
        logger.info("Processing dispatch request", extra={"trace_id": trace_id, "userid": request.userid})
        with session_scope() as session:
            try:
                ensure_user(session, request.userid)
            except ValueError as exc:
                raise AgentError(str(exc)) from exc
            history = get_recent_messages(session, request.userid, limit=12)
            result_state = self._graph.invoke({
                "request": request,
                "trace_id": trace_id,
                "history": history,
            })

            front_output = result_state.get("front_output")
            service_response = result_state.get("service_response")
            if not front_output or not service_response:
                raise AgentError("Dispatch graph did not produce required outputs")

            user_text = (request.user_query or "").strip()
            if user_text:
                record_message(session, request.userid, ConversationRole.USER, user_text)

            front_message = self._format_front_message(front_output)
            if front_message:
                record_message(session, request.userid, ConversationRole.AGENT, front_message)

            service_message = self._format_service_message(service_response)
            if service_message:
                record_message(session, request.userid, ConversationRole.AGENT, service_message)

            recent_history = get_recent_messages(session, request.userid, limit=12)
            task_payload = {
                "user_id": request.userid,
                "user_location": request.user_location,
                "history": recent_history,
                "front_agent": front_output.model_dump(mode="json"),
                "service_response": service_response.model_dump(mode="json"),
            }
            task = enqueue_task(
                session,
                trace_id=trace_id,
                service=service_response.service,
                priority=front_output.urgency,
                payload=task_payload,
            )
            
            # Record dispatch event for tracking and analytics
            if service_response.service != ServiceType.GENERAL:
                dispatch_event = DispatchEventCreate(
                    user_id=request.userid,
                    trace_id=trace_id,
                    service=service_response.service,
                    subservice=service_response.subservice,
                    action_taken=service_response.action_taken,
                    priority=front_output.urgency,
                    user_location=request.user_location,
                    user_lat=request.lat,
                    user_lon=request.lon,
                    status="dispatched",
                    event_metadata=service_response.metadata
                )
                record_dispatch_event(session, dispatch_event)
            
            logger.info(
                "Queued service task",
                extra={
                    "trace_id": trace_id,
                    "task_id": task.id,
                    "service": service_response.service.value,
                    "priority": task.priority,
                },
            )

            return front_output, service_response

    @staticmethod
    def _format_front_message(front_output: FrontAgentOutput) -> str:
        parts: List[str] = []
        
        # Remove technical explanations and make it conversational
        if front_output.explain:
            explain = front_output.explain.lower()
            if "urgency" in explain and "selected" in explain:
                # Convert technical format to conversational
                if "immediate life-threatening" in explain or "life safety" in explain:
                    parts.append("🚨 I understand this is a life-threatening emergency. Let me get you help immediately.")
                elif "serious" in explain or "urgent" in explain:
                    parts.append("⚠️ I can see this is a serious situation. I'm connecting you with the right service.")
                elif "informational" in explain or "general" in explain:
                    parts.append("ℹ️ I've noted your request and I'm here to help.")
                else:
                    parts.append("I understand your situation and I'm here to help.")
            elif "theft" in explain or "chori" in explain:
                parts.append("I understand a theft has occurred. Let me connect you with the police.")
            elif "broken" in explain or "toot" in explain:
                parts.append("I understand there's been an injury. Let me get you medical help.")
            elif "flood" in explain:
                parts.append("I understand there's a flood situation. Let me connect you with disaster services.")
            else:
                # Only show non-technical explanations
                if not any(tech_word in explain for tech_word in ["urgency", "selected", "based on", "keywords"]):
                    parts.append(front_output.explain)
        
        if front_output.follow_up_required and front_output.follow_up_reason:
            parts.append(f"Quick question: {front_output.follow_up_reason}")
        
        return "\n".join(part for part in parts if part).strip()

    @staticmethod
    def _format_service_message(service_response: ServiceAgentResponse) -> str:
        def convert_for_json(obj):
            """Deep-convert arbitrary objects into JSON-serializable structures.

            Handles:
              - set/tuple -> list
              - Enum -> value
              - datetime -> ISO string
              - pydantic models (model_dump)
              - objects with __dict__ (shallow) as last resort
              - Any remaining unsupported object -> str(obj)
            """
            from enum import Enum
            from datetime import datetime as _dt

            # Fast path for primitives
            if obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, (set, tuple)):
                return [convert_for_json(o) for o in obj]
            if isinstance(obj, list):
                return [convert_for_json(o) for o in obj]
            if isinstance(obj, dict):
                return {convert_for_json(k): convert_for_json(v) for k, v in obj.items()}
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, _dt):
                return obj.isoformat()
            # Pydantic v2 models
            if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
                try:
                    return convert_for_json(obj.model_dump())
                except Exception:  # pragma: no cover - defensive
                    return str(obj)
            # Generic dataclass-like / object with __dict__
            if hasattr(obj, "__dict__"):
                try:
                    return {k: convert_for_json(v) for k, v in vars(obj).items() if not k.startswith("_")}
                except Exception:  # pragma: no cover
                    return str(obj)
            # Fallback string representation
            return str(obj)
        
        parts: List[str] = []
        
        # Make service selection more conversational
        service_emojis = {
            "medical": "🏥",
            "police": "🚔", 
            "disaster": "🌪️",
            "general": "📞"
        }
        emoji = service_emojis.get(service_response.service.value, "📞")
        parts.append(f"{emoji} I've connected you with {service_response.service.value.upper()} services.")
        
        # Make action taken more conversational
        if service_response.action_taken:
            action = service_response.action_taken.lower()
            if "incident_report_created" in action:
                parts.append("✅ I've created an incident report for you.")
            elif "dispatch" in action:
                parts.append("✅ Emergency units have been dispatched to your location.")
            elif "alert" in action:
                parts.append("✅ I've sent out emergency alerts.")
            elif "non_emergency_guidance" in action:
                parts.append("✅ I've provided guidance for your situation.")
            elif "triage_questions" in action:
                parts.append("✅ I've sent you some important questions to assess the situation.")
            elif "evacuation_guidance" in action:
                parts.append("✅ I've shared evacuation guidance with you.")
            elif "guidance_shared" in action:
                parts.append("✅ I've shared important information with you.")
            else:
                # Convert technical action to user-friendly message
                friendly_action = action.replace("_", " ").title()
                parts.append(f"✅ {friendly_action}")
        
        # Make follow-up questions more conversational
        if service_response.follow_up_required and service_response.follow_up_question:
            parts.append(f"❓ {service_response.follow_up_question}")
        
        # Make metadata more conversational
        if service_response.metadata:
            try:
                serializable_metadata = convert_for_json(service_response.metadata)
                metadata_parts = []
                
                # Extract key information and present it conversationally
                if "report_number" in serializable_metadata:
                    metadata_parts.append(f"📋 Report #: {serializable_metadata['report_number']}")
                if "assigned_station" in serializable_metadata and isinstance(serializable_metadata["assigned_station"], dict):
                    station = serializable_metadata["assigned_station"]
                    if "name" in station and "phone" in station:
                        metadata_parts.append(f"🏢 Station: {station['name']} ({station['phone']})")
                if "eta" in serializable_metadata:
                    metadata_parts.append(f"⏱️ ETA: {serializable_metadata['eta']}")
                if "distance_km" in serializable_metadata:
                    metadata_parts.append(f"📍 Distance: {serializable_metadata['distance_km']} km")
                
                if metadata_parts:
                    parts.append("\n".join(metadata_parts))
                else:
                    # Fallback to basic metadata display
                    parts.append(f"📊 Details: {json.dumps(serializable_metadata, ensure_ascii=False)}")
            except Exception as exc:  # pragma: no cover - resilience
                logger.warning(
                    "Failed to serialize service metadata; sending fallback string",
                    extra={
                        "error": str(exc),
                        "service": service_response.service.value,
                        "subservice": service_response.subservice,
                    },
                )
                parts.append(f"📊 Additional details: {str(service_response.metadata)}")
        
        return "\n\n".join(part for part in parts if part).strip()
