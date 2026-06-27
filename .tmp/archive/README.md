# .tmp/archive/

Archived past newsletter runs, organized by date and topic.

**Structure:** Each archived run is a folder named `YYYY-MM-DD_<topic-slug>/` containing the output files from that run.

```
.tmp/archive/
  2026-06-27_engineering-leadership-overview/
    newsletter.html
    newsletter_plain.txt
  2026-07-04_engineering-leadership-agentic-teams/
    newsletter.html
    newsletter_plain.txt
```

**When to archive:** Before starting a new newsletter run, ask the agent to archive the current output:
> "Archive the current newsletter before starting a new one"

The agent moves `.tmp/output/` contents into a dated archive folder so you don't lose the previous run when the next one overwrites it.

Archives are gitignored but kept locally so you can reference past sends without going to your email.
