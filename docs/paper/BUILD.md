# Build
## Overleaf (recommended, 30s)
1. Zip docs/paper/* -> Upload to Overleaf -> Recompile (IEEEtran already included)
2. Or use ShareLaTeX: pdflatex main.tex -> figures/tables.tex is \input
## Local
tinytex: pdflatex main.tex
## Regenerate tables
python evaluation/run_evaluation.py --mode proxy  # updates evaluation/results.json -> figures/tables.tex is auto, but re-run the python snippet in docs/paper/figures if you want to refresh
