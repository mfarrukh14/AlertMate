#!/usr/bin/env python3
"""Debug disaster agent LLM error."""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.agents.disaster_agent import DisasterServiceAgent
from app.agents.base import AgentContext
from app.models.dispatch import DispatchRequest, FrontAgentOutput, ServiceType
from app.utils.llm_client import LLMError

def debug_disaster_llm_error():
    """Debug disaster agent LLM error."""
    print("🔍 Debugging disaster agent LLM error...")
    
    agent = DisasterServiceAgent()
    
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
    
    context = AgentContext(request=request, trace_id="test-trace-id")
    
    front_output = FrontAgentOutput(
        keywords=["66 people", "evacuation", "flood"],
        urgency=1,
        selected_service=ServiceType.DISASTER,
        explain="User providing number of people for evacuation assistance",
        follow_up_required=False,
        follow_up_reason=None
    )
    
    print(f"Input: '{request.user_query}'")
    print(f"Keywords: {front_output.keywords}")
    print(f"Urgency: {front_output.urgency}")
    
    try:
        # Test the LLM part directly
        print(f"\n🤖 Testing LLM directly...")
        result = agent._run_with_llm(context, front_output)
        print(f"  LLM Subservice: {result.subservice}")
        print(f"  LLM Follow-up required: {result.follow_up_required}")
        print(f"  LLM Follow-up question: {result.follow_up_question}")
        print(f"  ✅ LLM working correctly!")
        
    except LLMError as e:
        print(f"  ❌ LLM Error: {e}")
        print(f"  This explains why it falls back to heuristics")
    except Exception as e:
        print(f"  ❌ Other Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the full run method
    print(f"\n🔄 Testing full run method...")
    try:
        result = agent.run(context, front_output)
        print(f"  Final Subservice: {result.subservice}")
        print(f"  Final Follow-up required: {result.follow_up_required}")
        print(f"  Final Follow-up question: {result.follow_up_question}")
        
        if result.subservice == "situation_monitor":
            print(f"  ❌ Using heuristics (wrong subservice)")
        else:
            print(f"  ✅ Using LLM (correct subservice)")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    debug_disaster_llm_error()
