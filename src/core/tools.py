from langchain_core.tools import tool

@tool
def update_inventory(item: str, action: str) -> str:
    """
    Call this tool ONLY when the player explicitly picks up or drops an item.
    - item: The name of the item (e.g., 'rusty key', 'sealed letter').
    - action: MUST be strictly 'add' or 'remove'.
    """
    if action == "add":
        return f"System: Successfully added '{item}' to inventory."
    return f"System: Successfully removed '{item}' from inventory."

@tool
def change_location(new_location: str) -> str:
    """
    Call this tool when the player moves to a completely new area or room.
    - new_location: The name of the destination (e.g., 'Upstairs', 'Lighthouse Top').
    """
    return f"System: Player is now located at '{new_location}'."

@tool
def update_memory_flag(event_key: str, event_value: str) -> str:
    """
    Call this tool to remember significant events, choices, quests, or NPC attitudes.
    - event_key: A short snake_case key (e.g., 'keeper_alert_level', 'trusted_by_wizard').
    - event_value: The state of the event (e.g., 'high', 'True', 'read_the_letter').
    """
    return f"System: Memory updated. [{event_key}] is now recorded as '{event_value}'."

game_tools = [update_inventory, change_location, update_memory_flag]