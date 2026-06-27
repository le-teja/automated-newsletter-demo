# Workflow Conventions

Workflows are Markdown SOPs that tell the agent what to do and how. They are the authoritative instructions — don't overwrite them without user approval.

## Naming

`verb_noun.md` — lowercase, underscores, imperative verb first.

Examples: `scrape_newsletter.md`, `summarize_articles.md`, `publish_to_sheets.md`

## Required Sections

Every workflow must have all of these:

```
# Workflow Name

## Objective
One sentence. What does this workflow accomplish and why?

## Inputs
What the agent needs before starting. Be specific (URL, sheet ID, date range, etc.).

## Tools
Which scripts in `tools/` are used and in what order.

## Steps
Numbered, sequential instructions. Each step should map to a tool call or a decision point.

## Outputs
What gets produced and where it goes (always a cloud destination).

## Edge Cases & Gotchas
Known failure modes, rate limits, timing quirks, and how to handle them.
```

## Guidelines

- Write steps as if briefing a smart colleague, not a machine. Plain language.
- Each step should do one thing. If a step has an "and", consider splitting it.
- When a tool fails and you learn something new, add it to **Edge Cases & Gotchas** immediately.
- If a better method is discovered, update the Steps section — workflows evolve.
- Don't add steps for things the tool already handles internally.
