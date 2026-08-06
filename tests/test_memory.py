import pytest
import time
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler

# Import your compiled LangGraph app
from src.core.graph import app

def test_needle_in_haystack():
    """
    Test the Agent's long-term memory capabilities (Both State and LLM Context).
    """
    langfuse_handler = CallbackHandler()

    # Initialize a brand new session for this specific test
    config = {"configurable": {"thread_id": "test_player_999"}, "callbacks": [langfuse_handler]}
    
    # Reset the initial State (ensure inventory is empty)
    initial_state = {
        "current_location": "Test Room",
        "inventory": [],
        "memory_flags": {}
    }
    app.update_state(
        config, 
        {"messages": [{"role": "assistant", "content": "Welcome to the test room."}], **initial_state}
    )

    print("\n[1] PLANTING THE NEEDLE...")
    needle_action = "I pick up the rusty key and put it in my bag. Also, remember that my character is terrified of spiders."
    app.invoke({"messages": [HumanMessage(content=needle_action)]}, config)

    print("[2] BUILDING THE HAYSTACK (Distractions)...")
    # Loop through 5 trivial actions to push important info further back in the context window
    haystack_actions = [
        "I look at the ceiling to see if it's raining.",
        "I walk in circles humming a tavern song.",
        "I stretch my arms and yawn loudly.",
        "I check my boots for mud.",
        "I sit on the floor and count to ten."
    ]
    
    for action in haystack_actions:
        app.invoke({"messages": [HumanMessage(content=action)]}, config)
        print("Waiting 15 seconds to respect Groq's rate limits...")
        time.sleep(15)

    print("[3] HARVESTING AND TESTING...")
    
    # --- TEST 1: CHECK STATE VARIABLES ---
    # Retrieve current state to check if the Tool successfully updated the inventory and memory
    current_state = app.get_state(config).values
    inventory = current_state.get("inventory", [])
    memory_flags = current_state.get("memory_flags", {})
    
    # Assert system behavior, if false the test will Fail (Red)
    assert any("key" in item.lower() for item in inventory), "STATE ERROR: The inventory lost the key!"

    # --- TEST 2: CHECK LLM MEMORY ---
    # Ask a decisive question to see if the LLM retrieves the correct info
    query_action = "Quickly, what did I put in my bag earlier? And what creature am I afraid of?"
    response = app.invoke({"messages": [HumanMessage(content=query_action)]}, config)
    
    final_ai_message = response["messages"][-1].content.lower()

    assert "key" in final_ai_message, "LLM ERROR: The AI forgot about the key!"
    assert "spider" in final_ai_message, "LLM ERROR: The AI forgot about the fear of spiders!"

    print("[4] TEST COMPLETE: Memory system is working perfectly!")

    langfuse_handler._langfuse_client.flush()  # Ensure all logs are sent to Langfuse