"""
visualization/pipeline.py
============================
Purpose:
    Render the full PiGPL compiler pipeline (Source -> ... -> Output) as a
    single PNG diagram, visually distinguishing stages implemented in
    Phase 1 from stages architected but planned for Phase 2/3 -- matching
    the Phase 1 design document's Section 8.1 architecture diagram.

Input:
    None (the pipeline stage list and their Phase 1 status are fixed by
    the project's architecture).

Output:
    outputs/diagrams/compiler_pipeline.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# (stage label, status) -- status is "done" for Phase 1, "planned" otherwise.
STAGES = [
    ("PiGPL Source Code", "done"),
    ("Lexical Analyzer", "done"),
    ("Token Stream", "done"),
    ("Parser / Syntax Analyzer", "done"),
    ("Parse Tree / AST", "done"),
    ("Semantic Analyzer + Symbol Table", "done"),
    ("Intermediate Code Generator (IR)", "planned"),
    ("Optimizer", "planned"),
    ("Target Code Generator", "planned"),
    ("Execution Engine", "planned"),
    ("Final Program Output", "planned"),
]

COLORS = {
    "done": ("#dcfce7", "#16a34a"),      # light green fill, green border
    "planned": ("#f1f5f9", "#94a3b8"),   # light grey fill, grey border
}


def render_pipeline(output_path="outputs/diagrams/compiler_pipeline.png"):
    n = len(STAGES)
    fig_height = 1.05 * n + 0.8
    fig, ax = plt.subplots(figsize=(7.5, fig_height))

    box_w, box_h = 6.4, 0.72
    x_center = 3.2

    for i, (label, status) in enumerate(STAGES):
        y = (n - 1 - i) * 1.05
        face, edge = COLORS[status]
        box = FancyBboxPatch(
            (x_center - box_w / 2, y),
            box_w,
            box_h,
            boxstyle="round,pad=0.06,rounding_size=0.12",
            linewidth=1.8,
            edgecolor=edge,
            facecolor=face,
        )
        ax.add_patch(box)
        tag = "Implemented (Phase 1)" if status == "done" else "Planned"
        ax.text(x_center, y + box_h / 2 + 0.12, label, ha="center", va="center",
                fontsize=10.5, color="#0f172a", fontweight="bold")
        ax.text(x_center, y + box_h / 2 - 0.18, tag, ha="center", va="center",
                fontsize=8, color=edge)
        if i < n - 1:
            ax.annotate(
                "", xy=(x_center, y - 0.03), xytext=(x_center, y),
                arrowprops=dict(arrowstyle="-|>", color="#64748b", lw=1.4),
            )

    ax.set_xlim(0, 6.4)
    ax.set_ylim(-0.3, n * 1.05 + 0.2)
    ax.axis("off")
    ax.set_title("PiGPL Compiler Pipeline", fontsize=14, color="#0f172a", pad=14)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor="white")
    plt.close(fig)
    return output_path
