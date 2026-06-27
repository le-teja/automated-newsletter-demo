#!/usr/bin/env python3
"""Generate decorative elements for the newsletter (header banner PNG, SVG dividers/badge)."""

import argparse
import base64
import io
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


def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def make_header_banner_png_b64(title: str, theme: dict) -> str:
    """Render the header banner as a base64-encoded PNG using Pillow.
    Gmail strips inline SVG, so we rasterize to a PNG that embeds safely as <img>."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1200, 240  # 2x for retina; displayed at 600x120
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Horizontal gradient: primary (left) → secondary (right)
    c1 = _hex_to_rgb(theme["primary"])
    c2 = _hex_to_rgb(theme["secondary"])
    for x in range(W):
        t = x / W
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(x, 0), (x, H)], fill=(r, g, b))

    # Decorative circles (accent, low opacity)
    accent = _hex_to_rgb(theme["accent"])
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse((-80, -80, 200, 200), fill=(*accent, 38))   # top-left, 0.15 opacity
    odraw.ellipse((1060, 100, 1260, 300), fill=(*accent, 26))  # bottom-right, 0.10 opacity
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Text: wrap onto two lines if long
    words = title.split()
    if len(title) > 40:
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
        font_size = 52
    else:
        lines = [title]
        font_size = 60

    # Use default font (no external font required)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    total_h = len(lines) * (font_size + 8)
    y_start = (H - total_h) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = y_start + i * (font_size + 8)
        # Subtle shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 80))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


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
        "header_banner_png_b64": make_header_banner_png_b64(args.topic, theme),
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
