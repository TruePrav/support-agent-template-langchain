# Support Agent Template
### Build a production AI customer support agent in under 30 minutes.

Built by [@TruePrav](https://twitter.com/trueprav) | [ailevelup.ca](https://ailevelup.ca)

**No coding experience required.** Follow this README from top to bottom. Every step has exact commands to copy-paste.

---

## What this builds

You get **two AI customer support bots** that share the same brain:

1. **A Telegram bot** -- customers message your bot on Telegram, the AI answers instantly. When it can't help, it alerts you on your phone so you can take over.

2. **A website chat widget** -- a floating chat bubble on your website, same AI underneath. Looks professional, works on any site.

Both bots read from the same `knowledge-base/kb.md` file. Update that file and both bots instantly know the new information -- no restarts, no code changes.

---

## Quick Start with Claude Code

If you have Claude Code installed, paste this prompt to get fully set up automatically:

```
Clone the repo, read README.md, then:
1. Customize system-prompt.md for my business: [YOUR BUSINESS NAME], [DESCRIBE WHAT YOU SELL]
2. Rewrite knowledge-base/kb.md with: hours [YOUR HOURS], location [YOUR ADDRESS], products [YOUR PRODUCTS], return policy [YOUR POLICY]
3. Fill in .env with my keys (I will provide them)
4. Run python telegram_bot.py to start the Telegram bot
5. Run python web_bot.py to start the website chat widget
Do not stop until both bots are running and tested.
```

Claude Code handles the rest in under 30 minutes. Or keep reading to do it manually.

---

## Table of Contents

1. [What you need before starting](#what-you-need-before-starting)
2. [Installation](#installation)
3. [Configuration -- filling in your .env](#configuration)
4. [Customizing for your business](#customizing-for-your-business)
5. [Running the bot](#running-the-bot)
6. [Testing with eval.py](#testing-with-evalpy)
7. [Web Widget Setup](#web-widget-setup)
8. [Meta / WhatsApp Setup (advanced)](#meta--whatsapp-setup-advanced)
9. [Going to production (24/7 uptime)](#going-to-production)
10. [Troubleshooting](#troubleshooting)
11. [How the code works](#how-the-code-works)

---

## What you need before starting

You need accounts at these services. All free or low cost:

| What | Cost | Link | Why you need it |
|------|------|------|-----------------|
| OpenAI | Pay per use (~$1-5/mo) | [platform.openai.com](https://platform.openai.com) | The AI brain |
| Telegram (personal) | Free | [telegram.org](https://telegram.org) | To create your bot |
| Supabase | Free | [supabase.com](https://supabase.com) | Stores conversation memory |
| Python 3.10+ | Free | [python.org/downloads](https://python.org/downloads) | Runs the code |

> **Don't have Python?** Go to [python.org/downloads](https://python.org/downloads), download the latest version, run the installer. On Windows: check "Add Python to PATH" during install.

---

## Installation

Open a terminal (on Windows: press `Win + R`, type `cmd`, hit Enter).

Run these commands one at a time. Copy-paste exactly as shown.

**Step 1 -- Download the template:**
```bash
git clone https://github.com/trueprav/support-agent-template
cd support-agent-template
```

> **Don't have Git?** Download from [git-scm.com](https://git-scm.com/downloads). Or download the ZIP from GitHub and extract it -- then `cd` into the folder.

**Step 2 -- Create a virtual environment** (keeps dependencies isolated):
```bash
python -m venv venv
```

**Step 3 -- Activate the virtual environment:**

On Mac/Linux:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal line. That means it's active.

**Step 4 -- Install dependencies:**
```bash
pip install -r requirements.txt
```

This takes 1-2 minutes. It downloads all the libraries the agent needs.

---

## Configuration

**Step 1 -- Copy the example config:**

On Mac/Linux:
```bash
cp .env.example .env
```

On Windows:
```bash
copy .env.example .env
```

**Step 2 -- Get your API keys:**

**OpenAI API key:**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key -- it starts with `sk-`

**Telegram bot token:**
1. Open Telegram on your phone
2. Search for `@BotFather`
3. Send the message: `/newbot`
4. It will ask for a name (e.g. "Acme Support") and a username ending in `_bot`
5. Copy the token it gives you -- looks like `7123456789:AAFabcdef...`

**Your Telegram chat ID** (where escalation alerts go):
1. On Telegram, search for `@userinfobot`
2. Send it any message
3. It replies with your chat ID -- looks like `123456789`

**Supabase database URL:**
1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click "New Project", give it any name, set a database password (save it somewhere)
3. Wait ~2 minutes for the project to set up
4. Go to: Project Settings (gear icon) > Database > Connection string > URI
5. Copy the full string -- looks like `postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres`

**Step 3 -- Open .env and fill in your values:**

Open the `.env` file in any text editor (Notepad works fine) and replace the placeholder values:

```
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
TELEGRAM_BOT_TOKEN=7123456789:YOUR_TOKEN_HERE
ESCALATION_CHAT_ID=YOUR_CHAT_ID_HERE
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
```

Save the file.

> **Note:** Never share your `.env` file or upload it to GitHub. It contains secret keys.

---

## Customizing for your business

### Step 1 -- Edit the knowledge base

Open `knowledge-base/kb.md` in any text editor.

Replace the NovaTech Gaming demo content with your actual business information. The agent reads this file on every conversation -- the more specific you are, the better it answers.

**Example for a bakery:**
```markdown
## Store Information
Business name: Sweet Dreams Bakery
Hours: Tuesday-Sunday 7am-6pm, closed Mondays
Location: 456 Oak Street, Vancouver, BC
Phone: +1 604-555-1234

## Products
We sell: sourdough bread, croissants, cakes, cupcakes, custom wedding cakes.
We do NOT sell: gluten-free products, vegan items (coming soon).

## Policies
Custom cake orders require 5 days notice and a 50% deposit.
We do not offer refunds on custom orders once baking has started.
All items are made fresh daily -- no delivery.

## FAQ
Q: Can I order a custom birthday cake?
A: Yes! Visit us in-store or call ahead. We need 5 days notice.

Q: Do you have gluten-free options?
A: Not currently, but we're working on it. Check back soon!
```

**Tips for a great knowledge base:**
- Be specific with hours, prices, and policies
- Write out questions your real customers ask
- If the answer is "no", say so clearly -- the agent won't make things up
- You can add as much content as you want -- the agent reads it all

### Step 2 -- Edit the system prompt

Open `system-prompt.md` in any text editor.

Change `[BUSINESS NAME]` to your actual business name at the top.

Optionally change `[AGENT NAME]` to what you want customers to call the bot (e.g. "Nova", "Max", or just leave it as "Support Assistant").

Everything else in that file controls how the agent behaves. The default settings are good for most businesses -- you don't need to change them unless you want to.

**What you should change:**
- Business name (required)
- Agent name (optional)

**What you can customize:**
- Tone (friendlier, more formal, etc.)
- Escalation conditions (when to hand off to a human)
- What the agent refuses to do

---

## Running the bot

Make sure your virtual environment is active (you see `(venv)` in the terminal).

**Test the agent in your terminal first:**
```bash
python agent.py
```

This lets you chat with the agent directly -- no Telegram needed. Check:
- Does it answer your KB questions correctly?
- Does it escalate when you say "I want to speak to a manager"?
- Does the response say `ESCALATE --` in the right format?

Press `Ctrl+C` to stop.

**Start the Telegram bot:**
```bash
python telegram_bot.py
```

Open Telegram, find your bot (search by the username you gave it), and send it a message. It should respond within a few seconds.

**Start both Telegram + web chat at once:**
```bash
python start.py
```

This starts both the Telegram bot and the web chat server simultaneously. The web chat is at `http://localhost:8001`.

Press `Ctrl+C` to stop both.

---

## Testing with eval.py

Before showing the bot to real customers, run the automated test suite:

```bash
python eval.py
```

This sends 10 test questions to your agent and checks that the answers are correct. It takes about 30 seconds and costs a few cents in OpenAI credits.

**Example output:**
```
============================================================
Support Agent Eval
============================================================

[01] PASS -- Store hours query
     Input:    What time do you open on Saturdays?
     Response: We open at 10 AM on Saturdays...

[02] PASS -- Return policy query
...

============================================================
RESULTS: 10/10 passed (100%)
STATUS:  All tests pass. Agent is ready.
============================================================
Log saved: logs/eval-2026-03-21_11-30.json
```

### What each test checks
- Store hours, return policy, delivery, payments (does the agent know your KB?)
- Trade-in and repair questions (does it give the right yes/no?)
- Off-topic questions (does it NOT make up answers?)
- Rude customers (does it stay professional?)
- Prompt injection attacks (does it refuse to reveal its instructions?)

### Fixing failures

If a test says `FAIL`, it tells you exactly what's missing:
```
[03] FAIL -- Digital gift card delivery time
     MISSING: ['15 minute', '5 minute', 'instant']
```

This means your `kb.md` doesn't clearly state the delivery time. Add it:
```markdown
**Q: How fast are digital codes delivered?**
A: Digital codes are delivered within 5-15 minutes after payment.
```

Then run `python eval.py` again. If it passes, you're done.

### When the bot gives a wrong answer

1. Check `knowledge-base/kb.md` -- is the correct information in there?
2. If not: add it. Be specific and clear.
3. If yes but the answer is still wrong: the system prompt might need adjustment. Open `system-prompt.md` and make the rule clearer.
4. Run `python eval.py` again to confirm the fix.

### Adding your own test cases

The default 10 tests use the NovaTech demo KB. Once you've replaced `kb.md`, add tests for your business:

```python
{
    "description": "Custom cake order",
    "input": "Can I order a birthday cake?",
    "must_contain": ["yes", "5 day", "deposit", "custom"],
    "must_not_contain": ["i don't know"],
    "match_mode": "any_contain"
},
```

Add as many as you want. More tests = more confidence.

### When to run evals
- After editing `knowledge-base/kb.md`
- After editing `system-prompt.md`
- Before deploying to production
- After switching AI models

---

## Web Widget Setup

The web chat widget is a floating chat bubble that can be added to any website.

**Run the web server:**
```bash
python web_bot.py
```

Visit `http://localhost:8001` to see the demo page with the chat widget.

**Adding the widget to your existing website:**

You need three pieces from `static/index.html`:
1. The `<style>` block (the CSS that styles the chat bubble)
2. The chat `<div>` elements (the HTML structure)
3. The `<script>` block (the JavaScript that makes it work)

Copy all three into your website's HTML. Then update the fetch URL in the script to point to where your `web_bot.py` is hosted:

```javascript
// Change this line in the script:
const res = await fetch('/chat', { ... })

// To your actual server URL:
const res = await fetch('https://api.yoursite.com/chat', { ... })
```

**Or use Claude Code to do it automatically:**
```
I have a website at [YOUR FOLDER / URL]. Add the support chat widget from web_bot.py
and static/index.html to my existing site. Keep the agent backend the same --
just integrate the chat bubble into my pages and point the fetch URL to [YOUR API URL].
```

---

## Meta / WhatsApp Setup (advanced)

WhatsApp, Instagram DMs, and Facebook Messenger all use the same Meta Cloud API. Setup requires a publicly accessible HTTPS URL -- you need to deploy your server before configuring Meta.

### What you need

| What | Cost | Link |
|------|------|------|
| Meta Business Account | Free | [business.facebook.com](https://business.facebook.com) |
| Meta Developer App | Free | [developers.facebook.com](https://developers.facebook.com) |
| Deployed server with HTTPS | ~$5/mo | Railway or DigitalOcean |

### Which channels need App Review?

| Channel | Needs Review? |
|---------|--------------|
| WhatsApp (test numbers only) | No -- works immediately |
| WhatsApp (real customers) | Yes -- submit to Meta |
| Facebook Messenger | Yes |
| Instagram DMs | Yes |

For testing/demo purposes, WhatsApp test mode works instantly with no review.

### Setup steps

**Step 1 -- Add to your .env:**
```
WHATSAPP_TOKEN=your_permanent_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
META_VERIFY_TOKEN=any_secret_string_you_choose
```

**Step 2 -- Deploy meta_bot.py** to Railway or DigitalOcean (see [Going to production](#going-to-production)).

**Step 3 -- Set your webhook in Meta dashboard:**
1. Go to [developers.facebook.com](https://developers.facebook.com) → Your App → Webhooks
2. Set URL to: `https://yourdomain.com/webhook`
3. Set Verify Token to match your `META_VERIFY_TOKEN`
4. Subscribe to: `messages`

**Step 4 -- Run it:**
```bash
python meta_bot.py
```

This runs on port 8002.

---

## Going to production

"Production" means your bot runs 24/7 on a server, not just on your laptop.

### Option 1 -- Railway (easiest, recommended)

1. Push your code to a **private** GitHub repo. Never commit your `.env` file.
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Add your environment variables in Railway's dashboard (Settings → Variables) -- same values as your `.env`
5. Set the start command to: `python telegram_bot.py`
6. Deploy. Railway keeps it running and restarts automatically if it crashes.

**Cost:** ~$5/mo on the Starter plan.

### Option 2 -- DigitalOcean Droplet

1. Create a $6/mo Ubuntu droplet at [digitalocean.com](https://digitalocean.com)
2. SSH into it:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
3. Install Python:
   ```bash
   apt update && apt install python3-pip python3-venv -y
   ```
4. Clone your repo and install dependencies:
   ```bash
   git clone https://github.com/YOUR_USERNAME/your-bot-repo
   cd your-bot-repo
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Create your `.env` file on the server with your real keys
6. Run with screen (stays running after you disconnect):
   ```bash
   screen -S bot
   python telegram_bot.py
   ```
   Press `Ctrl+A` then `D` to detach.
   
   To check on it later:
   ```bash
   screen -r bot
   ```

**Cost:** $6/mo.

### Auto-start on Windows (for running on a Windows PC)

If you're running the bot on your own Windows PC instead of a server:

1. Press `Win + R`, type `shell:startup`, hit Enter
2. Create a new file called `start-agent.bat` with this content:
   ```bat
   @echo off
   cd "C:\path\to\support-agent-template"
   call venv\Scripts\activate
   python start.py
   ```
3. Replace `C:\path\to\support-agent-template` with your actual folder path
4. Save it. Windows will run this automatically every time you log in.

### Auto-start on Mac/Linux

Add a cron job:
```bash
crontab -e
```
Add this line:
```
@reboot cd /path/to/support-agent-template && source venv/bin/activate && python start.py
```

---

## Troubleshooting

### Bot isn't responding on Telegram
1. Check that `TELEGRAM_BOT_TOKEN` is correct in `.env`
2. Make sure the bot process is actually running: `python telegram_bot.py` in terminal
3. Try sending `/start` to the bot in Telegram
4. Check the terminal for error messages -- they tell you exactly what's wrong

### Bot is giving wrong answers
1. Open `knowledge-base/kb.md` -- is the correct info there?
2. If not: add it. Be specific.
3. Run `python eval.py` to check which tests fail -- they tell you what's missing
4. If the info IS in kb.md but the answer is still wrong: open `system-prompt.md` and add a more explicit rule
5. If you changed models (`OPENAI_MODEL` in `.env`), some models need more explicit prompting

### Escalation alerts not arriving
1. Check that `ESCALATION_CHAT_ID` in `.env` is YOUR personal chat ID (not the bot's ID)
2. Get the correct ID by messaging `@userinfobot` on Telegram
3. Make sure you've messaged the bot at least once (Telegram requires you to initiate)
4. Check the terminal for "Failed to send escalation alert" error messages

### Memory not persisting (bot forgets previous messages)
1. Check that `DATABASE_URL` is set correctly in `.env`
2. If `DATABASE_URL` is blank: the bot uses in-memory storage -- conversations reset on restart. This is expected behavior.
3. If you have a `DATABASE_URL` but memory still resets: check Supabase → Table Editor to see if the `message_store` table exists. Run the bot once and it should create it automatically.
4. Check that your Supabase project is active (free projects pause after 1 week of inactivity)

### pip install fails
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
If that still fails, try:
```bash
pip install -r requirements.txt --ignore-requires-python
```

### "ModuleNotFoundError" when running the bot
Your virtual environment isn't active. Run:
```bash
# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```
Then try again.

### Bot keeps escalating everything
Your `system-prompt.md` escalation rules might be too broad. Open it and check the "When to Escalate" section. Make sure normal questions aren't accidentally matching the escalation conditions.

### How to improve over time

Every `python eval.py` run saves a JSON log to the `logs/` folder. Review these to see which questions the agent struggles with. For each failure:
1. Add the missing info to `kb.md`
2. Add a test case for it in `eval.py` so it never regresses
3. Re-run eval to confirm it passes

Over time, your eval score will reach and stay at 100%.

---

## Rate limiting

The bot limits each user to **10 messages per minute** by default. This prevents abuse and protects your OpenAI bill.

To change the limit, edit your `.env`:
```
RATE_LIMIT_PER_MINUTE=20   # increase for busy businesses
RATE_LIMIT_PER_MINUTE=5    # decrease for stricter control
```

Users who hit the limit get: *"You're sending messages too fast. Please wait a moment and try again."*

---

## How the code works

You don't need to understand this to use the template. But it helps if you want to customize further.

### The 3-file architecture

```
agent.py              <- the brain (LangChain, memory, LLM)
telegram_bot.py       <- the Telegram channel
web_bot.py            <- the website channel
system-prompt.md      <- the personality (rules, tone, escalation triggers)
knowledge-base/kb.md  <- the knowledge (hours, products, policies, FAQs)
```

### How agent.py works

Every time a customer sends a message:

```
Customer message
      |
get_memory(session_id)      <- loads this user's conversation history from Postgres
      |
ChatPromptTemplate           <- assembles: [system prompt + KB] + [history] + [new message]
      |
LLM (OpenAI or Anthropic)   <- generates a response
      |
RunnableWithMessageHistory   <- saves the new message pair back to Postgres
      |
response string
```

The `session_id` is the key to memory. It's `"telegram:USER_ID"` -- unique per Telegram account. Two different customers never share memory.

### How escalation works

When the agent can't help (or a customer requests a human), it responds with:
```
ESCALATE -- [reason]
```

The bot code checks for this with:
```python
if response.upper().startswith("ESCALATE"):
```

If it matches, the bot sends a warm handoff message to the customer AND an alert to you on Telegram. The alert includes a deep link to open a direct chat with the customer.

### Swapping AI models

All model configuration is in `.env`. To switch from OpenAI to Anthropic:
1. Set `MODEL_PROVIDER=anthropic` in `.env`
2. Set `ANTHROPIC_API_KEY=your_key` in `.env`
3. Restart the bot

No code changes needed.

---

## Getting help

- Something broken? Open the terminal and look at the error message -- it usually says exactly what's wrong.
- Still stuck? Open an issue on GitHub.
- Want this set up and customised for your business: [ailevelup.ca](https://ailevelup.ca)

Built by [@TruePrav](https://twitter.com/trueprav)
