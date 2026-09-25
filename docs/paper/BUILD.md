# Building the paper

Two renderers, one source of data. Both read the evaluation artifacts directly, so
neither can drift from the harness output.

## Canonical PDF (published artifact)

The published PDF is `Failures_MCP_Paper.pdf` (Zenodo 10.5281/zenodo.22966362), built
with ReportLab:

```bash
python tools/build_paper_pdf.py     # -> docs/paper/Failures_MCP_Paper.pdf
```

## IEEEtran LaTeX (for conference submission)

```bash
python tools/build_paper_tex.py     # -> docs/paper/main.tex  (all tables generated)
pdflatex main.tex && pdflatex main.tex
```

Requires a LaTeX distribution with `IEEEtran`, `booktabs`, `listings`, `multirow`.
Verified with MiKTeX 25.12; compiles with 0 errors and 0 overfull boxes, 10 pages.

## Refreshing the numbers

```bash
python evaluation/run_evaluation.py --mode proxy
python tools/build_paper_pdf.py
python tools/build_paper_tex.py
```

Never hand-edit a number in either manuscript: both renderers read
`evaluation/results.json`, `evaluation/adversarial_results.json`, and
`mcp_server/knowledge/*.json`.
