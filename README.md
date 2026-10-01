# Research Agent

Type a question. The agent searches Google, picks the best pages, reads them,
and writes you a short report with numbered sources. One run takes about two
minutes and costs about 15 cents.

```
python research_agent.py "n8n vs Make vs Zapier in 2026: which skill are clients hiring for?"
```

See a real report it wrote: [examples/n8n-vs-make-vs-zapier-2026.md](examples/n8n-vs-make-vs-zapier-2026.md)

## Why I built it

Before a client call or a proposal, I research the client's industry, their
tools, and what the market pays. Doing that by hand means opening a dozen tabs
and copying notes. This does the first pass for me, and it shows where every
claim came from so I can check it.

It was also my way to learn LangChain properly, by building something I use
instead of following a tutorial.

## How it works

```
Your question
     |
     v
 Claude (the "brain") decides what to do next
     |                         ^
     |  "search for X"         |  results come back
     |  "read this page"       |
     v                         |
 Decodo (the "hands") fetches Google results and web pages
     |
     v
 Claude writes the report  ->  saved in reports/
```

Claude does not follow a fixed script. It looks at the search results, chooses
which pages are worth reading, and searches again if the first results are
weak. This back-and-forth loop is what people mean by an "AI agent".

**The tools:**
- **LangChain** connects Claude to the tools and runs the loop.
- **Decodo** fetches web pages for me. It gets past blocks and captchas that stop normal scripts.
- **Claude** (Sonnet), reached through OpenRouter, reads the pages and writes the report.

## Things I had to solve

- **The official tool sent back clutter.** Decodo's own LangChain package returns
  the raw page code (HTML). One Google results page is about a megabyte of it,
  which fills Claude's memory and costs far more. I wrote two small tools that
  ask Decodo for clean results instead: a tidy list of search results, and pages
  as plain text with images and link addresses removed.
- **Spending caps.** Each run is limited to 3 searches and 5 page reads, so a
  confused agent cannot burn through credits. You can change both in `.env`.
- **Trust.** Claude is told to cite only pages it actually read, to prefer
  official sources, and to say when sources disagree. In the example report, it
  caught a comparison article with wrong facts and left it out of its findings.

## Cost per run

| Part | Typical use | Cost |
|---|---|---|
| Decodo | 3 searches and 5 pages | about 1 cent |
| Claude Sonnet | reads about 55,000 tokens (small chunks of text), writes about 3,000 | about 14 cents |

## Set it up

You need Python 3.11 or newer, a [Decodo](https://decodo.com) Web Scraping API
plan, and an [OpenRouter](https://openrouter.ai) key.

```
python -m venv .venv
.venv\Scripts\activate          (Mac or Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          (Mac or Linux: cp .env.example .env)
```

Open `.env` and paste in your two keys. The Decodo one is on the dashboard
under **Web Scraping API > API Authentication**. Then run:

```
python research_agent.py "your question here"
```

Reports are saved in the `reports/` folder.

## Built by

Ema, AI automation and data operations specialist.
[emayourvirtualassistant.com](https://emayourvirtualassistant.com)
