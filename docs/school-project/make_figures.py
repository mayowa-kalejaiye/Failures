"""Figures for Chapter 3 of the Failures final-year project report.

Black-and-white, print-safe boxes-and-arrows diagrams rendered with
matplotlib. Saved as PNG into docs/school-project/figures/.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse

OUT = pathlib.Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,
})


def box(ax, x, y, w, h, text, fs=8.5, style="round,pad=0.02"):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=style, facecolor="white",
        edgecolor="black", linewidth=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, wrap=True)


def arrow(ax, x1, y1, x2, y2, label=""):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
        linewidth=1.0, color="black", shrinkA=1, shrinkB=3))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, label,
                ha="center", va="bottom", fontsize=7.5)


def finish(fig, name):
    fig.tight_layout()
    p = OUT / name
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("saved", p.name)


# ------------------------------------------------- Fig 3.1 architecture
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis("off")
box(ax, 0.3, 4.3, 2.4, 1.1, "Coding agent\n(Claude / Cursor / Codex)", 8)
box(ax, 3.8, 4.3, 2.4, 1.1, "MCP server\n13 tools (stdio)", 8)
box(ax, 7.3, 4.3, 2.4, 1.1, "Findings\nseverity + evidence", 8)
box(ax, 0.3, 2.3, 2.4, 1.1, "Knowledge base\nprinciples / rules", 8)
box(ax, 3.8, 2.3, 2.4, 1.1, "Deterministic engine\nreview + score", 8)
box(ax, 7.3, 2.3, 2.4, 1.1, "Evaluation harness\n10 criteria", 8)
box(ax, 3.8, 0.5, 2.4, 1.0, "Frozen artifacts\nprompts / manifests", 7.5)
for x1, x2 in [(2.7, 3.8), (6.2, 7.3)]:
    arrow(ax, x1, 4.85, x2, 4.85)
    arrow(ax, x1, 2.85, x2, 2.85)
arrow(ax, 5.0, 2.3, 5.0, 1.5)
finish(fig, "fig31_architecture.png")

# ------------------------------------------------- Fig 3.2 knowledge graph
fig, ax = plt.subplots(figsize=(6.4, 2.0))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3)
ax.axis("off")
labels = ["Principle", "Failure mode", "Pattern", "Test"]
xs = [0.4, 2.9, 5.4, 7.9]
for x, lab in zip(xs, labels):
    box(ax, x, 1.1, 1.7, 0.9, lab, 8.5)
    if x > 0.4:
        arrow(ax, x - 0.2, 1.55, x, 1.55)
subs = ["covers", "mitigated by", "verified by"]
for x, s in zip([2.05, 4.55, 7.05], subs):
    ax.text(x, 1.75, s, ha="center", fontsize=7)
box(ax, 0.4, 0.05, 1.7, 0.7, "Invariant", 7.5)
box(ax, 2.9, 0.05, 1.7, 0.7, "Component type", 7.5)
arrow(ax, 2.1, 0.4, 2.9, 0.4)
ax.text(2.5, 0.55, "applies to", ha="center", fontsize=7)
ax.text(5.0, 2.6, "", ha="center",
        fontsize=7.5, style="italic")
finish(fig, "fig32_knowledge_graph.png")

# ------------------------------------------------- Fig 3.3 use case
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.4)
ax.axis("off")
ax.add_patch(plt.Rectangle((3.2, 0.3), 6.4, 5.7, fill=False, edgecolor="black",
                           linewidth=1.0))
ax.text(6.4, 5.75, "Failures system", ha="center", fontsize=8.5,
        weight="bold")


def stick(ax, cx, y_base, h=1.1):
    ax.plot(cx, y_base + h, "o", color="black", ms=7)
    ax.plot([cx, cx], [y_base, y_base + h - 0.1], color="black", lw=1.2)
    ax.plot([cx - 0.4, cx + 0.4], [y_base + h - 0.45, y_base + h - 0.45],
            color="black", lw=1.2)
    ax.plot([cx, cx - 0.35], [y_base, y_base - 0.5], color="black", lw=1.2)
    ax.plot([cx, cx + 0.35], [y_base, y_base - 0.5], color="black", lw=1.2)


def oval(ax, cx, cy, w, h, text, fs=7.5):
    e = Ellipse((cx, cy), w, h, fill=True, facecolor="white",
                edgecolor="black", linewidth=1.0)
    ax.add_patch(e)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs)


stick(ax, 1.4, 4.35)
ax.text(1.4, 3.65, "Coding\nagent", ha="center", fontsize=8)
agent_uses = [("Submit code / plan\nfor review", 5.35),
              ("Receive findings\n+ evidence", 4.55),
              ("Generate failure\ntests", 3.75),
              ("View resilience\nscore", 2.95)]
for u, y in agent_uses:
    oval(ax, 6.4, y, 3.4, 0.62, u)
    ax.plot([1.85, 4.6], [4.9 - (5.35 - y) * 0.35, y], color="black", lw=0.7)
stick(ax, 1.4, 1.05)
ax.text(1.4, 0.35, "Administrator", ha="center", fontsize=8)
admin_uses = [("Maintain knowledge\nbase JSON", 1.85),
              ("Freeze prompts\n+ manifests", 1.05)]
for u, y in admin_uses:
    oval(ax, 6.4, y, 3.4, 0.62, u)
    ax.plot([1.85, 4.6], [1.6 - (1.85 - y) * 0.35, y], color="black", lw=0.7)
finish(fig, "fig33_usecase.png")

# ------------------------------------------------- Fig 3.4 evaluation flow
fig, ax = plt.subplots(figsize=(6.4, 2.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis("off")
box(ax, 0.2, 1.7, 2.0, 1.1, "Baseline arm\n(no guardrails)", 8)
box(ax, 0.2, 0.3, 2.0, 1.1, "Failures arm\n(MCP connected)", 8)
box(ax, 3.9, 1.0, 2.2, 1.1, "Harness\nreview + 10 criteria", 8)
box(ax, 7.8, 1.0, 2.0, 1.1, "Tables 4.x\nresults", 8)
arrow(ax, 2.2, 2.25, 3.9, 1.85)
arrow(ax, 2.2, 0.85, 3.9, 1.25)
arrow(ax, 6.1, 1.55, 7.8, 1.55)
ax.text(3.05, 2.62, "17 matched pairs", ha="center", fontsize=7.5)
ax.text(3.05, 0.42, "same 6 prompts", ha="center", fontsize=7.5)
finish(fig, "fig34_eval_flow.png")
print("figures done")
