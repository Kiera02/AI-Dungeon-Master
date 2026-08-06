import os
import logging
import warnings
from rich.console import Console
from rich.panel import Panel
from langchain_core.messages import HumanMessage
from langfuse.langchain import CallbackHandler

from src.core.graph import app

warnings.filterwarnings("ignore", category=UserWarning)

logging.basicConfig(
    filename='debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console = Console()
langfuse_handler = CallbackHandler()

def extract_text_from_content(content):
    """
    Helper function: Extracts plain text string from the model's response.
    Handles the case where the model returns a list containing dict elements.
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        return "".join([item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"])
    return str(content)

def main():
    logging.info("--- Dungeon Master Application starts ---")
    
    if not os.environ.get("GROQ_API_KEY"):
        logging.error("Cannot find GROQ_API_KEY.")
        console.print("[bold red]Error: GROQ_API_KEY is not set![/bold red]")
        console.print("Please set it in your .env file or export it via terminal.")
        return

    welcome_msg = "[bold green] Welcome to AI Dungeon Master[/bold green]\nType 'quit' or 'exit' to end the adventure."
    console.print(Panel.fit(welcome_msg, border_style="green"))
    
    config = {
        "configurable": {"thread_id": "player_1"},
        "callbacks": [langfuse_handler]  # <--- BỔ SUNG LUÔN Ở ĐÂY
    }

    initial_state = {
        "current_location": "Abandoned Lighthouse - Ground Floor",
        "inventory": [],
        "memory_flags": {}
    }
    
    intro_text = "You awaken in an abandoned lighthouse overlooking a stormy sea. Rain crashes against the windows. A rusty key and a sealed letter lie on a wooden table. A staircase disappears into darkness above you. What do you do?"
    
    app.update_state(
        config, 
        {"messages": [{"role": "assistant", "content": intro_text}], **initial_state}
    )
    
    console.print(f"\n[bold magenta]Dungeon Master:[/bold magenta] {intro_text}\n")
    
    # Game Loop
    while True:
        try:
            user_input = console.input("[bold cyan]Player:[/bold cyan] ")
            
            if user_input.lower() in ['quit', 'exit']:
                console.print("[italic yellow]Thank you for playing. Farewell![/italic yellow]")
                logging.info("Player exits game safely.")
                break
            if not user_input.strip():
                continue
 
            events = app.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="values"
            )
            
            for event in events:
                last_message = event["messages"][-1]
                
                # Hiển thị log của Tool
                if last_message.type == "tool":
                    console.print(f"[dim italic]{last_message.content}[/dim italic]")
                    
                # Hiển thị AI response
                elif last_message.type == "ai" and not last_message.tool_calls:
                    # 2. Xử lý content bị vướng định dạng List/Dict của Gemini
                    clean_text = extract_text_from_content(last_message.content)
                
                    console.print(f"\n[bold magenta]Dungeon Master:[/bold magenta] {clean_text}\n")
                    
        except KeyboardInterrupt:
            console.print("\n[italic yellow]Adventure terminated by user.[/italic yellow]")
            logging.info("The program is interrupted by KeyboardInterrupt (Ctrl+C).")
            break
        except Exception as e:
            console.print(f"\n[bold red]System Error:[/bold red] {e}")
            logging.error(f"System Error: {e}", exc_info=True)

if __name__ == "__main__":
    main()