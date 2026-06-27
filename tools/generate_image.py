#!/usr/bin/env python3
"""Generate a hero image using Gemini image generation (gemini-3.1-flash-image)."""

import argparse
import base64
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "hero_image.png")
USAGE_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "cache", "imagen_usage.json")
FREE_TIER_LIMIT = 50
WARN_THRESHOLD = 5
IMAGE_MODEL = "gemini-2.5-flash-image"


def load_usage() -> dict:
    if not os.path.exists(USAGE_PATH):
        return {"month": "", "count": 0}
    with open(USAGE_PATH) as f:
        return json.load(f)


def save_usage(usage: dict) -> None:
    os.makedirs(os.path.dirname(USAGE_PATH), exist_ok=True)
    with open(USAGE_PATH, "w") as f:
        json.dump(usage, f)


def check_and_increment_usage() -> int:
    usage = load_usage()
    current_month = datetime.now().strftime("%Y-%m")
    if usage.get("month") != current_month:
        usage = {"month": current_month, "count": 0}
    remaining = FREE_TIER_LIMIT - usage["count"]
    if remaining <= 0:
        print(f"Warning: Monthly free image limit ({FREE_TIER_LIMIT}) reached. Skipping.")
        sys.exit(0)
    if remaining <= WARN_THRESHOLD:
        print(f"Warning: Only {remaining} free images remaining this month.")
    usage["count"] += 1
    save_usage(usage)
    return remaining - 1


def generate_image(prompt: str, api_key: str) -> bytes:
    from google import genai

    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=IMAGE_MODEL,
        input=prompt,
    )
    return base64.b64decode(interaction.output_image.data)


def main():
    parser = argparse.ArgumentParser(description="Generate a newsletter hero image via Gemini")
    parser.add_argument("content_json", help="Path to newsletter_content.json")
    parser.add_argument("--style", default=None, help="Override the image prompt")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_AI_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    with open(args.content_json, encoding="utf-8") as f:
        content = json.load(f)

    prompt = args.style or content.get("image_prompt", "")
    if not prompt:
        print("No image prompt found in content JSON.", file=sys.stderr)
        sys.exit(1)

    remaining = check_and_increment_usage()

    print(f"Generating image with {IMAGE_MODEL}...")
    print(f"Prompt: {prompt[:100]}...")

    try:
        image_bytes = generate_image(prompt, api_key)
    except Exception as e:
        print(f"Image generation failed: {e}", file=sys.stderr)
        usage = load_usage()
        usage["count"] = max(0, usage["count"] - 1)
        save_usage(usage)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(image_bytes)

    print(f"Hero image saved to {OUTPUT_PATH}")
    print(f"Free images remaining this month: {remaining}")


if __name__ == "__main__":
    main()
