from typing import Literal
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from src.core.state import GameState
from src.core.tools import game_tools
from src.world_data.prompt import dungeon_master_prompt

# llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.7)
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)
llm_with_tools = llm.bind_tools(game_tools)

def call_model_node(state: GameState):
    """
    This node is responsible for loading the current state into the prompt and calling the LLM.
    """
    # Attach the current state to the Prompt Template
    prompt = dungeon_master_prompt.invoke({
        "messages": state["messages"],
        "current_location": state.get("current_location", "Ground Floor"),
        "inventory": state.get("inventory", []),
        "memory_flags": state.get("memory_flags", {})
    })

    response = llm_with_tools.invoke(prompt)
    return {"messages": [response]}

def process_tools_node(state: GameState):
    """
    This node scans for Tool Calls from the LLM, executes the logic to change the State,
    and returns the result (ToolMessage) to the system.
    """
    messages = state.get("messages", [])
    last_message = messages[-1]

    # Copy current states for safe modification
    inventory = list(state.get("inventory", []))
    current_location = state.get("current_location", "Unknown")
    memory_flags = dict(state.get("memory_flags", {}))
    
    tool_messages = []

    # Loop through the tools that the LLM requested to call
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        tool_id = tool_call["id"]
        
        # 1. Inventory update logic
        if tool_name == "update_inventory":
            item = args.get("item")
            action = args.get("action")
            if action == "add" and item not in inventory:
                inventory.append(item)
                msg = f"System: Successfully added '{item}' to inventory."
            elif action == "remove" and item in inventory:
                inventory.remove(item)
                msg = f"System: Successfully removed '{item}' from inventory."
            else:
                msg = "System: Action failed or item already in the requested state."
            
            tool_messages.append(ToolMessage(content=msg, tool_call_id=tool_id))

        # 2. Location change logic
        elif tool_name == "change_location":
            new_location = args.get("new_location")
            current_location = new_location
            msg = f"System: Player is now located at '{new_location}'."
            tool_messages.append(ToolMessage(content=msg, tool_call_id=tool_id))

        # 3. Memory update logic
        elif tool_name == "update_memory_flag":
            key = args.get("event_key")
            value = args.get("event_value")
            memory_flags[key] = value
            msg = f"System: Memory updated. [{key}] = '{value}'."
            tool_messages.append(ToolMessage(content=msg, tool_call_id=tool_id))
            
    # LangGraph will automatically update the State based on the Dictionary returned.
    return {
        "messages": tool_messages,
        "inventory": inventory,
        "current_location": current_location,
        "memory_flags": memory_flags
    }

def route_after_model(state: GameState) -> Literal["process_tools", "__end__"]:
    """
    This function routes the flow: Check if the LLM wants to call a Tool.
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "process_tools"
    return "__end__"

# Build the State Graph
workflow = StateGraph(GameState)

# Add Nodes
workflow.add_node("agent", call_model_node)
workflow.add_node("process_tools", process_tools_node)

# Define Edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route_after_model)
workflow.add_edge("process_tools", "agent") # Return to agent after state update

# Initialize memory (Checkpointer)
memory = MemorySaver()

# Compile the application
app = workflow.compile(checkpointer=memory)