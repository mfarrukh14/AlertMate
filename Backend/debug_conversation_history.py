#!/usr/bin/env python3
"""Debug conversation history being passed to front agent."""

import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.db import session_scope
from app.services.memory import get_recent_messages

def debug_conversation_history():
    """Debug conversation history."""
    print("🔍 Debugging conversation history...")
    
    with session_scope() as session:
        # Get conversation history for the test user
        history = get_recent_messages(session, "test_chat_user_1", limit=12)
        
        print(f"📋 Conversation history for test_chat_user_1:")
        print(f"  Total messages: {len(history)}")
        
        for i, msg in enumerate(history):
            print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
            print(f"      Created: {msg['created_at']}")
        
        if len(history) < 2:
            print(f"\n❌ Not enough conversation history to provide context")
            print(f"   This explains why the front agent doesn't understand it's a follow-up")
        else:
            print(f"\n✅ Sufficient conversation history available")

if __name__ == "__main__":
    debug_conversation_history()
