# PostAI - AI Email Agent ✉️

An autonomous AI email assistant powered by **Ollama** and **LangChain**. It drafts, refines, sends, and schedules emails through natural language conversation.

## Features

- **Natural language drafting** — describe what you want, the agent writes it
- **Multi-turn refinement** — iteratively improve drafts via conversation
- **SMTP send** — works with Gmail, Outlook, any SMTP provider
- **Email scheduling** — schedule sends for a future datetime
- **Draft persistence** — all drafts saved to JSON (swap for Redis/DB easily)
- **Rich terminal UI** — beautiful CLI with markdown rendering
- **Conversation memory** — maintains context across your session

## 📂 Project Structure

```
PostAI-EmailAgent/
│
├── main.py                  # CLI entrypoint
├── agents/
│   ├── prompt_template.py   # Agent system prompt
│   └── email_agent.py       # LangChain agent + Ollama LLM
├── tools/
│   ├── email_tools.py       # LangChain @tool definitions
│   └── draft_store.py       # JSON-backed draft persistence
├── logs/
│   ├── agent.log            # Runtime logs
│   └── drafts.json          # Saved drafts
├── .env.example             # Config template
└── requirements.txt
```

## Quickstart

### 1. Clone & install

```bash
git clone https://github.com/Shabeenabd/PostAI-EmailAgent.git
cd PostAI-EmailAgent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```
**Edit `.env`:**
```bash
OLLAMA_MODEL=llama3
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
```
**Gmail setup:**
1. Enable 2-Factor Authentication on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Generate an App Password and paste it as `SENDER_PASSWORD`

### 3. Run

```bash
python main.py
```

## Example Session

```
You: Draft a professional follow-up to sarah@company.com about our product demo last Tuesday

Agent: I've created draft [a3f1c2]:
  To: sarah@company.com
  Subject: Follow-Up: Product Demo — Next Steps
  Body: Dear Sarah, Thank you for taking the time...
  
  Shall I send it, or would you like any changes?

You: Make it shorter and more direct

Agent: Updated draft [a3f1c2] — more concise version:
  ...

You: Send it using my Gmail

Agent: Email sent successfully to sarah@company.com at 2:34 PM.
```

## Available Tools

| Tool | Description |
|------|-------------|
| ✍️ `draft_email` | Create a new email draft with to/subject/body/tone |
| 🔧 `refine_email` | Update an existing draft based on feedback |
| 📤 `send_email` | Send a draft via SMTP |
| ⏰ `schedule_email` | Schedule a draft for future delivery |
| 📋 `list_drafts` | List all drafts (filter by status) |
| 🗑 `delete_email` | Delete an emal from drafts |

## Extending

**Add a new tool:**
```python
from langchain_core.tools import tool

@tool
def translate_email_tool(draft_id: str, language: str) -> str:
    """Translate a draft email to another language."""
    ...
```
Then add it to the `tools` list in `agents/email_agent.py`.

**Swap the draft store for Redis:**
```python
import redis
r = redis.Redis()
r.set(f"draft:{draft_id}", json.dumps(draft))
```

**Add a web UI:** wrap `build_agent()` with FastAPI + WebSockets for a browser-based interface.

## ⚙️ Environment Variables

| Variable | Description |
|----------|-------------|
| `OLLAMA_MODEL` | Your local ollama model |
| `SMTP_HOST` | SMTP server (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | Port — 587 (TLS) or 465 (SSL) |
| `SENDER_EMAIL` | Your email address |
| `SENDER_PASSWORD` | App password |

## 📦 Requirements

- Python 3.10+
- Ollama
- SMTP credentials (Gmail App Password recommended)
