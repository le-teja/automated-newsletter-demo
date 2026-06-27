# Context Files

Context files let you inject editorial guidance into the newsletter synthesis step. They're passed to `tools/synthesize_newsletter.py` via the `--context` flag and inserted directly into the Gemini prompt, between the output schema rules and the research articles.

Use them to control tone, specificity, series framing, required tools or links, and anything else that the topic string alone can't capture.

---

## When to use a context file

| Situation | What to put in the context file |
|-----------|--------------------------------|
| Series newsletter | Series name, part number, what previous parts covered, how to reference them |
| Opinionated deep-dive | Specific tools to name, real links to include, "be opinionated, no hedging" |
| Audience-specific | Role (CTO vs IC), assumed knowledge level, what to skip |
| Tone change | "Lead with a stat", "use a cautionary tone", "write for a skeptical reader" |
| Topic constraints | What NOT to cover, which angles to avoid, word count guidance |

---

## Standard sections

A context file is plain markdown. Use any subset of these four sections:

```markdown
## Series framing
[Where this sits in a series. What prior parts covered. How to reference them.]

## Tone and specificity
[Voice, level of opinion, how to handle hedging, link inclusion requirements.]

## Required coverage
[Specific tools, frameworks, concepts, or data points that must appear.]

## What to avoid
[Topics, phrases, or approaches to exclude.]
```

---

## Copy-paste template

```markdown
## Series framing
This newsletter stands alone / is Part #N in the "[Series Name]" series.
[If part of a series: "The previous part covered X (subject line: 'Y'). Reference it once in the intro, then move on."]

## Tone and specificity
- Be opinionated. Take clear positions. Don't hedge with "consider" or "you might want to."
- Name real tools by name. Include real GitHub or docs links where they exist.
- Every section should end with one concrete action the reader can take this week.
- Audience: [Software Engineering Managers / Staff Engineers / CTOs / ICs]

## Required coverage
- [Tool or concept 1]
- [Tool or concept 2]
- [Specific angle or question to answer]

## What to avoid
- Generic advice that applies to any topic
- Marketing copy or framework comparisons without engineering substance
- Vague takeaways — end with verbs, not observations
```

---

## How to invoke

**Standalone newsletter with editorial context:**
> "Generate a newsletter on [topic] using `context/my-context.md`"

**Series part:**
> "Run part #2 from `series/my-series.json`"
(The agent reads the series config, finds the `context_file` field, and passes it automatically.)

**Manual CLI:**
```bash
python tools/synthesize_newsletter.py "Your topic here" .tmp/scraped_articles.json \
  --variant long-form \
  --context context/my-context.md
```

---

## Naming convention

Use descriptive kebab-case filenames that reflect the series and part:
```
[series-slug]-[part-slug].md
```
Examples: `eng-leadership-overview.md`, `saas-metrics-part-3-churn.md`

## Files in this directory

Campaign-specific context files are gitignored — they live here on disk but are not committed.
Use `_template.md` as your starting point for every new context file.
