# Research Manuscript

`main.tex` is the publication-oriented, Overleaf-ready paper. It summarizes the living notebook, configurations, generated findings, and preregistration without replacing them.

## Overleaf

1. Upload `main.tex` and `references.bib` to a blank Overleaf project.
2. Keep the default `article` class for portability.
3. To use the referenced template, upload `olplainarticle.cls` and use the document-class line shown at the top of `main.tex`.
4. Select pdfLaTeX and BibTeX.

## Local build

```bash
cd research/manuscript
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Maintenance rule

Update empirical facts in the pipeline, configuration, or findings layer first. Then update the manuscript narrative and version date. Do not introduce a result that cannot be reconstructed from the repository.
