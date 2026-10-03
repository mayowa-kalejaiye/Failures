"""Result charts for Chapter 4, generated from live evaluation artifacts."""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = pathlib.Path(__file__).resolve().parent / "figures"
sys.path.insert(0, str(ROOT / "mcp_server"))
sys.path.insert(0, str(ROOT / "evaluation"))
import run_evaluation as R

plt.rcParams.update({"font.family": "serif",
                     "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 9})

PROXY = json.loads((ROOT / "evaluation" / "results.json").read_text())
SCEN = ["payment", "queue", "authentication", "file-upload", "inventory",
        "webhook"]

# ------------------------------------------------- Fig 4.1 proxy findings
bc = [PROXY[s]["baseline"]["code_metrics"]["critical"] for s in SCEN]
fc = [PROXY[s]["failures_enabled"]["code_metrics"]["critical"] for s in SCEN]
bh = [PROXY[s]["baseline"]["code_metrics"]["high"] for s in SCEN]
fh = [PROXY[s]["failures_enabled"]["code_metrics"]["high"] for s in SCEN]
x = list(range(len(SCEN)))
w = 0.2
fig, ax = plt.subplots(figsize=(6.4, 2.8))
ax.bar([i - 1.5 * w for i in x], bc, w, label="CRITICAL baseline",
       color="black")
ax.bar([i - 0.5 * w for i in x], fc, w, label="CRITICAL enabled",
       color="white", edgecolor="black", hatch="///")
ax.bar([i + 0.5 * w for i in x], bh, w, label="HIGH baseline",
       color="dimgray")
ax.bar([i + 1.5 * w for i in x], fh, w, label="HIGH enabled",
       color="white", edgecolor="black", hatch="\\\\")
ax.set_xticks(x)
ax.set_xticklabels([s[:8] for s in SCEN], fontsize=8)
ax.set_ylabel("Findings")
ax.set_ylim(0, max(bc + bh) + 1)
ax.legend(fontsize=7.5, ncol=2)
fig.tight_layout()
fig.savefig(OUT / "fig41_proxy.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------- Fig 4.2 agent totals
pairs = []
for ag in ["claude", "cursor", "codex"]:
    for sc in R.SCENARIOS:
        b = R.load_code(sc, "manual", "baseline", ag)
        f = R.load_code(sc, "manual", "failures-enabled", ag)
        if b and f:
            pairs.append((R.evaluate_code(b, sc), R.evaluate_code(f, sc)))
tcb = sum(e[0]["critical"] for e in pairs)
tcf = sum(e[1]["critical"] for e in pairs)
thb = sum(e[0]["high"] for e in pairs)
thf = sum(e[1]["high"] for e in pairs)
fig, ax = plt.subplots(figsize=(6.4, 2.6))
cats = ["CRITICAL", "HIGH"]
base = [tcb, thb]
enab = [tcf, thf]
x = [0, 1]
ax.bar([i - 0.2 for i in x], base, 0.4, label="Baseline total (17 pairs)",
       color="black")
ax.bar([i + 0.2 for i in x], enab, 0.4, label="Enabled total (17 pairs)",
       color="white", edgecolor="black", hatch="///")
for i, (a, b) in enumerate(zip(base, enab)):
    ax.text(i - 0.2, a + 0.15, str(a), ha="center", fontsize=9)
    ax.text(i + 0.2, b + 0.15, str(b), ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(cats)
ax.set_ylabel("Total findings")
ax.set_ylim(0, max(base) + 2)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "fig42_agents.png", dpi=220, bbox_inches="tight")
plt.close(fig)
print("fig41 + fig42 done:",
      f"proxy crit {sum(bc)}->{sum(fc)}, high {sum(bh)}->{sum(fh)};",
      f"agents crit {tcb}->{tcf}, high {thb}->{thf}; pairs={len(pairs)}")
