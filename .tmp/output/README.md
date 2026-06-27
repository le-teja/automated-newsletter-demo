# .tmp/output/

Rendered newsletter files ready to review and send.

| File | Written by | Purpose |
|---|---|---|
| `newsletter.html` | `render_newsletter.py` | Full HTML email with inlined CSS — what subscribers receive |
| `newsletter_plain.txt` | `render_newsletter.py` | Plain text fallback — review this before sending |

**Workflow:** After the pipeline runs through the render step, check `newsletter_plain.txt` to verify content and tone before committing to send. If anything needs to be fixed, re-run just the render step — no need to re-do research or synthesis.

Before starting a new run, archive or clear this folder so outputs don't mix across topics.
