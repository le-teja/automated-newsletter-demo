#!/usr/bin/env python3
"""Fetch full article text for search results where Tavily content is short."""

import argparse
import json
import os
import sys
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "scraped_articles.json")
MIN_TAVILY_WORDS = 300
MIN_ARTICLE_WORDS = 100
USER_AGENT = "Mozilla/5.0 (compatible; NewsletterBot/1.0; research-only)"


def is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True


def extract_article_text(html: str) -> tuple[str, str]:
    """Return (title, body_text) using readability if available, else BeautifulSoup fallback."""
    try:
        from readability import Document
        doc = Document(html)
        title = doc.title()
        soup = BeautifulSoup(doc.summary(), "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return title, text
    except ImportError:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        title = soup.title.string if soup.title else ""
        text = soup.get_text(separator="\n", strip=True)
        return title, text


def scrape_url(url: str) -> dict | None:
    if not is_allowed(url):
        print(f"  Skipped (robots.txt): {url}")
        return None
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        title, text = extract_article_text(resp.text)
        words = text.split()
        if len(words) < MIN_ARTICLE_WORDS:
            print(f"  Skipped (likely paywalled, {len(words)} words): {url}")
            return None
        return {"url": url, "title": title, "text": text, "word_count": len(words)}
    except Exception as e:
        print(f"  Failed to scrape {url}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Scrape full article text from search results")
    parser.add_argument("results_json", help="Path to search_results.json")
    parser.add_argument("--max-articles", type=int, default=5, help="Max articles to scrape")
    args = parser.parse_args()

    with open(args.results_json, encoding="utf-8") as f:
        results = json.load(f)

    articles = []

    for r in results:
        if len(articles) >= args.max_articles:
            break

        content = r.get("content", "")
        word_count = len(content.split())

        if word_count >= MIN_TAVILY_WORDS:
            # Tavily already gave us enough content
            articles.append({
                "url": r["url"],
                "title": r["title"],
                "text": content,
                "word_count": word_count,
                "source": "tavily",
            })
            print(f"Using Tavily content for: {r['title'][:60]}")
        else:
            # Need to scrape the full page
            print(f"Scraping: {r['url']}")
            article = scrape_url(r["url"])
            if article:
                article["source"] = "scraped"
                articles.append(article)
                time.sleep(1)  # polite crawl delay

    if not articles:
        print("No articles collected.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    total_words = sum(a["word_count"] for a in articles)
    print(f"\nCollected {len(articles)} articles ({total_words:,} total words)")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
