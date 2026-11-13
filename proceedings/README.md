# Proceedings: Costas Arrays of Order 32

Eight self-contained papers, one per strand of the investigation, assembled from the consolidated
report (`report/costas32_report.tex`) and the symmetric-campaign report (revision 13).

Rebuild: `python3 build.py && python3 assemble.py && python3 fixrefs.py && python3 revise.py && pdflatex costas32_proceedings.tex` (three times). `revise.py` applies the review revisions and appends the conclusions chapter (`conclusions.tex`).
`build.py` extracts shared preliminaries and splits the rungs subsection by content markers;
`assemble.py` builds each paper with per-paper label, reference and citation prefixes and its own reference list;
`fixrefs.py` rewords references that point outside a paper and applies the editorial review fixes. The shared notation table and glossary are in `shared_notation.tex`, included by `\input`. Front matter for each paper is in `front.json`.
The scripts read the symmetric report from `/tmp/texbuild/`; adjust `SYM` in both scripts to rebuild elsewhere.

Extraction notes. Paper 8 is extracted from the symmetric report by section heading, so edits to that
report cannot misalign it. Papers 1-7 are still extracted from `report/costas32_report.tex` by line
range: an edit to that report must preserve its line count, or the ranges in `build.py` and
`assemble.py` must be updated. `projblock.py` is idempotent and skips a source that already documents
projection blocking.
