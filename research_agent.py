"""Research agent.

Give it a topic. It searches Google, reads the most useful pages, and writes a
short report with numbered sources.

Built with LangChain. Decodo fetches the web pages (it gets past blocks and
captchas), and Claude, reached through OpenRouter, decides what to read and
writes the report.

Run:  python research_agent.py "your topic here"
"""
import datetime as dt
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()

DECODO_URL = "https://scraper-api.decodo.com/v2/scrape"
MODEL = os.getenv("MODEL", "anthropic/claude-sonnet-5.5")
MAX_SEARCHES = int(os.getenv("MAX_SEARCHES", "3"))  # spending cap per run
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))        # spending cap per run
PAGE_CHARS = 8000  # how much of each page Claude gets to read

usage = {"searches": 0, "pages": 0}


def decodo(payload: dict) -> dict:
    """Send one request to Decodo and return the first result."""
    token = os.getenv("DECODO_API_TOKEN", "").strip()
    if not token:
        sys.exit("DECODO_API_TOKEN is missing. Copy .env.example to .env and fill it in.")
    token = token.removeprefix("Basic ").strip()  # works whether or not "Basic " was pasted too
    r = httpx.post(DECODO_URL, json=payload, headers={"Authorization": f"Basic {token}"}, timeout=180)
    r.raise_for_status()
    return r.json()["results"][0]


def tidy(markdown: str) -> str:
    """Strip images and link addresses so Claude reads words, not clutter."""
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", markdown)      # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links: keep the words only
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


# Why not the official langchain-decodo tools? They hand back the raw page code
# (HTML), so a single Google results page fills Claude's memory with clutter and
# costs far more. These two ask Decodo for clean results instead.

@tool
def search_google(query: str) -> str:
    """Search Google. Returns the top results as a numbered list with title,
    link and a short snippet. Use this first to find pages worth reading."""
    if usage["searches"] >= MAX_SEARCHES:
        return "Search limit reached for this run. Work with the results you already have."
    usage["searches"] += 1
    try:
        res = decodo({"target": "google_search", "query": query, "parse": True})
        organic = res["content"]["results"]["results"].get("organic", [])
    except Exception as e:
        return f"Search failed ({e}). Try a different wording."
    if not organic:
        return "No results. Try a shorter or different search."
    return "\n".join(f"{i}. {o.get('title', '')}\n   {o.get('url', '')}\n   {o.get('desc', '')}"
                     for i, o in enumerate(organic[:10], 1))


@tool
def read_page(url: str) -> str:
    """Open a web page and return its main text (cut to about 8,000 characters).
    Use it on the 3 to 5 most useful search results."""
    if usage["pages"] >= MAX_PAGES:
        return "Page limit reached for this run. Write the report with what you have read."
    usage["pages"] += 1
    try:
        res = decodo({"target": "universal", "url": url, "markdown": True})
    except Exception as e:
        return f"Could not open this page ({e}). Pick another result."
    text = tidy(res.get("content") or "")
    if (res.get("status_code") or 200) >= 400 or len(text) < 200:
        return f"This page was empty or blocked (status {res.get('status_code')}). Pick another result."
    return text[:PAGE_CHARS]


SYSTEM_PROMPT = f"""You are a careful research assistant. Today is {dt.date.today():%B %d, %Y}.

How to work:
1. Search Google (1 to {MAX_SEARCHES} searches). Add the current year to the search when freshness matters.
2. Read the {min(3, MAX_PAGES)} to {MAX_PAGES} most useful pages. Prefer official docs and original sources over list articles and ads.
3. Write the report.

Report format (Markdown):
# <short title>
**In short:** two or three sentences that answer the question.
## Key findings
Bullet points. End each one with the source number, like [1].
## What to do with this
Two to four practical next steps.
## Sources
Numbered list: page title, then the link.

Rules: only cite pages you actually read. If sources disagree, say so. Use plain English and short sentences.
Never use em dashes."""


def main() -> None:
    topic = " ".join(sys.argv[1:]).strip() or input("What should I research? ").strip()
    if not topic:
        sys.exit("No topic given.")
    if not os.getenv("OPENROUTER_API_KEY"):
        sys.exit("OPENROUTER_API_KEY is missing. Copy .env.example to .env and fill it in.")

    model = ChatOpenAI(model=MODEL, base_url="https://openrouter.ai/api/v1",
                       api_key=os.getenv("OPENROUTER_API_KEY"), temperature=0.2)
    agent = create_agent(model, tools=[search_google, read_page], system_prompt=SYSTEM_PROMPT)

    print(f"Researching: {topic}\n")
    report, tokens_in, tokens_out = "", 0, 0
    # The agent loops: Claude picks a tool, the tool runs, Claude reads the answer,
    # and so on until Claude writes the report. Print each step as it happens.
    for update in agent.stream({"messages": [{"role": "user", "content": topic}]},
                               {"recursion_limit": 30}, stream_mode="updates"):
        for step in update.values():
            for msg in (step or {}).get("messages", []):
                if msg.type != "ai":
                    continue
                meta = getattr(msg, "usage_metadata", None) or {}
                tokens_in += meta.get("input_tokens", 0)
                tokens_out += meta.get("output_tokens", 0)
                for call in msg.tool_calls:
                    label = "Searching" if call["name"] == "search_google" else "Reading"
                    print(f"  {label}: {next(iter(call['args'].values()), '')}")
                if not msg.tool_calls and msg.content:
                    report = msg.content if isinstance(msg.content, str) else "".join(
                        part.get("text", "") for part in msg.content if isinstance(part, dict))

    if not report:
        sys.exit("The agent finished without writing a report. Try again or reword the topic.")
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:60]
    out = Path(__file__).parent / "reports" / f"{dt.date.today()}-{slug}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")

    print(f"\n{report}\n")
    print(f"Saved to {out}")
    print(f"Decodo: {usage['searches']} searches + {usage['pages']} pages read = "
          f"{usage['searches'] + usage['pages']} requests")
    print(f"Claude ({MODEL}): {tokens_in:,} tokens in, {tokens_out:,} tokens out")


if __name__ == "__main__":
    main()
