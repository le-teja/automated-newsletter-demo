# Automated Newsletter Platform

An AI-powered newsletter pipeline built on the WAT framework (Workflows, Agents, Tools). You give it a topic — or a series config — and it researches, writes, renders, and sends a polished email newsletter to your subscriber list. Zero cost beyond free API tiers.

---

## How to prompt the system

Talk to Claude Code (the agent) in natural language. Here are the main prompt patterns:

### Standalone newsletter
> "Generate a newsletter on [topic]"

The agent runs the full pipeline: search → scrape → synthesize → chart → SVG → render → send.

> "Generate a newsletter on the state of Rust adoption in backend engineering in 2025"

---

### Standalone with editorial context
> "Generate a newsletter on [topic] using `context/my-context.md`"

Same as above, but the context file injects editorial guidance into the synthesis step — tone, required tools to mention, audience, what to avoid. See `context/README.md` for how to write one.

> "Generate a newsletter on AI agent frameworks using `context/series-deep-dive-1-agentic-teams.md`"

---

### Run a multipart Newsletter
> "Run part #[N] from `series/[series-file].json`"

The agent reads the series config, picks the right topic and context file, and runs the pipeline. After sending, it updates the part status in the JSON.

> "Run part #0 from `series/engineering-leadership-ai.json`"
> "Run the next pending part from `series/engineering-leadership-ai.json`"

---

### Preview / dry run (don't send)
> "Run part #1 from `series/engineering-leadership-ai.json` but don't send — just show me the plain text"
> "Generate a newsletter on [topic] and stop before sending"

The pipeline runs through render. You review `output/newsletter_plain.txt` before committing to send.

---

### Re-render and re-send
> "Re-render the current newsletter and send it"
> "Send the last newsletter with subject line: [your subject line here]"

Skips research and synthesis — re-uses `.tmp/newsletter_content.json` and re-renders. Useful for resending after a layout fix or sending to a newly added subscriber.

---

### Archive the current run
> "Archive the current newsletter before starting a new one"

Moves the current `.tmp/output/` files to a dated archive folder so the next run starts clean.

---

## Directory reference

| Directory / File | Purpose |
|-----------------|---------|
| `workflows/` | Markdown SOPs — step-by-step instructions the agent follows |
| `tools/` | Python scripts that do the actual work (search, scrape, synthesize, render, send) |
| `context/` | Editorial context files — injected into the synthesis prompt via `--context` |
| `series/` | Series config JSONs — define multi-part newsletter sequences |
| `.tmp/` | Temporary processing files — regenerated each run, disposable |
| `.tmp/output/` | The rendered newsletter (HTML + plain text) ready to send |
| `.tmp/archive/` | Archived past runs, organized by date and topic |
| `.tmp/cache/` | Research cache — avoids re-scraping the same topic within 24 hours |
| `.env` | API keys and environment variables — never commit this file |

---

## First-time setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Set API keys in `.env`**
```
TAVILY_API_KEY=...           # Web search (primary). Get free key at tavily.com
BRAVE_API_KEY=...            # Web search (fallback). Get free key at brave.com/search/api
GOOGLE_AI_API_KEY=...        # Gemini synthesis + Imagen images. Get at aistudio.google.com
GOOGLE_SHEETS_SUBSCRIBER_ID= # Google Sheet ID containing your subscriber list
GMAIL_FROM=you@gmail.com     # Your Gmail address (used as sender)
```

**3. Set up Google OAuth (first run only)**

Place `credentials.json` in the project root (download from Google Cloud Console — enable Gmail API and Google Sheets API). On the first run of `send_via_gmail.py`, a browser window opens for OAuth approval. The token is saved to `token.json` for future runs.

**4. Set up your subscriber sheet**

Create a Google Sheet with:
- Column A: email address
- Column B: name
- Column C: `active` or `unsubscribed`
- Row 1: header row (skipped automatically)

Copy the Sheet ID from the URL and set it as `GOOGLE_SHEETS_SUBSCRIBER_ID` in `.env`.

