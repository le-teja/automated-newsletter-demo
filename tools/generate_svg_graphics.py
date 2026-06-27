#!/usr/bin/env python3
"""Generate SVG decorative elements for the newsletter (header banner, dividers, badge)."""

import argparse
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "svg_elements.json")

# Color themes by topic category keyword
THEMES = {
    "tech": {"primary": "#2563EB", "secondary": "#7C3AED", "accent": "#06B6D4", "bg": "#EFF6FF"},
    "health": {"primary": "#059669", "secondary": "#0891B2", "accent": "#34D399", "bg": "#ECFDF5"},
    "finance": {"primary": "#D97706", "secondary": "#2563EB", "accent": "#F59E0B", "bg": "#FFFBEB"},
    "science": {"primary": "#7C3AED", "secondary": "#2563EB", "accent": "#A78BFA", "bg": "#F5F3FF"},
    "climate": {"primary": "#059669", "secondary": "#065F46", "accent": "#6EE7B7", "bg": "#ECFDF5"},
    "default": {"primary": "#2563EB", "secondary": "#1E40AF", "accent": "#93C5FD", "bg": "#EFF6FF"},
}

TOPIC_KEYWORDS = {
    "tech": ["tech", "ai", "software", "digital", "cyber", "data", "cloud", "robot", "machine", "algorithm"],
    "health": ["health", "medical", "pharma", "wellness", "mental", "hospital", "drug", "treatment", "care"],
    "finance": ["finance", "financial", "invest", "stock", "market", "economy", "crypto", "bank", "money", "fund"],
    "science": ["science", "research", "study", "quantum", "space", "physics", "biology", "chem"],
    "climate": ["climate", "environment", "green", "carbon", "energy", "solar", "wind", "sustainable"],
}


def detect_theme(topic: str) -> dict:
    topic_lower = topic.lower()
    for category, keywords in TOPIC_KEYWORDS.items():
        if any(kw in topic_lower for kw in keywords):
            return THEMES[category]
    return THEMES["default"]


def make_header_banner(title: str, theme: dict) -> str:
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    words = safe_title.split()
    # Wrap long titles onto two lines
    if len(safe_title) > 45:
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        text_block = f"""
    <text x="300" y="52" font-family="Georgia, serif" font-size="22" font-weight="bold"
          fill="#FFFFFF" text-anchor="middle">{line1}</text>
    <text x="300" y="78" font-family="Georgia, serif" font-size="22" font-weight="bold"
          fill="#FFFFFF" text-anchor="middle">{line2}</text>"""
    else:
        text_block = f"""
    <text x="300" y="65" font-family="Georgia, serif" font-size="26" font-weight="bold"
          fill="#FFFFFF" text-anchor="middle">{safe_title}</text>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="120" viewBox="0 0 600 120">
  <defs>
    <linearGradient id="hg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{theme['primary']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{theme['secondary']};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="600" height="120" rx="8" fill="url(#hg)" />
  <circle cx="30" cy="30" r="60" fill="{theme['accent']}" fill-opacity="0.15" />
  <circle cx="570" cy="90" r="50" fill="{theme['accent']}" fill-opacity="0.10" />
  {text_block}
  <text x="300" y="100" font-family="Arial, sans-serif" font-size="11" fill="{theme['accent']}"
        text-anchor="middle" letter-spacing="3">NEWSLETTER</text>
</svg>"""


def make_divider(theme: dict) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="20" viewBox="0 0 600 20">
  <line x1="0" y1="10" x2="260" y2="10" stroke="{theme['accent']}" stroke-width="1.5" />
  <circle cx="300" cy="10" r="5" fill="{theme['primary']}" />
  <line x1="340" y1="10" x2="600" y2="10" stroke="{theme['accent']}" stroke-width="1.5" />
</svg>"""


def make_badge(theme: dict) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="30" viewBox="0 0 120 30">
  <rect width="120" height="30" rx="15" fill="{theme['primary']}" />
  <text x="60" y="20" font-family="Arial, sans-serif" font-size="11" font-weight="bold"
        fill="#FFFFFF" text-anchor="middle" letter-spacing="1">KEY INSIGHTS</text>
</svg>"""


def main():
    parser = argparse.ArgumentParser(description="Generate SVG decorative elements for a newsletter")
    parser.add_argument("topic", help="Newsletter topic (used to auto-detect color theme)")
    parser.add_argument("--theme", choices=list(THEMES.keys()), default=None, help="Override auto-detected theme")
    args = parser.parse_args()

    theme = THEMES[args.theme] if args.theme else detect_theme(args.topic)
    print(f"Using theme: {theme['primary']} / {theme['secondary']}")

    elements = {
        "header_banner": make_header_banner(args.topic, theme),
        "divider": make_divider(theme),
        "badge": make_badge(theme),
        "theme": theme,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(elements, f, indent=2, ensure_ascii=False)

    print(f"SVG elements saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
