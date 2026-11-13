# These reports are frozen at their completion dates

`costas32_cell3_report.tex` states "three of six cells are closed" and lists
later cells as unstarted. That was the campaign status when Cell 3 completed and
it is **not** rewritten, because the value of an archival report is that it
records what was known when the result was obtained.

`costas32_z1F_f6_report.tex` is frozen likewise.

For live campaign status see `../../README.md` (symmetric programme) and
`../../../report/costas32_report.tex` §14 (whole project). Where they disagree
with these frozen reports, the live ledgers are current and these are historical.

## Erratum: Z=1T, f=4 future-work parameterisation

The frozen `costas32_z1F_f6_report.tex` future-work section describes the
$Z{=}1\mathrm{T}$, $f=4$ branch as having **one** omitted short transposition
length. That count is wrong.

With $f=4$ there are 14 transpositions. In the transpositional branch exactly one
is long, leaving **13** short transpositions drawn from the 15 short lengths.
So **two** short lengths are omitted:

    D_short = {1,...,15} \ {r, s}

The frozen report is not rewritten. The live report and any future solver must
use the two-omission parameterisation. This affects no f=6 result: the f=6
theorem and its census are unaffected.
