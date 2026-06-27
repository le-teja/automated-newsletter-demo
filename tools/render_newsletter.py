#!/usr/bin/env python3
"""Render the final email-safe HTML newsletter and plain text version."""

import argparse
import base64
import json
import os
import sys
import textwrap

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", ".tmp", "output")
HTML_OUTPUT = os.path.join(OUTPUT_DIR, "newsletter.html")
PLAIN_OUTPUT = os.path.join(OUTPUT_DIR, "newsletter_plain.txt")


def encode_image(path: str) -> str | None:
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def load_svg_elements(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render_plain_text(content: dict) -> str:
    """Render a plain text version with 72-char line wrapping."""
    lines = []

    # Title
    topic = content.get("topic", "Newsletter")
    lines.append(topic.upper())
    lines.append("=" * len(topic))
    lines.append("")

    # Intro
    intro = content.get("intro", "")
    for para in intro.split("\n"):
        if para.strip():
            lines.append(textwrap.fill(para.strip(), width=72))
            lines.append("")

    # Sections
    for section in content.get("sections", []):
        heading = section.get("heading", "")
        lines.append(heading.upper())
        lines.append("-" * len(heading))
        lines.append("")

        body = section.get("body", "")
        for para in body.split("\n"):
            if para.strip():
                lines.append(textwrap.fill(para.strip(), width=72))
                lines.append("")

        for dp in section.get("data_points", []):
            if isinstance(dp.get("value"), (int, float)):
                lines.append(f"  - {dp['label']}: {dp['value']}{dp.get('unit', '')}")
        if section.get("data_points"):
            lines.append("")

    # Takeaways
    takeaways = content.get("takeaways", [])
    if takeaways:
        lines.append("KEY TAKEAWAYS")
        lines.append("-------------")
        for t in takeaways:
            lines.append(textwrap.fill(f"* {t}", width=72, subsequent_indent="  "))
        lines.append("")

    # Sources
    sources = content.get("sources", [])
    if sources:
        lines.append("SOURCES")
        lines.append("-------")
        for s in sources:
            lines.append(f"- {s['title']}")
            lines.append(f"  {s['url']}")
        lines.append("")

    lines.append("--")
    lines.append("You're receiving this because you subscribed.")
    lines.append("To unsubscribe, reply with 'unsubscribe' in the subject line.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Render the newsletter HTML and plain text")
    parser.add_argument("content_json", help="Path to newsletter_content.json")
    parser.add_argument("--chart", default=None, help="Path to chart.png")
    parser.add_argument("--hero", default=None, help="Path to hero_image.png")
    parser.add_argument("--svg", default=None, help="Path to svg_elements.json")
    parser.add_argument("--variant", choices=["long-form", "quick-digest", "data-heavy"], default="long-form")
    parser.add_argument("--sender-email", default=os.environ.get("GMAIL_FROM", "newsletter@example.com"))
    args = parser.parse_args()

    with open(args.content_json, encoding="utf-8") as f:
        content = json.load(f)

    # Infer topic from content or filename
    topic = content.get("topic", "Newsletter")

    svg = load_svg_elements(args.svg)
    hero_b64 = encode_image(args.hero)
    chart_b64 = encode_image(args.chart)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)
    template = env.get_template("newsletter.html.j2")

    html = template.render(
        topic=topic,
        variant=args.variant,
        preheader=content.get("preheader", ""),
        intro=content.get("intro", ""),
        sections=content.get("sections", []),
        takeaways=content.get("takeaways", []),
        sources=content.get("sources", []),
        hero_image_b64=hero_b64,
        chart_b64=chart_b64,
        header_banner_svg=svg.get("header_banner"),
        divider_svg=svg.get("divider"),
        badge_svg=svg.get("badge"),
        sender_email=args.sender_email,
    )

    # Inline all CSS for email-client compatibility
    try:
        import css_inline
        inliner = css_inline.CSSInliner()
        html = inliner.inline(html)
    except ImportError:
        print("Warning: css-inline not installed. CSS may not be inlined. Run: pip install css-inline")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    # Plain text version
    content["topic"] = topic
    plain = render_plain_text(content)
    with open(PLAIN_OUTPUT, "w", encoding="utf-8") as f:
        f.write(plain)

    print(f"HTML newsletter: {HTML_OUTPUT}")
    print(f"Plain text:      {PLAIN_OUTPUT}")
    print(f"  Hero image:    {'embedded' if hero_b64 else 'none'}")
    print(f"  Chart:         {'embedded' if chart_b64 else 'none'}")
    print(f"  SVG graphics:  {'embedded' if svg else 'none'}")


if __name__ == "__main__":
    main()
