# Licensing

| Material | Licence | Files |
|---|---|---|
| Source code, build and job scripts | Apache License 2.0 (`LICENSE`) | `*.c`, `*.cpp`, `*.h`, `*.hpp`, `*.py`, `*.sh`, `*.pbs`, `*.lean`, `Makefile`, and other program text |
| Reports, papers, documentation | CC BY 4.0 (`LICENSE-CC-BY-4.0.md`) | `*.tex`, `*.pdf`, `*.md`, `*.bib`, and the proceedings and reports generally |
| Data produced by the project | CC BY 4.0 | results, logs, summaries and catalogues generated here (`*.json`, `*.jsonl`, `*.txt`, `*.csv`, `*.log`) |

Machine-readable form: `REUSE.toml`. The repository is compliant with version 3.3 of the REUSE
Specification (`reuse lint`). Full licence texts are in `LICENSES/`.

Archives holding both code and data (the campaign bundles in `symmetric/z1/closed_cells/` and the
independent workstream's archives in `mining/independent/`) are licensed `Apache-2.0 AND CC-BY-4.0`: the
code inside under Apache 2.0, the data and documents under CC BY 4.0. Compressed result data and logs,
checksum manifests, `VERSION` and `NOTICE` are under CC BY 4.0; `lean-toolchain` is under Apache 2.0.

**Third-party material.** Material by others that is cited or reproduced here keeps its original terms.
This includes published Costas-array data used as inputs (for example the order-28 and order-29 census
representatives and the OEIS counts), and the bibliographic data in `literature/`. Archives in
`mining/independent/` are the project's own independent implementation and fall under the terms above.

**Provenance note.** Licence notices are declared at repository level rather than in file headers,
because the campaign sources (for example `symmetric/campaign32/inv32.cpp`) are bound by SHA-256 hash to
completed runs, and any edit, even to a comment, would break that binding.

**Errata.** Reports of errors, omissions and overlooked prior work are welcome: please write to the
corresponding author, Charles Gretton, at charles.gretton@anu.edu.au. Every report that leads to a
correction will be acknowledged in the errata and in any revised edition, cited as a private
communication; where the point was already made in a publication that appeared before the report's
publication date, that publication will be cited as well.
