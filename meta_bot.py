"""
Meta Bot — WhatsApp, Instagram DMs, and Facebook Messenger via Meta Cloud API.
Same agent brain as telegram_bot.py — just a different channel.

Setup:
1. Create a Meta App at developers.facebook.com
2. Add WhatsApp / Messenger / Instagram products
3. Set webhook URL to: https://yourdomain.com/webhook
4. Add WHATSAPP_TOKEN, META_VERIFY_TOKEN to your .env

Run: python meta_bot.py (runs on port 8002)
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from agent import build_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
WHATSAPP_TOKEN   = os.getenv("WHATSAPP_TOKEN", "")       # Meta permanent token
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")   # Any string you choose
PHONE_NUMBER_ID  = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")  # From Meta dashboard
ESCALATION_CHAT_ID = os.getenv("ESCALATION_CHAT_ID", "")

# WhatsApp Cloud API endpoint
WA_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

chain = build_agent()


# ── Webhook verification (Meta requires this on setup) ──────────────────────
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == META_VERIFY_TOKEN:
        logger.info("Webhook verified")
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


# ── Incoming messages ────────────────────────────────────────────────────────
@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()

    try:
        entry    = data["entry"][0]
        changes  = entry["changes"][0]["value"]
        messages = changes.get("messages", [])

        if not messages:
            return {"status": "ok"}

        msg      = messages[0]
        platform = detect_platform(changes)
        sender   = msg["from"]           # phone number or PSID
        text     = extract_text(msg)

        if not text:
            return {"status": "ok"}

        logger.info(f"Message from {sender} via {platform}: {text}")

        session_id = f"{platform}:{sender}"
        result = chain.invoke(
            {"input": text},
            config={"configurable": {"session_id": session_id}},
        )
        reply = result.content if hasattr(result, "content") else str(result)

        if reply.upper().startswith("ESCALATE"):
            reason = reply.split("--", 1)[-1].strip() if "--" in reply else "Needs human support"
            await notify_escalation(sender, text, reason, platform)
            reply = "I'm connecting you with a team member right now. Someone will be with you shortly."

        await send_whatsapp_reply(sender, reply)

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return {"status": "ok"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def detect_platform(changes: dict) -> str:
    """Detect if message came from WhatsApp, Instagram, or Messenger."""
    metadata = changes.get("metadata", {})
    phone_id = metadata.get("phone_number_id", "")
    if phone_id:
        return "whatsapp"
    if "instagram" in str(changes).lower():
        return "instagram"
    return "messenger"


def extract_text(msg: dict) -> str:
    """Extract text from any message type."""
    msg_type = msg.get("type", "")
    if msg_type == "text":
        return msg["text"]["body"]
    if msg_type == "interactive":
        # Button reply
        interactive = msg.get("interactive", {})
        if interactive.get("type") == "button_reply":
            return interactive["button_reply"]["title"]
    return ""


async def send_whatsapp_reply(to: str, text: str):
    """Send a WhatsApp message via Meta Cloud API."""
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.warning("WHATSAPP_TOKEN or PHONE_NUMBER_ID not set — skipping send")
        return

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(WA_API_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            logger.error(f"WhatsApp send failed: {resp.text}")
        else:
            logger.info(f"Sent reply to {to}")


async def notify_escalation(sender: str, message: str, reason: str, platform: str):
    """Send escalation alert via Telegram to the business owner."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = ESCALATION_CHAT_ID
    if not token or not chat_id:
        return

    alert = (
        f"🚨 ESCALATION NEEDED\n\n"
        f"Platform: {platform.upper()}\n"
        f"Customer: {sender}\n"
        f"Message: {message}\n"
        f"Reason: {reason}"
    )
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": alert}
        )


if __name__ == "__main__":
    logger.info("Meta bot starting — waiting for webhooks...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
