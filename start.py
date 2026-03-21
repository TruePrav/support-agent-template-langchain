"""
Start both the Telegram bot and web chat server simultaneously.
Run: python start.py

This starts two processes in parallel:
  - telegram_bot.py  (Telegram polling loop)
  - web_bot.py       (FastAPI server on port 8001)

Meta (WhatsApp/Instagram/Messenger) is intentionally NOT started here.
Reason: Meta requires a publicly accessible HTTPS webhook URL, which means
it can only run on a deployed server (Railway, DigitalOcean, etc.) -- not locally.
To add Meta to this start script after deployment, ask Claude Code:
  "Add meta_bot.py to start.py so all channels start together"
"""

import threading
import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
PYTHON = sys.executable


def run_telegram():
    """Run the Telegram bot in a subprocess. Logs errors if it crashes."""
    try:
        logger.info("Starting Telegram bot...")
        subprocess.run([PYTHON, str(BASE / "telegram_bot.py")], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Telegram bot crashed with exit code {e.returncode}")
    except Exception as e:
        logger.error(f"Telegram bot error: {e}")


def run_web():
    """Run the web chat server in a subprocess. Logs errors if it crashes."""
    try:
        logger.info("Starting web chat server on port 8001...")
        subprocess.run([PYTHON, str(BASE / "web_bot.py")], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Web server crashed with exit code {e.returncode}")
    except Exception as e:
        logger.error(f"Web server error: {e}")


if __name__ == "__main__":
    print("\nSupport Agent")
    print("-------------")
    print("  Telegram bot : polling for messages")
    print("  Web chat     : http://localhost:8001")
    print("")
    print("  Meta (WhatsApp/Instagram): not started here")
    print("  Reason: Meta needs a public HTTPS URL -- deploy first, then run meta_bot.py")
    print("")
    print("  Press Ctrl+C to stop both\n")

    # Start both bots in daemon threads so Ctrl+C stops everything cleanly
    t1 = threading.Thread(target=run_telegram, daemon=True)
    t2 = threading.Thread(target=run_web, daemon=True)

    t1.start()
    t2.start()

    try:
        # Keep main thread alive until both subprocesses finish or Ctrl+C
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("\nStopped.")
