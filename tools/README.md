# Tool Conventions

Tools are Python scripts that do the actual work. They must be deterministic, self-contained, and safe to rerun.

## Naming

`verb_noun.py` — lowercase, underscores, imperative verb first. Match the workflow that calls it where possible.

Examples: `scrape_page.py`, `summarize_text.py`, `write_to_sheets.py`

## Script Structure

Every tool should follow this pattern:

```python
#!/usr/bin/env python3
"""One-line description of what this script does."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    # core logic here
    pass

if __name__ == "__main__":
    main()
```

## Conventions

**Credentials:** Always load from `.env` via `python-dotenv`. Never hardcode keys or paths.

**Arguments:** Accept inputs via `sys.argv` or `argparse`. No hardcoded values that should vary per run.

**Output:** Print results to stdout. Write files to `.tmp/`. Final deliverables go to cloud services, not local disk.

**Errors:** Print a clear error message and exit with a non-zero code on failure. Don't silently swallow exceptions.

**Idempotency:** Scripts should be safe to rerun. If a file already exists or a row is already written, handle it gracefully.

**Dependencies:** Add any new packages to `requirements.txt`.

## Running a Tool

```bash
python tools/script_name.py [args]
```

## Dependencies

Maintain a `requirements.txt` in the project root. Add packages as you introduce them.
