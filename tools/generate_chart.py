#!/usr/bin/env python3
"""Generate a data chart PNG from newsletter content data_points."""

import argparse
import json
import os
import sys

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", ".tmp", "chart.png")

# Email-safe palette: works on light backgrounds, readable without color inversion
COLORS = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2"]
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#1E293B"
GRID_COLOR = "#E2E8F0"


def collect_data_points(sections: list[dict]) -> list[dict]:
    points = []
    for section in sections:
        for dp in section.get("data_points", []):
            if isinstance(dp.get("value"), (int, float)):
                points.append({
                    "label": dp.get("label", ""),
                    "value": dp["value"],
                    "unit": dp.get("unit", ""),
                })
    return points


def detect_chart_type(points: list[dict]) -> str:
    if not points:
        return "none"
    units = [p["unit"] for p in points]
    if all(u == "%" for u in units) and len(points) <= 5:
        return "donut"
    if len(points) >= 5:
        return "bar"
    return "bar"


def _truncate_label(label: str, max_chars: int = 18) -> str:
    words = label.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines[:2])  # max 2 lines


def render_bar_chart(points: list[dict], output_path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [_truncate_label(p["label"]) for p in points]
    values = [p["value"] for p in points]
    units = points[0]["unit"] if points else ""

    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=144)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.bar(labels, values, color=COLORS[: len(labels)], width=0.6, zorder=3)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(axis="y", colors=TEXT_COLOR, labelsize=8)
    ax.tick_params(axis="x", colors=TEXT_COLOR, labelsize=7, pad=4)
    for tick in ax.get_xticklabels():
        tick.set_multialignment("center")

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.02,
            f"{val}{units}",
            ha="center",
            va="bottom",
            fontsize=8,
            color=TEXT_COLOR,
            fontweight="bold",
        )

    plt.tight_layout(pad=1.2)
    plt.savefig(output_path, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()


def render_donut_chart(points: list[dict], output_path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [p["label"] for p in points]
    values = [p["value"] for p in points]

    fig, ax = plt.subplots(figsize=(6, 3), dpi=144)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=COLORS[: len(values)],
        autopct="%1.0f%%",
        startangle=90,
        wedgeprops={"width": 0.55, "edgecolor": BG_COLOR, "linewidth": 2},
        pctdistance=0.75,
    )
    for t in autotexts:
        t.set_color(BG_COLOR)
        t.set_fontsize(8)
        t.set_fontweight("bold")

    ax.legend(
        wedges,
        labels,
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=8,
        frameon=False,
        labelcolor=TEXT_COLOR,
    )

    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate a chart PNG from newsletter data_points")
    parser.add_argument("content_json", help="Path to newsletter_content.json")
    parser.add_argument("--chart-type", choices=["bar", "donut", "auto"], default="auto")
    args = parser.parse_args()

    with open(args.content_json, encoding="utf-8") as f:
        content = json.load(f)

    points = collect_data_points(content.get("sections", []))

    if not points:
        print("NO_DATA")
        sys.exit(0)

    chart_type = args.chart_type if args.chart_type != "auto" else detect_chart_type(points)
    print(f"Rendering {chart_type} chart with {len(points)} data points")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    if chart_type == "donut":
        render_donut_chart(points, OUTPUT_PATH)
    else:
        render_bar_chart(points, OUTPUT_PATH)

    print(f"Chart saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
