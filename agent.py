"""
Support Agent — LangChain + Telegram
Built by TruePrav / ailevelup.ca

This file is the brain of the agent.
It handles: loading your knowledge base, building the system prompt,
connecting to the LLM, managing memory, and processing messages.
"""

import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

# LangChain imports — the framework that connects everything together
from langchain_openai import ChatOpenAI          # OpenAI model wrapper
from langchain_anthropic import ChatAnthropic    # Anthropic (Claude) model wrapper
from langchain_google_genai import ChatGoogleGenerativeAI  # Google Gemini model wrapper
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_postgres import PostgresChatMessageHistory
import psycopg
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# load_dotenv() reads your .env file and makes all variables available via os.getenv()
load_dotenv()

# Suppress LangSmith tracing warnings — not needed unless you have a LangSmith account
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# Suppress noisy LangSmith auth warnings
logging.getLogger("langsmith").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


# ── Config ───────────────────────────────────────────────────────────────────
# All settings come from .env — nothing is hardcoded here.
# This means you can change model, temperature, memory window without touching code.

MODEL_PROVIDER  = os.getenv("MODEL_PROVIDER", "openai")       # which LLM company to use
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")    # cheap + fast, good for support
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
TEMPERATURE     = float(os.getenv("TEMPERATURE", "0.3"))
# Temperature controls how creative/random the model is.
# 0.0 = fully deterministic (same input → same output every time)
# 1.0 = very creative/random
# 0.3 = slight variation but mostly consistent — ideal for support agents
DATABASE_URL    = os.getenv("DATABASE_URL")                    # Supabase / Postgres URL
MEMORY_WINDOW   = int(os.getenv("MEMORY_WINDOW", "20"))

KB_PATH = Path(__file__).parent / "knowledge-base" / "kb.md"


# ── Knowledge Base ───────────────────────────────────────────────────────────
# The knowledge base (kb.md) is a plain text file with your business info —
# hours, products, policies, FAQs. The agent reads this on every conversation.
# Updating kb.md is how a non-technical business owner "trains" the agent —
# no code changes needed, just edit the markdown file.

def load_kb() -> str:
    """Load the business knowledge base from kb.md."""
    if KB_PATH.exists():
        return KB_PATH.read_text(encoding="utf-8")
    logger.warning("kb.md not found — agent will run without knowledge base")
    return ""


# ── System Prompt ────────────────────────────────────────────────────────────
# The system prompt is the agent's personality and rule set.
# It runs before every single conversation — it's what makes the agent
# act like your business, not a generic chatbot.
#
# It lives in system-prompt.md so non-technical people can edit it
# without touching Python code.
#
# The {{KB_CONTENT}} placeholder gets replaced with the actual kb.md content
# at runtime — so the agent always has your latest business info.

def build_system_prompt() -> str:
    """Build the full system prompt by combining the template with the KB."""
    kb = load_kb()
    system_prompt_path = Path(__file__).parent / "system-prompt.md"

    if system_prompt_path.exists():
        template = system_prompt_path.read_text(encoding="utf-8")
        return template.replace("{{KB_CONTENT}}", kb)

    # Fallback if system-prompt.md is missing
    return f"""You are a helpful customer support assistant.

Answer customer questions clearly and accurately using the knowledge base below.
If you don't know, say so honestly. Never make up information.

If a customer asks to speak to a human or you cannot help them, respond with:
ESCALATE -- [brief reason]

## Knowledge Base
{kb}
"""


# ── LLM (the model) ──────────────────────────────────────────────────────────
# This function returns the actual AI model object.
# Swapping between OpenAI and Anthropic is a one-line change in .env —
# the rest of the code doesn't care which model is running underneath.
# This is called "provider abstraction" — your business logic is decoupled
# from the specific model you're using.

def get_llm():
    """Return the configured language model."""
    if MODEL_PROVIDER == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is missing from your .env file. "
                "Get your key at console.anthropic.com/settings/keys"
            )
        return ChatAnthropic(
            model=ANTHROPIC_MODEL,
            temperature=TEMPERATURE,
            api_key=api_key,
        )
    if MODEL_PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from your .env file. "
                "Get your key at aistudio.google.com/app/apikey"
            )
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=TEMPERATURE,
            google_api_key=api_key,
        )
    # Default: OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing from your .env file. "
            "Get your key at platform.openai.com/api-keys"
        )
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        api_key=api_key,
    )


# ── Memory ───────────────────────────────────────────────────────────────────
# Memory is what makes this a real support agent vs a basic chatbot.
#
# Without memory: every message is a blank slate. Customer says "my PSN code
# isn't working", agent asks for details, customer provides them... next message,
# the agent has no idea what they were talking about.
#
# With Postgres memory: each user gets their own conversation history stored
# in a database. The agent loads the last N messages before every reply,
# so it has full context — even across days or restarts.
#
# session_id is the key — it's unique per user (we use their Telegram ID).
# This means User A and User B have completely separate memory stores.
# The agent never confuses one customer's issue with another's.

def get_memory(session_id: str) -> BaseChatMessageHistory:
    """
    Return the memory store for a specific user session.

    If DATABASE_URL is set: uses Postgres (persistent — survives restarts).
    If not set: uses in-memory storage (resets on restart — fine for testing).
    """
    from langchain_core.chat_history import InMemoryChatMessageHistory

    if DATABASE_URL:
        try:
            # PostgresChatMessageHistory requires a valid UUID for session_id.
            # We derive a deterministic UUID from the session_id string so the
            # same user always gets the same UUID (and thus the same memory).
            session_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id))
            conn = psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=5)
            return PostgresChatMessageHistory(
                "message_store",
                session_uuid,
                sync_connection=conn,
            )
        except Exception as e:
            logger.warning(
                f"Database connection failed — falling back to in-memory storage. "
                f"Error: {e}\n"
                f"Check your DATABASE_URL in .env. "
                f"If using Supabase, use the session pooler URL "
                f"(aws-0-*.pooler.supabase.com:5432), not the direct URL."
            )
            return InMemoryChatMessageHistory()

    # No DATABASE_URL set — in-memory mode (conversations reset on restart)
    return InMemoryChatMessageHistory()


# ── Agent (the full chain) ───────────────────────────────────────────────────
# This is where everything gets assembled into a single runnable chain:
# system prompt → message history → current message → model → response
#
# LangChain's ChatPromptTemplate defines the structure of every request:
# 1. System message (personality + rules + KB)
# 2. History (last N messages from Postgres)
# 3. Human message (what the customer just said)
#
# RunnableWithMessageHistory wraps the chain and handles loading/saving
# memory automatically on every invocation — you don't have to manage it manually.

def build_agent():
    """Assemble the full agent chain with prompt + LLM + memory."""
    # Validate API key up front so users get a clear error at startup,
    # not a confusing hang or cryptic error on the first message.
    try:
        llm = get_llm()
        logger.info(f"LLM ready: provider={MODEL_PROVIDER}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise

    # Create the Postgres table once at startup (no-op if it already exists).
    if DATABASE_URL:
        try:
            with psycopg.connect(DATABASE_URL, autocommit=True, connect_timeout=5) as conn:
                PostgresChatMessageHistory.create_tables(conn, "message_store")
            logger.info("Postgres memory table ready")
        except Exception as e:
            logger.warning(
                f"Could not connect to database at startup — running in in-memory mode. "
                f"Error: {e}"
            )

    system_prompt = build_system_prompt()

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # The prompt template defines what gets sent to the model on every turn:
    # - "system": the agent's instructions (loaded once from system-prompt.md + kb.md)
    # - MessagesPlaceholder: where the conversation history gets inserted
    # - "human": the customer's current message
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),  # injected automatically from DB
        ("human", "{input}"),
    ])

    # The pipe operator (|) chains components: prompt output → LLM input
    chain = prompt | llm

    # RunnableWithMessageHistory adds automatic memory management:
    # before each call: loads history from DB → injects into prompt
    # after each call: saves the new message pair (human + AI) to DB
    agent_with_memory = RunnableWithMessageHistory(
        chain,
        get_session_history=get_memory,    # which memory store to use
        input_messages_key="input",        # which key is the user's message
        history_messages_key="history",    # which key is the history placeholder
    )

    return agent_with_memory


# ── Chat function ────────────────────────────────────────────────────────────
# This is the public API for the agent — one function call, one response.
# telegram_bot.py calls this for every message that comes in.
# The session_id ensures each user gets their own memory context.

_agent = None  # cached so we don't rebuild the chain on every message

def chat(message: str, session_id: str) -> str:
    """
    Process a customer message and return the agent's response.

    Args:
        message: what the customer said
        session_id: unique identifier for this user (e.g. "telegram:123456789")

    Returns:
        The agent's response as a string.
        If it starts with "ESCALATE", the telegram_bot will handle it normally.
    """
    global _agent
    if _agent is None:
        _agent = build_agent()

    try:
        result = _agent.invoke(
            {"input": message},
            # configurable tells RunnableWithMessageHistory which session's memory to load
            config={"configurable": {"session_id": session_id}},
        )
        return result.content
    except Exception as e:
        logger.error(f"Agent error for session {session_id}: {e}")
        return "Sorry, I ran into an issue. Please try again or call us directly."


# ── Local test ───────────────────────────────────────────────────────────────
# Run `python agent.py` to test the agent in your terminal before setting up Telegram.
# This lets you check responses, test escalation, verify the KB is loading correctly.

if __name__ == "__main__":
    import uuid
    print("Agent ready. Type your message (Ctrl+C to quit)\n")
    session = str(uuid.uuid4())  # fresh UUID each test run
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            response = chat(user_input, session)
            print(f"Agent: {response}\n")
        except KeyboardInterrupt:
            print("\nDone.")
            break
