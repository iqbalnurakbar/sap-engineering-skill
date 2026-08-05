#!/usr/bin/env python3
"""
Render the "1.5 High-Level Process Flow" diagram WITHOUT Graphviz, using
matplotlib instead. This is the fallback renderer for when `dot` isn't
available and couldn't be installed (see check_dependencies.py /
SKILL.md) — it produces the same kind of image (top-to-bottom boxes
connected by labeled arrows) so the final .docx still gets a real
diagram, not a text substitute. Never falls back to Markdown for this
reason; the document format is unaffected by which renderer draws the
picture.

Input is a small JSON file describing the flow as an ordered, single-
column list of steps — the same shape the Graphviz path would draft
before turning it into a .dot file:

    [
      {"label": "User uploads file via ZEDTUPLOAD_EXEC"},
      {"label": "ZCL_WS_NDS_STAGING validates and stages rows",
       "edge_label": "raw file rows"},
      {"label": "BAPI_SALESORDER_CREATEFROMDAT2 creates SD document",
       "edge_label": "staged + validated rows"}
    ]

`edge_label` is the text on the arrow leading INTO that step (omit or
leave empty for the first step, which has no incoming arrow). Every
step must be something confirmed by the source material or the user —
this script only draws what you give it; it does not invent steps.

Usage:
    python scripts/render_diagram_matplotlib.py <steps.json> <output.png> \
        [--width-in 6.5] [--title "..."]

Exits non-zero with a clear message if matplotlib isn't importable —
check `matplotlib.available` from check_dependencies.py before calling
this.
"""
import argparse
import json
import sys
import textwrap


def render(steps, output_path, width_in, title=None):
    try:
        import matplotlib
        matplotlib.use("Agg")  # no display needed, just write the file
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    except ImportError as e:
        print(f"ERROR: matplotlib not importable: {e}")
        sys.exit(1)

    if not steps:
        print("ERROR: no steps provided — nothing to render.")
        sys.exit(1)

    box_w, box_h, gap = 5.0, 0.9, 0.9
    n = len(steps)
    fig_h = n * (box_h + gap) + (0.6 if title else 0.2)
    fig_w = width_in

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, box_w + 1)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    if title:
        ax.text(fig_w / 2, fig_h - 0.15, title, ha="center", va="top",
                 fontsize=12, fontweight="bold")

    y = fig_h - (0.6 if title else 0.2)
    centers = []
    for step in steps:
        y_top = y
        y_bottom = y_top - box_h
        y_center = (y_top + y_bottom) / 2
        centers.append(y_center)

        label = step.get("label", "").strip()
        wrapped = "\n".join(textwrap.wrap(label, width=42)) or "(no label)"

        box = FancyBboxPatch(
            (0.5, y_bottom), box_w, box_h,
            boxstyle="round,pad=0.08,rounding_size=0.12",
            linewidth=1.4, edgecolor="#2f5d8a", facecolor="#dbe9f7",
        )
        ax.add_patch(box)
        ax.text(0.5 + box_w / 2, y_center, wrapped, ha="center", va="center",
                 fontsize=9.5, wrap=True)

        y = y_bottom - gap

    # Arrows drawn after all boxes so labels sit cleanly between them.
    for i in range(1, n):
        y_from = centers[i - 1] - box_h / 2
        y_to = centers[i] + box_h / 2
        x_mid = 0.5 + box_w / 2

        arrow = FancyArrowPatch(
            (x_mid, y_from), (x_mid, y_to),
            arrowstyle="-|>", mutation_scale=14,
            linewidth=1.2, color="#444444",
        )
        ax.add_patch(arrow)

        edge_label = (steps[i].get("edge_label") or "").strip()
        if edge_label:
            y_label = (y_from + y_to) / 2
            ax.text(x_mid + 0.15, y_label, edge_label, ha="left",
                     va="center", fontsize=8, style="italic",
                     color="#555555")

    fig.tight_layout(pad=0.3)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Rendered {len(steps)}-step flow diagram to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("steps_json", help="Path to a JSON file: list of "
                         "{label, edge_label} steps, top to bottom")
    parser.add_argument("output_png")
    parser.add_argument("--width-in", type=float, default=6.5)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    with open(args.steps_json, "r", encoding="utf-8") as f:
        steps = json.load(f)

    render(steps, args.output_png, args.width_in, args.title)
