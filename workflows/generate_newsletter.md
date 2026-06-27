# Generate Newsletter

## Objective
Given a topic, research it on the web, synthesize the findings into a structured newsletter, render an email-safe HTML file with embedded infographics, and send it to active subscribers via Gmail. Zero cost beyond the free tiers of Tavily, Gemini Flash, and Imagen.

## Inputs
- `TOPIC` — short phrase describing the newsletter subject (e.g. "AI in healthcare 2025")
- `--variant` (optional) — `long-form` (default), `quick-digest`, or `data-heavy`
- `--no-images` (optional flag) — skip Imagen hero image generation (use when near the ~50/month free limit)

Required `.env` keys:
- `TAVILY_API_KEY` or `BRAVE_API_KEY` — at least one must be set
- `GOOGLE_AI_API_KEY` — for Gemini Flash synthesis and Imagen images
- `GOOGLE_SHEETS_SUBSCRIBER_ID` — Google Sheet containing subscriber list
- Google OAuth: `credentials.json` must exist in project root (first run opens a browser for auth)

## Tools
In order:
0. `tools/archive_run.py`
1. `tools/cache_research.py`
2. `tools/search_topic.py`
3. `tools/scrape_articles.py`
4. `tools/synthesize_newsletter.py`
5. `tools/generate_chart.py`
6. `tools/generate_svg_graphics.py`
7. `tools/generate_image.py` (conditional)
8. `tools/render_newsletter.py`
9. `tools/send_via_gmail.py`

## Steps

**0. Check for existing run and offer to archive**
```
python tools/archive_run.py check
```
- Prints `NO_CURRENT_RUN` → no previous output exists. Continue to Step 1.
- Prints `CURRENT_RUN_EXISTS` → there is a previous newsletter in `.tmp/output/`. **Stop and ask the user** whether to archive it before proceeding.
  - If yes: ask for the topic and subject line of the previous run (or read from `.tmp/newsletter_content.json`), then run:
    ```
    python tools/archive_run.py archive --topic "previous topic" --subject "chosen subject line"
    ```
  - If no: proceed without archiving (previous output will be overwritten).

**1. Check research cache**
```
python tools/cache_research.py --check "$TOPIC"
```
- Exit code 0 → cache hit. The path to cached articles is printed. Skip to Step 5.
- Exit code 1 → cache miss. Continue to Step 2.

**2. Search for articles**
```
python tools/search_topic.py "$TOPIC"
```
Output: `.tmp/search_results.json` — up to 8 results with title, URL, content snippet, and relevance score.

Tavily is tried first; Brave Search is the automatic fallback if Tavily fails or rate-limits. If both fail, check your API keys in `.env`.

**3. Scrape full article text**
```
python tools/scrape_articles.py .tmp/search_results.json
```
Output: `.tmp/scraped_articles.json` — articles with full text. Tavily results with ≥300 words are used directly without scraping. For shorter results, the full page is fetched and cleaned. Paywalled pages (< 100 words extracted) are skipped automatically.

**4. Write research to cache**
```
python tools/cache_research.py --write "$TOPIC" .tmp/scraped_articles.json
```
Future runs of the same topic within 24 hours skip steps 2–3.

**5. Synthesize newsletter content**
```
python tools/synthesize_newsletter.py "$TOPIC" .tmp/scraped_articles.json --variant long-form
```
Output: `.tmp/newsletter_content.json` containing subject lines (3 variants), preheader, intro, sections (with optional data_points), takeaways, sources, and an image prompt.

For series newsletters or any newsletter needing custom editorial direction, pass a context file:
```
python tools/synthesize_newsletter.py "$TOPIC" .tmp/scraped_articles.json \
  --variant long-form \
  --context context/my-context.md
```
The `--context` flag is optional. When omitted, the pipeline behaves exactly as before. See `context/README.md` for how to write context files.

Uses Gemini 2.5 Flash (free tier: 1,500 requests/day). Retries once if JSON output is malformed.

**6. Generate data chart**
```
python tools/generate_chart.py .tmp/newsletter_content.json
```
Output: `.tmp/chart.png` (if numeric data_points exist in any section) or prints `NO_DATA` and exits 0.

Note the output: if `NO_DATA`, omit `--chart` from the render step.

**7. Generate SVG graphics**
```
python tools/generate_svg_graphics.py "$TOPIC" --title "$SUBJECT_LINE"
```
Output: `.tmp/svg_elements.json` — header banner, divider, and badge SVGs auto-themed by topic category.

`$TOPIC` is used for theme detection only. `--title` sets the text displayed in the header banner — use the chosen subject line so the banner matches what the reader sees in their inbox. If `--title` is omitted, the topic string is used as a fallback (previous behavior).

**8. Generate hero image (unless --no-images)**
```
python tools/generate_image.py .tmp/newsletter_content.json
```
Output: `.tmp/hero_image.png` — thematic illustration via Gemini image generation (`gemini-3.1-flash-image`).

Check the usage warning. If the script prints that the monthly free limit (~50/month) is reached, it exits cleanly without generating an image. Omit `--hero` from the render step in that case.

Skip this step entirely if `--no-images` was specified.

**9. Render HTML and plain text**
```
python tools/render_newsletter.py .tmp/newsletter_content.json \
  --chart .tmp/chart.png \
  --hero .tmp/hero_image.png \
  --svg .tmp/svg_elements.json \
  --variant long-form
```
Omit `--chart` if step 6 returned `NO_DATA`. Omit `--hero` if step 8 was skipped.

Output:
- `.tmp/output/newsletter.html` — email-safe HTML with all images base64-embedded and CSS inlined
- `.tmp/output/newsletter_plain.txt` — plain text fallback

**10. Choose subject line and send**
Read the three subject line options from `.tmp/newsletter_content.json` (or shown in the synthesis step output). Choose one, then:

```
python tools/send_via_gmail.py \
  .tmp/output/newsletter.html \
  .tmp/output/newsletter_plain.txt \
  "Your chosen subject line here"
```

First run: a browser window opens for Google OAuth. Approve access for Gmail, Sheets. The token is saved to `token.json` for future runs.

Use `--dry-run` to preview the subscriber list without sending:
```
python tools/send_via_gmail.py ... --dry-run
```

## Outputs
- Email delivered to all active subscribers in the Google Sheet
- `.tmp/output/newsletter.html` — local copy for reference (disposable, regenerate any time)

## Edge Cases & Gotchas

**Tavily rate limit (429):** The script retries once automatically, then falls back to Brave Search. If both fail, your monthly free quota may be exhausted. Check your usage at tavily.com dashboard.

**Paywalled articles:** Any page returning < 100 words after scraping is skipped silently. The newsletter is generated from whatever content remains. If too many articles are paywalled, add more sources by increasing `--num-results` in the search step.

**Gemini JSON parse failure:** The synthesis script retries once with a stricter JSON-only instruction prepended. If it fails twice, inspect `.tmp/` for any partial output and rerun manually. Rarely happens with Gemini 2.0 Flash.

**Large topic, too much text:** Each article is truncated to 1,500 words before being sent to Gemini. The highest word-count articles are prioritized. If the topic is very broad, the newsletter may be shallower — consider narrowing the topic string.

**NO_DATA from generate_chart.py:** Normal behavior when the topic is qualitative (no stats/percentages). The newsletter renders cleanly without a chart. Omit `--chart` from the render command.

**Imagen monthly limit reached:** `generate_image.py` exits 0 with a warning and no file written. Omit `--hero` from the render step. The newsletter still looks good with the SVG header banner alone.

**Google OAuth browser flow:** Only happens on first run or when `token.json` expires (~7 days for refresh tokens in certain Google Cloud configurations). If you're running this headlessly, pre-generate `token.json` on a machine with a browser first.

**Gmail sending to many subscribers:** Gmail API allows ~500 recipients/day for free accounts. The script adds a 0.3-second delay between sends to stay within rate limits. For larger lists, consider batching runs across multiple days or upgrading to Google Workspace.

**Subscriber list format:** Column A = email, Column B = name, Column C = "active" or "unsubscribed". Row 1 is the header (skipped). Add new subscribers by appending rows with `active` in column C.

**CSS inlining:** If `css-inline` is not installed, styles won't be inlined and some email clients (Gmail web) will strip them. Run `pip install css-inline` to fix. It's in `requirements.txt` — this only happens if you skipped `pip install -r requirements.txt`.

## Series Newsletters

The `series/` directory contains JSON configs for planned newsletter series. The `context/` directory contains the editorial guidance files they reference.

### Directory structure
```
series/
  README.md                   # Schema reference and copy-paste template
  _template.json              # Blank series config to duplicate for new series
  <your-series-name>.json     # Campaign-specific — gitignored; create per series

context/
  README.md                   # Usage guide and copy-paste template for context files
  _template.md                # Blank context file to duplicate for new parts
  <your-context-file>.md      # Campaign-specific — gitignored; create per part
```

### How to run a series part

1. Read the series JSON — find the first part with `"status": "pending"`.
2. Run the standard pipeline (Steps 0–4) using the `topic` field from the config.
   - If Step 2 (search) yields fewer than 4 real articles, retry with `search_queries[1]`.
3. Run synthesis with the context file:
   ```
   python tools/synthesize_newsletter.py "<topic>" .tmp/scraped_articles.json \
     --variant long-form \
     --context <context_file from config>
   ```
4. Continue with Steps 6–10 (chart, SVG, image, render, send) as normal.
5. After sending, update the series JSON for that part:
   - `"status"` → `"sent"`
   - `"subject_line_chosen"` → the chosen subject line
   - `"sent_date"` → today's date (YYYY-MM-DD)

### Design intent
Series configs and context files are read by the agent (Claude Code), not by any script.
This keeps the pipeline tools generic and the series logic in human-readable files that are easy to edit before each send.
