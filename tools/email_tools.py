"""
LangChain tools used by the email agent.
Each tool is a self-contained unit the LLM can invoke.
"""
import json
import logging
from datetime import datetime
import os
import uuid
import smtplib
from typing import Any, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from langchain_core.tools import tool

from tools.draft_store import DraftStore
 
logger = logging.getLogger(__name__)
store = DraftStore()

 # Draft ─────────────────────────────────────────────────────────────────────
 
@tool
def draft_email_tool(
    to: str,
    subject: str,
    body: str,
    tone: str = "professional",
    cc: str = "",
    bcc: str = "",
) -> str:
    """
    Create and store a new email draft.-
 
    Args:
        to: Recipient email address(es), comma-separated.
        subject: Email subject line.
        body: Full email body text.
        tone: Tone used — professional, casual, formal, friendly, assertive.
        cc: Optional CC addresses.
        bcc: Optional BCC addresses.
 
    Returns:
        JSON string with draft_id and a preview of the draft.
    """
    draft_id = str(uuid.uuid4())[:8]
    draft = {
        "id": draft_id,
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "subject": subject,
        "body": body,
        "tone": tone,
        "created_at": datetime.now().isoformat(),
        "status": "draft",
    }
    store.save(draft_id, draft)
    logger.info("Draft created: %s", draft_id)
    
    return json.dumps({
        "draft_id": draft_id,
        "preview": {
            "to": to,
            "subject": subject,
            "body_preview": body[:200] + ("…" if len(body) > 200 else ""),
            "tone": tone,
        },
        "message": f"Draft saved with ID: {draft_id}. Review and confirm to send.",
    }, indent=2)
 
 # ── Refine ────────────────────────────────────────────────────────────────────
 
@tool
def refine_email_tool(
    draft_id: str,
    instruction: str,
    new_tone: Optional[str] = None,
) -> str:
    """
    Refine an existing draft based on user feedback.
 
    Args:
        draft_id: The ID of the draft to refine.
        instruction: What to change, e.g. 'make it shorter', 'sound friendlier'.
        new_tone: Optional new tone to apply.
 
    Returns:
        JSON with the updated draft details.
    """
    draft = store.load(draft_id)
    if not draft:
        return json.dumps({"error": f"Draft '{draft_id}' not found."})
 
    # The LLM will handle actual text rewriting — here we record the instruction
    # so it can be shown as part of the refinement history.
    draft["last_refinement"] = instruction
    if new_tone:
        draft["tone"] = new_tone
    draft["updated_at"] = datetime.now().isoformat()
    store.save(draft_id, draft)
 
    return json.dumps({
        "draft_id": draft_id,
        "instruction_recorded": instruction,
        "current_draft": {
            "to": draft["to"],
            "subject": draft["subject"],
            "body": draft["body"],
            "tone": draft["tone"],
        },
        "message": "Apply the refinement instruction to the body above, then show the updated draft to the user.",
    }, indent=2)
 
 
# ── Send ──────────────────────────────────────────────────────────────────────
 
@tool
def send_email_tool(
    draft_id: str,
    use_tls: bool = True,
) -> str:
    """
    Send a saved draft via SMTP.
 
    Args:
        draft_id: Draft ID to send.
        use_tls: Whether to use STARTTLS (recommended).
 
    Returns:
        JSON with send status.
    """
    smtp_host: str = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", 587))
    sender_email: str = os.getenv("SENDER_EMAIL")
    sender_password: str = os.getenv("SENDER_PASSWORD")

    draft = store.load(draft_id)
    if not draft:
        return json.dumps({"error": f"Draft '{draft_id}' not found."})
 
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = draft["to"]
    msg["Subject"] = draft["subject"]
    if draft.get("cc"):
        msg["Cc"] = draft["cc"]
 
    msg.attach(MIMEText(draft["body"], "plain"))
 
    recipients = [r.strip() for r in draft["to"].split(",")]
    if draft.get("cc"):
        recipients += [r.strip() for r in draft["cc"].split(",")]
    if draft.get("bcc"):
        recipients += [r.strip() for r in draft["bcc"].split(",")]
 
    try:
        if use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
 
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
 
        draft["status"] = "sent"
        draft["sent_at"] = datetime.now().isoformat()
        store.save(draft_id, draft)
 
        logger.info("Email sent: %s → %s", draft_id, draft["to"])
        return json.dumps({
            "success": True,
            "draft_id": draft_id,
            "sent_to": draft["to"],
            "subject": draft["subject"],
            "sent_at": draft["sent_at"],
        }, indent=2)
 
    except smtplib.SMTPAuthenticationError:
        return json.dumps({"error": "SMTP authentication failed. Check email/password."})
    except smtplib.SMTPException as exc:
        return json.dumps({"error": f"SMTP error: {exc}"})
    except Exception as exc:
        return json.dumps({"error": f"Unexpected error: {exc}"})
 
 
# ── List drafts ───────────────────────────────────────────────────────────────
 
@tool
def list_drafts_tool(status_filter: str = "all") -> str:
    """
    List all saved email drafts.
 
    Args:
        status_filter: Filter by status — 'all', 'draft', 'sent', 'scheduled'.
 
    Returns:
        JSON list of drafts.
    """
    all_drafts = store.list_all()
    if status_filter != "all":
        all_drafts = [d for d in all_drafts if d.get("status") == status_filter]
 
    summary = [
        {
            "id": d["id"],
            "to": d["to"],
            "subject": d["subject"],
            "status": d["status"],
            "created_at": d["created_at"],
        }
        for d in all_drafts
    ]
    return json.dumps({"count": len(summary), "drafts": summary}, indent=2)
 
 
# ── Schedule ──────────────────────────────────────────────────────────────────
 
@tool
def schedule_email_tool(draft_id: str, send_at: str) -> str:
    """
    Schedule a draft to be sent at a future time.
 
    Args:
        draft_id: Draft ID to schedule.
        send_at: ISO 8601 datetime string, e.g. '2025-09-01T09:00:00'.
 
    Returns:
        JSON with schedule confirmation.
    """
    draft = store.load(draft_id)
    if not draft:
        return json.dumps({"error": f"Draft '{draft_id}' not found."})
 
    try:
        scheduled_dt = datetime.fromisoformat(send_at)
    except ValueError:
        return json.dumps({"error": f"Invalid datetime format: '{send_at}'. Use ISO 8601."})
 
    if scheduled_dt <= datetime.now():
        return json.dumps({"error": "Scheduled time must be in the future."})
 
    draft["status"] = "scheduled"
    draft["scheduled_for"] = scheduled_dt.isoformat()
    store.save(draft_id, draft)
 
    return json.dumps({
        "draft_id": draft_id,
        "scheduled_for": scheduled_dt.isoformat(),
        "subject": draft["subject"],
        "to": draft["to"],
        "message": f"Email scheduled for {scheduled_dt.strftime('%B %d, %Y at %I:%M %p')}.",
    }, indent=2)

# ── Delete ──────────────────────────────────────────────────────────────────

@tool
def delete_draft_tool(draft_id: str) -> str:
    """
    Delete a draft by ID.
 
    Args:
        draft_id: The ID of the draft to delete.
 
    Returns:
        JSON with deletion status.
    """
    success = store.delete(draft_id)
    if success:
        logger.info("Draft deleted: %s", draft_id)
        return json.dumps({"success": True, "message": f"Draft '{draft_id}' deleted."})
    else:
        return json.dumps({"error": f"Draft '{draft_id}' not found."})