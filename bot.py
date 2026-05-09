"""Telegram bot entry point for the Agentic Teaching Assistant homework."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
import os
from pathlib import Path
import shlex

from dotenv import load_dotenv
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from agents.orchestrator import LessonRequest, TeachingAssistantAgent
from tools.email import send_email
from tools.logger import log_event
from tools.slides import parse_slides
from tools.web_search import resources_to_markdown, search_web

load_dotenv()


@dataclass
class SessionState:
    uploaded_file: str | None = None
    latest_package: str | None = None
    latest_email_subject: str | None = None
    latest_email_body: str | None = None
    recipient_email: str | None = None
    last_error: str | None = None
    awaiting_send_confirmation: bool = False
    metadata: dict[str, str] = field(default_factory=dict)


SESSIONS: dict[int, SessionState] = {}


def get_state(chat_id: int) -> SessionState:
    if chat_id not in SESSIONS:
        SESSIONS[chat_id] = SessionState()
    return SESSIONS[chat_id]


def _parse_plan_args(text: str) -> dict[str, str]:
    """Parse /plan duration=90 audience="..." language=English email=x@y.com."""
    parts = shlex.split(text)
    args: dict[str, str] = {}
    for token in parts[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            args[key.strip().lower()] = value.strip()
        elif token.isdigit() and "duration" not in args:
            args["duration"] = token
    return args


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "Hello! I am an Agentic Teaching Assistant bot.\n\n"
        "Upload a lecture PDF, then run:\n"
        "/plan duration=90 audience=\"BA NLP students\" language=English email=name@example.com\n\n"
        "I will parse the slides, use a local LLM, search the web, show a preview, "
        "and send the email only after you confirm with /send."
    )
    await update.message.reply_text(message)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "Commands:\n"
        "/start - introduce the bot and show an example.\n"
        "/help - list commands and limitations.\n"
        "/plan duration=90 audience=\"...\" language=English email=x@y.com - generate package.\n"
        "/research - return supporting web resources for the uploaded slides.\n"
        "/status - show uploaded file, state, and errors.\n"
        "/send - confirm and send the latest preview by email.\n\n"
        "Limitations: PDF is preferred. PPTX is supported as a bonus. Scanned PDFs need OCR, "
        "which is not included in this minimal version."
    )
    await update.message.reply_text(message)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    document = update.message.document
    filename = document.file_name or "uploaded_slides.pdf"
    suffix = Path(filename).suffix.lower()

    if suffix not in {".pdf", ".pptx"}:
        state.last_error = "Unsupported file type. Please upload PDF or PPTX."
        await update.message.reply_text(state.last_error)
        return

    upload_dir = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = filename.replace("/", "_").replace("\\", "_")
    target = upload_dir / f"{chat_id}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{safe_name}"

    file_obj = await context.bot.get_file(document.file_id)
    await file_obj.download_to_drive(custom_path=str(target))

    try:
        chunks = await asyncio.to_thread(parse_slides, target)
        state.uploaded_file = str(target)
        state.last_error = None
        log_event(chat_id, "file_uploaded", {"path": str(target), "slides": len(chunks)})
        await update.message.reply_text(
            f"Uploaded and parsed {len(chunks)} slide/page(s). Now run /plan with duration, audience, language, and email."
        )
    except Exception as exc:  # noqa: BLE001
        state.last_error = str(exc)
        log_event(chat_id, "file_parse_error", {"error": str(exc)})
        await update.message.reply_text(f"I could not parse this file: {exc}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    text = (
        f"Uploaded file: {state.uploaded_file or 'None'}\n"
        f"Latest package: {'Yes' if state.latest_package else 'No'}\n"
        f"Recipient email: {state.recipient_email or 'Not set'}\n"
        f"Awaiting /send confirmation: {state.awaiting_send_confirmation}\n"
        f"Last error: {state.last_error or 'None'}"
    )
    await update.message.reply_text(text)


async def research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    if not state.uploaded_file:
        await update.message.reply_text("Please upload lecture slides first.")
        return
    try:
        chunks = await asyncio.to_thread(parse_slides, state.uploaded_file)
        query = " ".join(chunk.text[:80] for chunk in chunks[:2])[:220]
        resources, error = await asyncio.to_thread(search_web, query, 5)
        await update.message.reply_text(resources_to_markdown(resources, error)[:3900])
    except Exception as exc:  # noqa: BLE001
        state.last_error = str(exc)
        await update.message.reply_text(f"Research failed: {exc}")


async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    if not state.uploaded_file:
        await update.message.reply_text("Please upload a lecture PDF/PPTX before running /plan.")
        return

    args = _parse_plan_args(update.message.text or "")
    try:
        duration = int(args.get("duration", "90"))
    except ValueError:
        duration = 90
    audience = args.get("audience", "university students")
    language = args.get("language", "English")
    email = args.get("email", "")

    if not email or "@" not in email:
        await update.message.reply_text(
            "Please include a recipient email, e.g. /plan duration=90 audience=\"BA NLP students\" language=English email=name@example.com"
        )
        return

    await update.message.reply_text("Generating the teaching package with the local LLM and tools...")
    request = LessonRequest(
        duration_minutes=duration,
        audience=audience,
        output_language=language,
        recipient_email=email,
    )
    agent = TeachingAssistantAgent(chat_id=chat_id)

    try:
        result = await asyncio.to_thread(agent.run, state.uploaded_file, request)
        state.latest_package = result.package_md
        state.latest_email_subject = result.email_subject
        state.latest_email_body = result.email_body
        state.recipient_email = email
        state.awaiting_send_confirmation = True
        state.last_error = None

        preview = result.package_md[:3500]
        if len(result.package_md) > len(preview):
            preview += "\n\n...preview truncated in Telegram. Full text will be emailed."
        await update.message.reply_text(
            f"Preview generated. Review it, then run /send to confirm email delivery.\n\n{preview}"
        )
    except Exception as exc:  # noqa: BLE001
        state.last_error = str(exc)
        log_event(chat_id, "plan_error", {"error": str(exc)})
        try:
            await update.message.reply_text(f"Plan generation failed: {exc}")
        except TelegramError as notify_exc:
            log_event(chat_id, "telegram_reply_error", {"error": repr(notify_exc)})


async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    if not state.latest_package or not state.recipient_email:
        await update.message.reply_text("No approved preview is ready. Run /plan first.")
        return
    if not state.awaiting_send_confirmation:
        await update.message.reply_text("There is no pending email confirmation. Run /plan to create a new preview.")
        return

    subject = state.latest_email_subject or "Lesson plan generated from slides"
    body = state.latest_email_body or state.latest_package
    try:
        await asyncio.to_thread(send_email, state.recipient_email, subject, body)
        state.awaiting_send_confirmation = False
        log_event(chat_id, "email_sent", {"to": state.recipient_email, "subject": subject})
        await update.message.reply_text(f"Email sent to {state.recipient_email}.")
    except Exception as exc:  # noqa: BLE001
        state.last_error = str(exc)
        log_event(chat_id, "email_error", {"error": str(exc)})
        await update.message.reply_text(f"Email sending failed: {exc}")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Persist unhandled handler exceptions to app logs."""
    chat_id = -1
    if isinstance(update, Update) and update.effective_chat:
        chat_id = update.effective_chat.id
    log_event(chat_id, "telegram_handler_error", {"error": repr(context.error)})


def build_app():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to .env.")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("research", research))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(on_error)
    return app


if __name__ == "__main__":
    application = build_app()
    application.run_polling(
        timeout=20,
        bootstrap_retries=3,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
