#!/usr/bin/env python3
"""Synthesize newsletter content from scraped articles using Gemini 2.0 Flash."""

import argparse
import json
import os
import re
import sys

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "newsletter_content.json")
MAX_WORDS_PER_ARTICLE = 1500

SYSTEM_PROMPT = """You are an expert newsletter writer. You produce engaging, well-researched newsletters
that are informative, concise, and enjoyable to read. You write in a clear, professional tone
with personality. You always return valid JSON — no markdown fences, no extra explanation."""

VARIANT_INSTRUCTIONS = {
    "long-form": "Write a full newsletter with a 2-3 paragraph intro, 4-5 detailed sections with body text, and a takeaways list.",
    "quick-digest": "Write a concise newsletter with a short intro paragraph, 3-4 bullet-heavy sections (minimal prose), and a brief takeaways list.",
    "data-heavy": "Lead with the most striking statistic in the intro. Each section should open with a key number or data point before any prose.",
}

USER_PROMPT_TEMPLATE = """Topic: {topic}

Create a newsletter based on the research articles below. Return ONLY valid JSON matching this exact structure:

{{
  "subject_lines": [
    "factual subject line (states the key fact or update)",
    "curiosity-gap subject line (makes reader wonder)",
    "benefit-led subject line (what reader gains by reading)"
  ],
  "preheader": "Exactly 80-100 characters. The preview snippet shown in Gmail before opening.",
  "intro": "Opening section. {variant_instruction}",
  "sections": [
    {{
      "heading": "Section heading",
      "body": "Section body text. Multiple sentences.",
      "data_points": [
        {{"label": "Metric name", "value": 42, "unit": "%"}}
      ]
    }}
  ],
  "takeaways": [
    "Key takeaway 1",
    "Key takeaway 2",
    "Key takeaway 3"
  ],
  "sources": [
    {{"title": "Article title", "url": "https://..."}}
  ],
  "image_prompt": "A professional, flat-style illustration for a newsletter about {topic}. Minimal, clean design. Blue and white color palette. No text in image. Suitable for a newsletter header."
}}

Rules:
- data_points array may be empty [] if no numeric data exists for that section
- All values in data_points must be numbers (integers or floats), not strings
- preheader must be between 80 and 100 characters
- subject_lines must have exactly 3 items
- Return ONLY the JSON object, nothing else

Research articles:
{articles}"""


def truncate_articles(articles: list[dict]) -> list[dict]:
    truncated = []
    for a in articles:
        words = a["text"].split()
        if len(words) > MAX_WORDS_PER_ARTICLE:
            text = " ".join(words[:MAX_WORDS_PER_ARTICLE]) + "..."
        else:
            text = a["text"]
        truncated.append({**a, "text": text})
    return sorted(truncated, key=lambda x: x.get("word_count", 0), reverse=True)


def call_gemini(prompt: str, model_name: str) -> str:
    client = genai.Client(api_key=os.environ["GOOGLE_AI_API_KEY"])
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        ),
    )
    return response.text


def parse_json_response(text: str) -> dict:
    text = text.strip()
    # Strip markdown fences if model added them anyway
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description="Synthesize newsletter content via Gemini Flash")
    parser.add_argument("topic", help="Newsletter topic")
    parser.add_argument("articles_json", help="Path to scraped_articles.json")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use")
    parser.add_argument("--variant", choices=["long-form", "quick-digest", "data-heavy"], default="long-form")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_AI_API_KEY"):
        print("Error: GOOGLE_AI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    with open(args.articles_json, encoding="utf-8") as f:
        articles = json.load(f)

    articles = truncate_articles(articles)

    articles_text = "\n\n---\n\n".join(
        f"Title: {a['title']}\nURL: {a['url']}\n\n{a['text']}" for a in articles
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        topic=args.topic,
        variant_instruction=VARIANT_INSTRUCTIONS[args.variant],
        articles=articles_text,
    )

    print(f"Calling {args.model} for topic: {args.topic}")
    raw = call_gemini(prompt, args.model)

    try:
        content = parse_json_response(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed ({e}), retrying with strict prompt...")
        strict_prefix = "You must return only valid JSON. No markdown, no explanation, no fences. Start your response with {{ and end with }}.\n\n"
        raw = call_gemini(strict_prefix + prompt, args.model)
        content = parse_json_response(raw)

    # Validate required keys
    required = {"subject_lines", "preheader", "intro", "sections", "takeaways", "sources", "image_prompt"}
    missing = required - set(content.keys())
    if missing:
        print(f"Warning: missing keys in response: {missing}", file=sys.stderr)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)

    print(f"Newsletter content saved to {OUTPUT_PATH}")
    print(f"  Sections: {len(content.get('sections', []))}")
    print(f"  Subject lines:")
    for s in content.get("subject_lines", []):
        print(f"    - {s}")


if __name__ == "__main__":
    main()
