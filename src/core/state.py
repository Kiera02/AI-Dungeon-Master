from typing import Annotated, TypedDict, List, Dict
from langgraph.graph.message import add_messages

class GameState(TypedDict):
    """
    Represents the complete state of the Dungeon Master game at any given moment.
    This state is passed down to the LLM (Agent) and Tools during each iteration of the LangGraph.
    """
    # Add new messages from user or LLM to the messages list. The messages list is passed to the LLM (Agent) and Tools during each iteration of the LangGraph.
    messages: Annotated[list, add_messages]

    # The current location of the player in the game world.
    current_location: str

    # The list of locations that the player has visited in the game world.
    visited_locations: List[str]

    # The list of items that the player is carrying.
    inventory: List[str]

    # A key-value store for recording significant events, quest states, or NPC relationships.
    # Examples:
    # - "trusts_wizards": "False"
    # - "read_valen_letter": "True"
    # - "keeper_alert_level": "High"
    memory_flags: Dict[str, str]
