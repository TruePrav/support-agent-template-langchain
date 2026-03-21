# CONTRACT — Web Chat Widget

**Goal:** Add a working website chat widget that uses the same agent.py brain as the Telegram bot.

**Done when:**
- [ ] `web_bot.py` — FastAPI server with POST /chat endpoint that calls agent.chat()
- [ ] `static/index.html` — demo webpage with floating chat bubble (bottom right)
- [ ] Chat widget opens/closes, sends messages, shows typing indicator, displays replies
- [ ] Works by running `python web_bot.py` and visiting http://localhost:8000
- [ ] No new dependencies beyond what's in requirements.txt except `fastapi` and `uvicorn`
- [ ] CORS enabled so it works from any domain
- [ ] Session ID derived from browser session (localStorage UUID) — each visitor gets their own memory

**Out of scope:**
- Do NOT touch agent.py, telegram_bot.py, system-prompt.md, kb.md
- No auth, no database changes, no deployment config
- No React or build tools — plain HTML/CSS/JS only

**Style:**
- Dark theme chat bubble, bottom right corner
- Branded: "NovaTech Support" header
- Typing indicator (3 dots) while waiting for response
- Mobile friendly
