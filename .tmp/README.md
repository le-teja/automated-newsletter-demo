# .tmp/

Temporary processing directory. All files here are regenerated on each pipeline run and are **not committed to git**.

| Subdirectory | Purpose |
|---|---|
| `output/` | Rendered newsletter files ready to send (HTML + plain text) |
| `archive/` | Past runs organized by date — moved here before starting a new run |
| `cache/` | Research cache — avoids re-scraping the same topic within 24 hours |

**Intermediate files** (written directly into `.tmp/`, not a subdirectory):

| File | Written by | Purpose |
|---|---|---|
| `search_results.json` | `search_topic.py` | Raw search results from Tavily/Brave |
| `scraped_articles.json` | `scrape_articles.py` | Full article text after scraping |
| `newsletter_content.json` | `synthesize_newsletter.py` | Structured newsletter JSON from Gemini |
| `chart.png` / `chart_section_N.png` | `generate_chart.py` | Per-section chart images |
| `chart_map.json` | `generate_chart.py` | Maps section index → chart file path |
| `graphics.json` | `generate_svg_graphics.py` | Header banner and decorative elements |

Everything here is disposable. If you delete `.tmp/`, the next pipeline run recreates it.
