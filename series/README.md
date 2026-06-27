# Series Config Files

Series configs define a planned sequence of newsletters that build on each other. The agent (Claude Code) reads these files to know which part to run next, what topic and search queries to use, and which context file to pass to the synthesis step.

**No script reads these files automatically.** They are agent-readable instructions, not machine-executable config.

---

## How the agent uses a series config

When you say "Run the next part from `series/my-series.json`", the agent:

1. Reads the series JSON and finds the first part with `"status": "pending"`
2. Uses the `topic` string for `search_topic.py` and `synthesize_newsletter.py`
3. Tries `search_queries[0]` first — falls back to `search_queries[1]` if results are thin (< 4 good articles)
4. Passes `context_file` to `synthesize_newsletter.py` via the `--context` flag
5. Runs the full pipeline (search → scrape → synthesize → chart → SVG → render → send)
6. After sending, updates the part: `status → "sent"`, fills `subject_line_chosen` and `sent_date`

---

## JSON schema

```json
{
  "series_name": "Human-readable series name",
  "description": "One sentence describing who this series is for and what it covers.",
  "parts": [
    {
      "part_number": 0,
      "title": "Short descriptive title for this part",
      "topic": "The topic string passed to search and synthesis — write it as a full phrase, not just keywords",
      "search_queries": [
        "Primary search query — most specific",
        "Fallback search query — broader, used if primary yields thin results"
      ],
      "context_file": "context/path-to-context-file.md",
      "variant": "long-form",
      "status": "pending",
      "subject_line_chosen": null,
      "sent_date": null
    }
  ]
}
```

### Field reference

| Field | Type | Description |
|-------|------|-------------|
| `series_name` | string | Display name for the series |
| `description` | string | One-sentence summary — audience and scope |
| `part_number` | integer | 0-indexed. Part 0 is typically the overview/intro |
| `title` | string | Short label used by the agent to identify parts |
| `topic` | string | Passed verbatim to `search_topic.py` and `synthesize_newsletter.py` |
| `search_queries` | array | Ordered list — agent tries index 0 first, falls back to index 1 |
| `context_file` | string | Relative path from project root to the context markdown file |
| `variant` | string | `long-form`, `quick-digest`, or `data-heavy` |
| `status` | string | `pending` → `sent` after the part is sent |
| `subject_line_chosen` | string\|null | Fill in after choosing a subject line at send time |
| `sent_date` | string\|null | ISO date (YYYY-MM-DD) filled after sending |

---

## Copy-paste template for a new series

```json
{
  "series_name": "Your Series Name",
  "description": "One sentence: who is this for and what does it cover.",
  "parts": [
    {
      "part_number": 0,
      "title": "Overview — Setting the Stage",
      "topic": "Full topic phrase for the intro part",
      "search_queries": [
        "specific search query",
        "broader fallback query"
      ],
      "context_file": "context/your-series-overview.md",
      "variant": "long-form",
      "status": "pending",
      "subject_line_chosen": null,
      "sent_date": null
    },
    {
      "part_number": 1,
      "title": "First Deep-Dive Topic",
      "topic": "Full topic phrase for part 1",
      "search_queries": [
        "specific search query",
        "broader fallback query"
      ],
      "context_file": "context/your-series-part-1.md",
      "variant": "long-form",
      "status": "pending",
      "subject_line_chosen": null,
      "sent_date": null
    }
  ]
}
```

---

## Naming convention

Use descriptive kebab-case filenames that reflect the series topic:
```
[series-slug].json
```
Examples: `engineering-leadership-ai.json`, `saas-growth-playbook.json`

## Files in this directory

Campaign series configs are gitignored — they live here on disk but are not committed.
Use `_template.json` as your starting point for every new series.
