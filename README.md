# Research Agent

Type a question. The agent searches Google, picks the best pages, reads them,
and writes you a short report with numbered sources, so you can check where
every claim came from. One run takes about two minutes and costs about 15 cents.

```
python research_agent.py "n8n vs Make vs Zapier in 2026: which skill are clients hiring for?"
```

See a real report it wrote: [examples/n8n-vs-make-vs-zapier-2026.md](examples/n8n-vs-make-vs-zapier-2026.md)

## Why I built it

Before a client call or a proposal, I research the client's industry, their
tools, and what the market pays. Doing that by hand means opening a dozen tabs
and copying notes. This does the first pass for me.

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
 Decodo (the "hands") opens Google and the web pages
     |
     v
 Claude writes the report  ->  saved in the reports folder
```

Claude does not follow a fixed script. It looks at the search results, chooses
which pages are worth reading, and searches again if the first results are
weak. An AI that decides its own next step like this, and uses tools to do it,
is what people mean by an "AI agent".

**What each part is:**
- **Claude** is the AI model (made by Anthropic) that reads the pages and writes the report.
- **LangChain** is a free toolkit for connecting an AI model to tools. It runs the back-and-forth loop shown above.
- **Decodo** is a paid service that opens web pages on my behalf. It gets past the "are you a robot?" checks that block ordinary scripts.
- **OpenRouter** is a service that lets one account use many AI models. I use it to reach Claude.

## Problems I had to solve

- **The ready-made tool sent back clutter.** Decodo offers an official add-on for
  LangChain, but it returns a page's raw code (the HTML behind what you see in a
  browser) instead of its text. One Google results page is about a million
  characters of code, which buries the useful part and costs far more to process.
  I wrote two small tools of my own that ask Decodo for clean results instead: a
  tidy list of search results, and pages as plain text with pictures and links
  stripped out.
- **A spending limit.** Each run can search at most 3 times and read at most 5
  pages, so the agent can never get stuck in a loop and run up a bill. Both
  limits can be changed in the settings file.
- **Trust.** Claude is told to quote only pages it actually read, to prefer
  official sources over ads and list articles, and to say when sources disagree.
  In the example report, it caught a comparison article that had its facts wrong
  and left it out.

## Cost per run

| Part | What it does in one run | Cost |
|---|---|---|
| Decodo | 3 Google searches and 5 pages opened | about 1 cent |
| Claude | reads about 40,000 words of web pages, writes about 2,000 | about 14 cents |

## Try it yourself

You need three things:
- **Python** (version 3.11 or newer), the programming language this is written in. Free from python.org.
- A **Decodo** Web Scraping API plan ([decodo.com](https://decodo.com)), for opening web pages.
- An **OpenRouter** account and key ([openrouter.ai](https://openrouter.ai)), for using Claude.

Then, in a terminal (the command window) inside this folder:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

What those four lines do:
1. Make a private folder (`.venv`) for this project's add-ons, so they don't clash with anything else on your computer.
2. Switch to that private folder. (On Mac or Linux: `source .venv/bin/activate`)
3. Install the add-ons this project needs. The list is in `requirements.txt`.
4. Make your own copy of the settings file. (On Mac or Linux: `cp .env.example .env`)

Open `.env` in any text editor and paste in your two keys. The Decodo key is on
the Decodo dashboard, under **Web Scraping API > API Authentication**. The `.env`
file stays on your computer and is never uploaded to GitHub, so your keys stay private.

Then ask it anything:

```
python research_agent.py "your question here"
```

Each report is saved in the `reports` folder.

## Built by

Ema, AI automation and data operations specialist.
[emayourvirtualassistant.com](https://emayourvirtualassistant.com)
