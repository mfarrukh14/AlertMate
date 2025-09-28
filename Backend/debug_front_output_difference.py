#!/usr/bin/env python3
"""Debug difference in front output between individual test and full pipeline."""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.agents.router import DispatchRouter
from app.agents.disaster_agent import DisasterServiceAgent
from app.agents.base import AgentContext
from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceType

def debug_front_output_difference():
    """Debug difference in front output."""
    print("🔍 Debugging front output difference...")
    
    router = DispatchRouter()
    disaster_agent = DisasterServiceAgent()
    
    # Test the follow-up response "66"
    request = DispatchRequest(
        userid="test_chat_user_1",
        user_query="66",
        user_location="Soan River",
        lat=33.550274,
        lon=73.094238,
        lang="en",
        network_quality="fast",
        connection_type="4g"
    )
    
    print("1️⃣ Testing with router (full pipeline)...")
    try:
        front_output_router, service_response_router = router.process(request, "test-trace-router")
        print(f"  Router Front service: {front_output_router.selected_service.value}")
        print(f"  Router Front urgency: {front_output_router.urgency}")
        print(f"  Router Front keywords: {front_output_router.keywords}")
        print(f"  Router Front explain: {front_output_router.explain}")
        print(f"  Router Service subservice: {service_response_router.subservice}")
        print(f"  Router Service follow-up: {service_response_router.follow_up_required}")
    except Exception as e:
        print(f"  ❌ Router error: {e}")
        return
    
    print(f"\n2️⃣ Testing disaster agent with router's front output...")
    context = AgentContext(request=request, trace_id="test-trace-agent")
    
    try:
        disaster_result = disaster_agent.run(context, front_output_router)
        print(f"  Disaster Subservice: {disaster_result.subservice}")
        print(f"  Disaster Follow-up required: {disaster_result.follow_up_required}")
        print(f"  Disaster Follow-up question: {disaster_result.follow_up_question}")
        
        # Compare with what we expect
        if disaster_result.subservice == "evacuation_guidance" and not disaster_result.follow_up_required:
            print(f"  ✅ Disaster agent working correctly with router's front output")
        else:
            print(f"  ❌ Disaster agent not working correctly with router's front output")
            
    except Exception as e:
        print(f"  ❌ Disaster agent error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_front_output_difference()
