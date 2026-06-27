#!/usr/bin/env python3
"""Search for articles on a topic using Tavily (primary) or Brave Search (fallback)."""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "search_results.json")


def search_tavily(topic: str, num_results: int) -> list[dict]:
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY not set")

    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": topic,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": False,
            "max_results": num_results,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for r in data.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
            "source": "tavily",
        })
    return results


def search_brave(topic: str, num_results: int) -> list[dict]:
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        raise EnvironmentError("BRAVE_API_KEY not set")

    resp = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
        params={"q": topic, "count": num_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for i, r in enumerate(data.get("web", {}).get("results", [])):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("description", ""),
            "score": 1.0 - (i * 0.1),
            "source": "brave",
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Search for articles on a topic")
    parser.add_argument("topic", help="Topic to search for")
    parser.add_argument("--num-results", type=int, default=8, help="Number of results to fetch")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    results = None
    try:
        print(f"Searching Tavily for: {args.topic}")
        results = search_tavily(args.topic, args.num_results)
        print(f"Tavily returned {len(results)} results")
    except Exception as e:
        print(f"Tavily failed ({e}), falling back to Brave Search...")
        try:
            results = search_brave(args.topic, args.num_results)
            print(f"Brave Search returned {len(results)} results")
        except Exception as e2:
            print(f"Brave Search also failed: {e2}", file=sys.stderr)
            sys.exit(1)

    if not results:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(results)} results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
