"""
Telegram Bot — connects your support agent to Telegram.
Built by TruePrav / ailevelup.ca

This file handles everything Telegram-related:
- Receiving messages from customers
- Sending responses back
- Detecting escalations and alerting you
- Showing the typing indicator while the agent is thinking

The agent logic lives in agent.py — this file just handles the channel.
That separation means you could swap Telegram for WhatsApp or Discord
by replacing this file, without touching agent.py at all.
"""

import os
import logging
import time
from collections import defaultdict
from dotenv import load_dotenv

# python-telegram-bot is the library that connects to Telegram's API.
# Update = one incoming event (a message, a button press, etc.)
# Application = the bot runner — manages the connection and dispatches events
# CommandHandler = handles /commands like /start
# MessageHandler = handles regular text messages
# filters = lets you specify which messages to handle (text only, not commands, etc.)
# ContextTypes = type hints for the bot context object
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Import the chat function from agent.py — this is the only connection between the two files
from agent import chat

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# These come from your .env file
BOT_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN")
ESCALATION_CHAT = os.getenv("ESCALATION_CHAT_ID")  # your personal Telegram ID

# ── Rate Limiting ─────────────────────────────────────────────────────────────
# Tracks message timestamps per user to enforce a per-minute limit.
# Prevents abuse and protects your OpenAI bill.
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
_user_message_times: dict = defaultdict(list)

def is_rate_limited(user_id: str) -> bool:
    """Return True if user has exceeded RATE_LIMIT messages in the last 60 seconds."""
    now = time.time()
    times = _user_message_times[user_id]
    # Drop timestamps older than 60 seconds
    _user_message_times[user_id] = [t for t in times if now - t < 60]
    if len(_user_message_times[user_id]) >= RATE_LIMIT:
        return True
    _user_message_times[user_id].append(now)
    return False


# ── /start command ───────────────────────────────────────────────────────────
# Fires when someone first messages the bot or sends /start.
# Good place for a welcome message — keep it short.
# In production you might also log new users to a CRM here.

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command — greet new users."""
    await update.message.reply_text(
        "Hi! I'm the support assistant. How can I help you today?"
    )


# ── Main message handler ─────────────────────────────────────────────────────
# This fires for every text message the bot receives.
# The flow is:
# 1. Extract who sent it and what they said
# 2. Show the typing indicator (so the user knows something is happening)
# 3. Pass the message to agent.py with a unique session_id
# 4. Check if the response is an escalation
# 5. Send the response back

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process every incoming customer message."""

    # Telegram gives us the user's ID (a number) and their display name
    user_id   = str(update.effective_user.id)    # unique per Telegram account, never changes
    user_name = update.effective_user.first_name or "Customer"
    user_input = update.message.text

    logger.info(f"Message from {user_name} ({user_id}): {user_input[:80]}")

    # Check rate limit before doing anything
    if is_rate_limited(user_id):
        logger.warning(f"Rate limit hit for user {user_id}")
        await update.message.reply_text(
            "You're sending messages too fast. Please wait a moment and try again."
        )
        return

    # Send typing indicator — Telegram shows "typing..." in the chat
    # while the model is generating a response. Small UX detail that matters.
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Call the agent with graceful error handling
    try:
        response = chat(message=user_input, session_id=f"telegram:{user_id}")
    except Exception as e:
        logger.error(f"Agent error for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I'm having trouble right now. Please try again in a moment."
        )
        return

    # Check if the agent is asking us to escalate.
    if response.upper().startswith("ESCALATE"):
        await handle_escalation(update, context, user_name, user_id, user_input, response)
        return

    await update.message.reply_text(response)


# ── Escalation handler ───────────────────────────────────────────────────────
# When the agent detects it can't help (or the customer asks for a human),
# two things happen simultaneously:
# 1. The customer gets a warm handoff message
# 2. You get an alert on Telegram with full context
#
# The alert includes a deep link (tg://user?id=...) so you can tap it
# and open a direct chat with the customer immediately.
#
# In a more advanced version, you'd also create a ticket in your CRM here,
# or notify a team Slack channel instead of just your personal Telegram.

async def handle_escalation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_name: str,
    user_id: str,
    user_input: str,
    agent_response: str,
):
    """Send a handoff message to the customer and an alert to you."""

    # Tell the customer a human is taking over
    await update.message.reply_text(
        "Of course! Let me connect you with a team member right now. "
        "Someone will be with you shortly."
    )

    # Alert you (or your team) on Telegram
    if ESCALATION_CHAT:
        # Strip the "ESCALATE --" prefix to get just the reason
        reason = agent_response.replace("ESCALATE --", "").replace("ESCALATE -", "").strip()

        alert = (
            f"ESCALATION NEEDED\n\n"
            f"Customer: {user_name} (ID: {user_id})\n"
            f"Their message: {user_input}\n"
            f"Reason: {reason}\n\n"
            f"Tap to open chat: tg://user?id={user_id}"
            # Note: the deep link only works if the customer has messaged you before
        )
        try:
            await context.bot.send_message(chat_id=ESCALATION_CHAT, text=alert)
            logger.info(f"Escalation alert sent for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send escalation alert: {e}")


# ── Error handler ────────────────────────────────────────────────────────────
# If anything unexpected fails (network timeout, Telegram API error, etc.)
# this logs it instead of crashing the entire bot.

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors without crashing the bot."""
    logger.error(f"Update {update} caused error: {context.error}")


# ── Main ─────────────────────────────────────────────────────────────────────
# Application.builder() creates the bot with your token.
# add_handler() registers which function handles which type of event.
# run_polling() starts a long-running loop that checks Telegram for new messages.
# This is the "always on" loop — it runs until you kill the process.
#
# In production on a server: this process runs 24/7.
# You use a process manager (systemd, screen, or Railway's built-in runner)
# to keep it alive and restart it if it crashes.

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers in priority order
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    # filters.TEXT = only text messages (not photos, stickers, etc.)
    # ~filters.COMMAND = exclude /commands (handled separately above)
    app.add_error_handler(error_handler)

    logger.info("Bot starting — waiting for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
