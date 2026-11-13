import re
p='costas32_proceedings.tex'; s=open(p).read()
W=lambda t: re.escape(t).replace('\\ ','\\s+')   # tolerate line breaks between words
fixes=[
 (r"Section~\\ref\{p1-sec:coords\} records the computation\.", "The computation is recorded in the project's consolidated report."),
 (r"Section~\\ref\{p1-sec:heredity\} shows", "Paper~3 shows"),
 (r"see Section~\\ref\{p1-sec:ladder\}\.", "see Papers~2 and~3."),
 (r"This\s+figure\s+is\s+used\s+in\s+Section~\\ref\{p1-sec:sat\}\s+to\s+calibrate", "The project's consolidated report uses this figure to calibrate"),
 (r"refuted in Section~\\ref\{p1-sec:structural\}", "refuted in the project's consolidated report"),
 (r"examined\s+in\s+Section~\\ref\{p1-sec:structural\}", "examined in the project's consolidated report"),
 (r"consistent\s+with\s+Theorem~\\ref\{p1-thm:heredity\}:", "consistent with the heredity measurement of Paper~3:"),
 (r"\(Theorem~\\ref\{p1-thm:rungs\}\)", "(Paper~2)"),
 (r"This\s+is\s+the\s+same\s+distinction\s+drawn\s+in\s+Remark~\\ref\{p4-rem:tierb\},\s+and\s+the\s+paper\s+should\s+state\s+it\s+in\s+one\s+line\s+rather\s+than\s+let\s+the\s+presence\s+of\s+a\s+Lean\s+certificate\s+imply\s+more\s+than\s+it\s+delivers\.",
  "The presence of a Lean certificate should not be read as implying more than it delivers."),
 (r"This\s+was\s+identified\s+above\s+as\s+the\s+cheapest\s+real\s+certificate\s+available\s+and\s+the\s+one\s+underwriting\s+the\s+quantifier\s+in\s+Theorem~\\ref\{p4-thm:rung3census\}\.",
  "The census underwrites the universal quantifier in the order-29 deletion-minor theorem of Paper~3, and certifying it is the cheapest real certificate available to this investigation."),
 (r"Theorem~\\ref\{p4-thm:rung3census\}'s\s+universal\s+quantifier", "that theorem's universal quantifier"),
 (r"so\s+Observation~\\ref\{p6-obs:uniformity\}\s+does\s+not\s+apply\s+to\s+it\.", "so the uniformity caveat recorded in the project's consolidated report does not apply to it."),
 (r"\(Proposition~\\ref\{p6-prop:polydual\}\)", "(Paper~1, Proposition~\\\\ref{p1-prop:polydual})"),
 (r"The\s+catalogue\s+generator\s+of\s+Section~\\ref\{p6-sec:catalogue\}", "The catalogue generator of Paper~2"),
 (r"the\s+methods\s+of\s+Sections~\\ref\{p6-sec:structural\}--\\ref\{p6-sec:coords\}\s+failed", "the structural methods examined in the project's consolidated report failed"),
 (r"The\s+mod-64\s+injectivity\s+noted\s+in\s+Section~\\ref\{p7-sec:2adic\}", "The mod-64 injectivity of the 2-adic tower, noted in the project's consolidated report,"),
 (r"\(Algorithm~\\ref\{p8-alg:enum\},\s+run\s+to\s+completion\)", "(run to completion)"),
 (r"in\s+the\s+order\s+of\s+Algorithm~\\ref\{p8-alg:enum\}", "in the order of that enumeration"),
 (r"Script\s+and\s+output\s+digests\s+are\s+in\s+Appendix~\\ref\{p8-app:digests\}\.", "Script and output digests are in the released software archive."),
 (r"\(Section~\\ref\{p8-app:manifests\}\)", "(see the released manifests)"),
 (r"\(Section~\\ref\{p8-sec:campaign\}\)", "(the first stage of the campaign)"),
]
for pat,rep in fixes:
    s2,n=re.subn(pat,rep,s)
    if n==0: print("NO MATCH:",pat[:70])
    s=s2
# "this report" -> per paper
parts=re.split(r'(?=\\chapter\{)',s)
for i,part in enumerate(parts):
    if '\\chapter{An Independent SAT Verification' in part: parts[i]=part.replace('this report','this paper').replace('This report','This paper')
    elif part.startswith('\\chapter{'): parts[i]=part.replace('this report','this investigation').replace('This report','This investigation')
s=''.join(parts)

lit=[
 ("\\[\nC_{31} = (", "{\\footnotesize\\[\nC_{31} = ("),
 ("16,23,17),\n\\]\nand the order-32 optimum", "16,23,17),\n\\]}\nand the order-32 optimum"),
 ("\\[\nN_{32}' = (", "{\\footnotesize\\[\nN_{32}' = ("),
 ("16,23,17),\n\\]\nwhich is $C_{31}$", "16,23,17),\n\\]}\nwhich is $C_{31}$"),
 ("\\[\n\\text{Welch-30 (algebraic)}\n\\;\\xrightarrow{\\ \\text{free adjunction}\\ }\\;\nC_{31} \\text{ (unique derived order-31 orbit)}\n\\;\\xrightarrow{\\ \\text{minimum-cost adjunction}\\ }\\;\nN_{32}\\ (\\text{defect }2).\n\\]",
  "\\[\n\\begin{aligned}\n&\\text{Welch-30 (algebraic)}\\;\\xrightarrow{\\ \\text{free adjunction}\\ }\\;C_{31}\\text{ (unique derived order-31 orbit)}\\\\\n&\\qquad\\xrightarrow{\\ \\text{minimum-cost adjunction}\\ }\\;N_{32}\\ (\\text{defect }2).\n\\end{aligned}\n\\]"),
 ("\\begin{center}\n\\begin{tabular}{@{}ll@{}}\n\\toprule\nformer obligation", "\\begin{center}\\footnotesize\n\\begin{tabular}{@{}ll@{}}\n\\toprule\nformer obligation"),
]
for a,b in lit:
    if a not in s: print("LITERAL NOT FOUND:", a[:50].replace(chr(10),' '))
    s=s.replace(a,b,1)

review=[
 (r"The\s+work\s+package\s+above\s+seeks\s+to\s+resolve\s+the\s+ambiguous\s+\$G_3\$/\$G_4\$/Taylor/Lempel\s+designations\s+into\s+exact\s+source-defined\s+equations\s+before\s+specialising\s+each\s+to\s+\$\\F_\{32\}\$\.\s+That\s+resolution\s+is\s+worth\s+having,\s+but\s+the\s+question\s+it\s+exists\s+to\s+answer",
  r"The literature's $G_3$/$G_4$/Taylor/Lempel designations are not used consistently. Resolving them into exact source-defined equations before specialising each to $\\F_{32}$ would be worth having, but the question that resolution exists to answer"),
 (r"\\begin\{remark\}\[Column convention, corrected\].*?\\end\{remark\}",
  r"\\begin{remark}[Measured placements]\n\\label{p3-rem:colconv}\nThe placements column records core placements measured in the runs, not a priori counts of the\nconfiguration space. Re-running the rungs from a single binary reproduced the recorded outcomes\nexactly: zero Costas arrays, with minimum defect 4 at $k=3$.\n\\end{remark}"),
 (r"single\s+most\s+consequential\s+measurement\s+in\s+the\s+report", "single most consequential measurement in this investigation"),
 (r"\\section\{Order-29 census: the first Tier B certificate\}", r"\\section{A machine-checked certificate in Lean}"),
 (r"the\s+question\s+the\s+report\s+addresses,\s+why\s+it\s+is\s+of\s+interest,\s+and\s+how\s+the\s+report\s+is\s+organised", "the question this paper addresses, why it is of interest, and how the paper is organised"),
]
for pat,rep in review:
    s2,n=re.subn(pat,rep,s,count=1,flags=re.S)
    if n==0: print("REVIEW NO MATCH:",pat[:60])
    s=s2
parts=re.split(r'(?=\\chapter\{)',s)
for i,part in enumerate(parts):
    if part.startswith('\\chapter{Telescoping-Sum'):
        part=part.replace("F3$'$","Stage~2"); part=re.sub(r'\bF3\b','Stage~1',part); parts[i]=part
    if part.startswith('\\chapter{An Independent SAT Verification'):
        parts[i]=re.sub(r'\bthe report\b','the paper',part)
s=''.join(parts)
s=re.sub(r'^\\part\{[^}]*\}\n','',s,flags=re.M)
open(p,'w').write(s); print("fixes applied")
