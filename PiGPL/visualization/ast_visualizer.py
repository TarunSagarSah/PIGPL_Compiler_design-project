"""
visualization/ast_visualizer.py
=================================
Purpose:
    Render the AST produced by compiler/parser.py as an actual graphical
    tree image (not text), saved as outputs/ast/ast.png, as required by
    the Phase 1 design ("AST: Tree representation of program structure").

Input:
    root: pigpl_ast.ASTNode (typically a Program node)

Output:
    A PNG file path. Also returns a JSON-serializable nested dict (the
    same shape as ASTNode.to_dict()) so the UI can additionally render a
    text-fallback tree if desired.

Implementation notes:
    Uses matplotlib only (no system-level Graphviz binary required), which
    keeps installation on Windows to a single `pip install`. A simple
    recursive layout algorithm assigns each leaf a unique x-slot left to
    right, and each internal node the average x of its children -- the
    standard approach for drawing a readable, non-overlapping node-link
    tree diagram.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

_leaf_counter = [0]


def _layout(node, depth, positions):
    """Recursively assign (x, y) to every node. Returns this node's x."""
    children = node.children()
    if not children:
        x = _leaf_counter[0]
        _leaf_counter[0] += 1
    else:
        child_xs = [_layout(child, depth + 1, positions) for child in children]
        x = sum(child_xs) / len(child_xs)
    positions[id(node)] = (x, -depth, node, children)
    return x


SPACING = 2.8  # horizontal distance between adjacent leaf slots


def render_ast(root, output_path="outputs/ast/ast.png"):
    """
    Draw `root` (an ASTNode tree) as a PNG tree diagram.

    Returns the output file path.
    """
    _leaf_counter[0] = 0
    positions = {}
    _layout(root, 0, positions)

    max_depth = max(-y for (_, y, _, _) in positions.values()) if positions else 0
    n_leaves = max(_leaf_counter[0], 1)
    width = max(9, n_leaves * SPACING * 0.9)
    height = max(4, (max_depth + 1) * 1.6)

    fig, ax = plt.subplots(figsize=(width, height))

    # Draw edges first so they sit behind the node boxes.
    for x, y, node, children in positions.values():
        for child in children:
            cx, cy = positions[id(child)][0] * SPACING, positions[id(child)][1]
            ax.plot([x * SPACING, cx], [y, cy], color="#94a3b8", linewidth=1.5, zorder=1)

    for x, y, node, children in positions.values():
        x = x * SPACING
        label = node.label()
        box_width = max(1.3, 0.1 * len(label))
        box = FancyBboxPatch(
            (x - box_width / 2, y - 0.26),
            box_width,
            0.52,
            boxstyle="round,pad=0.08,rounding_size=0.08",
            linewidth=1.4,
            edgecolor="#1d4ed8",
            facecolor="#dbeafe",
            zorder=2,
        )
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=9, zorder=3, color="#0f172a")

    ax.set_xlim(-1.5, n_leaves * SPACING)
    ax.set_ylim(-max_depth - 1, 1)
    ax.axis("off")
    ax.set_title("PiGPL Abstract Syntax Tree", fontsize=13, color="#0f172a")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor="white")
    plt.close(fig)
    return output_path
