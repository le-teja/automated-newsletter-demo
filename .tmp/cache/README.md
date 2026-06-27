# .tmp/cache/

Research cache — stores scraped article data so the same topic isn't re-scraped within 24 hours.

**How it works:** After the scrape step, `cache_research.py` writes a JSON file keyed by a hash of the topic string. On the next run for the same topic, the pipeline checks this cache first. If the cached data is under 24 hours old, it skips the search and scrape steps entirely and goes straight to synthesis.

**Cache file naming:** `<topic-hash>.json` — you don't need to manage these manually.

**When to bypass the cache:** If you want fresh research (e.g., breaking news on the topic), ask the agent:
> "Run the pipeline with fresh research — bypass the cache"

The agent will delete the cached file for that topic before running, forcing a new scrape.

**When to clear the whole cache:** If disk space is a concern or you want a clean slate:
> "Clear the research cache"

Cache files are gitignored and fully regenerable — safe to delete any time.
