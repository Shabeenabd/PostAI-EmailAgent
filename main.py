"""
AI Email Agent — interactive CLI.
Run: python main.py
"""
import os
import sys
import requests
from typing import Any
import logging

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.theme import Theme

from agent.email_agent import build_agent

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL","gpt-oss:120b-cloud")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/agent.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── Console theme ─────────────────────────────────────────────────────────────
theme = Theme({
    "agent": "bold cyan",
    "user": "bold green",
    "tool": "dim yellow",
    "error": "bold red",
    "info": "dim white",
})

console = Console(theme=theme)
 
BANNER = """
╔══════════════════════════════════════════╗
║   Post AI - AI Email Agent  ✉  v1.0      ║
║   Powered by Ollama + LangChain          ║
╚══════════════════════════════════════════╝
"""
 
HELP_TEXT = """
**Commands**
- Type anything to talk to the agent
- `drafts`  — list all saved drafts
- `clear`   — clear conversation history
- `help`    — show this message
- `quit`    — exit
 
**Example prompts**
- *"Draft a professional follow-up email to john@acme.com about our meeting"*
- *"Make it more concise and add a call to action"*
- *"Send draft abc123 using Gmail"*
- *"Schedule it for tomorrow at 9am"*
"""

def validate_env() -> None:
    """Ensure required env vars are present."""
    required_vars = ["OLLAMA_MODEL", "SENDER_EMAIL", "SENDER_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        console.print(f"[error]Missing environment variables: {', '.join(missing)}[/error]")
        sys.exit(1)

def validate_ollama() -> None:
    try:
        response = requests.get("http://localhost:11434")
        if response.status_code == 200:
            console.print("[info]Ollama is running ...[/info]")
        else:
            console.print("[error]Connection to Ollama failed.[/error]")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        console.print("[error]Ollama is not running. Please start Ollama and try again.[/error]")
        sys.exit(1)

def run_cli() -> None:
    validate_env()

    with console.status("[info]Checking Ollama connection...[/info]", spinner="dots"):
            validate_ollama()

    console.print(BANNER, style="agent")
    console.print(Markdown(HELP_TEXT))
    console.rule(style="dim")

    agent = build_agent(model=OLLAMA_MODEL)
    chat_history : list[Any] = []

    while True:
        try:
            user_input = Prompt.ask("\n[user]You[/user]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[info]Goodbye![/info]")
            break

        if not user_input:
            continue
 
        # Built-in commands
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[info]Goodbye![/info]")
            break
        
        if user_input.lower() == "help":
            console.print(Markdown(HELP_TEXT))
            continue
 
        if user_input.lower() == "clear":
            chat_history.clear()
            console.print("[info]Conversation history cleared.[/info]")
            continue
 
        if user_input.lower() == "drafts":
            user_input = "List all my email drafts."
        
        # Run agent
        console.rule(style="dim")
        with console.status("[agent]Agent thinking…[/agent]", spinner="dots"):
            try:
                result = agent.invoke({
                    "input": user_input,
                    "chat_history": chat_history,
                })
                response = result.get("output", "No response.")
            except Exception as exc:
                logger.exception("Agent error")
                response = f"Agent encountered an error: {exc}"

        # Update history
        from langchain_core.messages import AIMessage, HumanMessage
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response))
 
        # Trim history to last 10 exchanges (20 messages)
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]
 
        # Display response
        console.print(
            Panel(
                Markdown(response),
                title="[agent]Agent[/agent]",
                border_style="cyan",
                padding=(0, 1),
            )
        )

if __name__ == "__main__":
    run_cli()