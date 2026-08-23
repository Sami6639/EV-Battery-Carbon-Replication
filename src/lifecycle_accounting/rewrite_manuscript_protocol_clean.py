from pathlib import Path
import hashlib
import re
import shutil


ROOT = Path(__file__).resolve().parents[2]

TARGET = ROOT / "docs" / "MANUSCRIPT_WRITING_PROTOCOL.md"

BACKUP = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL_BEFORE_CANONICAL_REWRITE.md"
)


CONTENT = """# EV_Battery_Carbon_Footprint

# MANUSCRIPT WRITING PROTOCOL - LOCKED

STATUS:

WOS-Q1 / VERY STRONG PUBLICATION POTENTIAL TARGET

BENCHMARK ARTICLE:

Tournament Design as Climate Governance:
Scope 3 Life-Cycle Emissions and Decarbonization
in the 2026 FIFA World Cup

The benchmark article is used only for manuscript architecture, flow,
evidence discipline, table/figure integration, discussion structure,
and conclusion strength.

Its prose and topic-specific content must not be copied.


1. TITLE

The title must:

- represent the entire manuscript accurately;
- foreground the actual scientific novelty;
- be precise, memorable, and attractive to WoS-Q1 editors and reviewers;
- avoid exaggerated first-ever claims;
- reflect the same-BEV continue-versus-immediate-replacement problem;
- preferably signal the trajectory-free/state-conditioned architecture
  when this improves clarity;
- remain fully consistent with the Abstract, research questions,
  findings, discussion, and conclusion.

Several candidate titles must be evaluated before the final title is locked.


2. ABSTRACT

Target length: 140-150 words.

The Abstract must contain, in a compact continuous narrative:

1) scientific problem;
2) research gap;
3) objective;
4) methodological architecture;
5) principal quantitative findings;
6) principal mechanism;
7) scientific implication and contribution.

The Abstract must:

- agree exactly with the title and full manuscript;
- naturally contain all final keywords;
- contain no unsupported novelty claim;
- contain no result that is absent from the manuscript;
- avoid citations unless required by the target journal;
- use natural, human-written academic English;
- avoid robotic or template-like phrasing.


3. KEYWORDS

Keywords must:

- all appear naturally in the Abstract;
- reflect the searchable scientific contribution;
- support bibliometric discoverability;
- avoid unnecessary duplication of title terms where possible;
- be finalized only after the title and Abstract are stable.


4. INTRODUCTION

Target length: 900-1,000 words.

Mandatory order:

1) Strong scientific hook
2) Connection with relevant existing theory or conceptual reasoning
3) State of the scientific problem
4) Explicit literature gap
5) Contribution to the field
6) Research question(s)
7) Scientific and practical importance
8) Scope and boundary of the study
9) Hypotheses or pre-specified analytical propositions

The Introduction must:

- move from the broad scientific problem to the exact research problem;
- explain why existing degradation-aware LCA and retirement studies
  do not resolve the present problem;
- position trajectory-free, state-conditioned, same-BEV
  continue-versus-immediate-replacement lifecycle-GHG set identification
  as the core novelty;
- distinguish headline novelty from supporting contributions;
- avoid premature presentation of detailed results.

Hypotheses may only be presented as ex-ante hypotheses if they can be
traced to pre-result project decisions or preregistration.

No post-result statement may be presented falsely as an ex-ante hypothesis.

Where appropriate, use the terms analytical proposition or pre-specified
expectation instead of hypothesis.


5. LITERATURE REVIEW AND THEORETICAL FRAMEWORK

Target length: 1,200-1,300 words.

Scientific literature priority:

- Web of Science indexed literature;
- preferably Q1 journals;
- preferably 2020 and later;
- DOI verified individually;
- recent literature prioritized.

Older literature is permitted only for:

- foundational theory;
- foundational methodology;
- indispensable seminal evidence.

Official datasets, government reports, standards, and technical
documentation may be used for data provenance even when they are not
WoS-Q1 publications.

The Literature Review must be discussive rather than a bibliography list.

It must be divided into thematic domains, including where scientifically
appropriate:

- EV battery degradation and multidimensional state of health;
- degradation-to-vehicle-energy translation;
- lifecycle GHG and battery replacement;
- battery retirement and first-life decision literature;
- prospective battery-manufacturing decarbonization;
- temporal electricity-carbon accounting;
- residual vehicle service and mobility requirements;
- robust and partial-identification decision architectures.

Each thematic section must:

- synthesize studies;
- compare assumptions and boundaries;
- identify contradictions;
- identify what remains unresolved;
- connect explicitly to the manuscript research question.

Text citations and References must correspond exactly.

Every DOI must be independently verified.

No fabricated citation or DOI is permitted.


6. MATERIALS AND METHODS

Target length: approximately 1,650-1,850 words.

The Methods section must faithfully document the validated scientific
pipeline.

No fashionable or unnecessary method may be added merely to make the
paper appear more sophisticated.

The methodology must cover:

- functional unit and system boundary;
- same-BEV continue versus immediate battery replacement decision;
- degradation-state evidence;
- capacity SOH and resistance architecture;
- 10-ms primary resistance specification;
- 1-s alternative resistance specification;
- FASTSim vehicle-energy translation;
- charging conversion;
- vehicle survival and residual service;
- temporal grid-carbon pathways;
- prospective battery-manufacturing pathways;
- trajectory-free set identification;
- DeltaG accounting;
- identified intervals;
- carbon classification rules;
- structural robustness;
- magnitude and manufacturing break-even defense;
- scientific limitations and claim constraints.

All mathematical expressions must be written in proper LaTeX
mathematical form.

Every important equation must:

- be numbered;
- be referenced in the text;
- define all symbols immediately after the equation;
- use consistent notation throughout the manuscript.

No undefined mathematical symbol is permitted.

No proportional resistance-percent to energy-percent shortcut is permitted.

No unsupported degradation trajectory is permitted.


7. TABLES AND FIGURES

Only scientifically necessary tables and figures are allowed.

Every table and figure must:

- be publication quality;
- have a complete title or caption;
- define all abbreviations;
- state units;
- state evidence/source where relevant;
- distinguish primary, robustness, and conditional/extreme evidence;
- be explicitly referenced in the manuscript text;
- be interpreted immediately after introduction in the text.

No table or figure may merely duplicate prose.

Main-text figures should communicate scientific mechanisms rather than
decorative information.

Additional diagnostics may be placed in Appendices or Supplementary Material.


8. RESULTS

Target length: approximately 1,150-1,350 words.

Results must:

- answer the research questions directly;
- report quantitative evidence before interpretation;
- separate primary results from robustness results;
- report identified intervals rather than only point estimates;
- explicitly report the ROBUST CONTINUE result within its supported domain;
- present temporal context modulation;
- present mechanism decomposition;
- report 10-ms versus 1-s structural robustness;
- report grid, LRMER, regional, context, and extreme robustness;
- disclose conditional/extreme evidence separately.

Results must not:

- overclaim engineering feasibility;
- hide the aged-state power limitation;
- imply that Xu 2022 robustness was completed;
- imply that recycling-credit sensitivity was completed;
- infer time-to-state;
- perform or imply replacement-time optimization.


9. DISCUSSION

Target length: approximately 1,400-1,550 words.

The Discussion must be thematic.

Each major theme should integrate:

1) empirical/result finding;
2) research question, hypothesis, or analytical proposition;
3) theoretical interpretation;
4) mechanism;
5) comparison with prior literature;
6) scientific implication;
7) managerial, policy, or engineering implication where justified.

Headline discussion themes should prioritize:

- trajectory-free state-conditioned carbon decision;
- manufacturing-burden versus operational-saving asymmetry;
- temporal decarbonization and persistence of the decision;
- why multidimensional battery health remains scientifically relevant
  even when resistance does not reverse the carbon classification;
- robustness and partial-identification implications.

Dual-state resistance and identification leverage are supporting
contributions and must not be forced into headline claims.

Limitations must explicitly include:

- aged-state power capability is not state-resolved;
- Xu 2022 was not numerically implemented in P16;
- recycling-credit sensitivity was not numerically implemented;
- no degradation trajectory or time-to-state inference was used.


10. CONCLUSION

Target length: 600-900 words.

Preferred working target: approximately 650-800 words.

The Conclusion must:

- answer the Primary RQ clearly;
- synthesize the principal quantitative finding;
- explain the headline mechanism;
- summarize temporal and structural robustness;
- state the scientific contribution;
- state theoretical and methodological contributions;
- explain practical implications only within supported bounds;
- state central limitations;
- identify future research directions;
- end with a strong conceptual closing statement.

The final paragraph must be memorable but scientifically disciplined.

No new result, unsupported claim, or new citation-dependent argument may
be introduced in the Conclusion.


11. DATA AND CODE AVAILABILITY

Immediately after the Conclusion or Declarations, include a reproducibility
statement.

A versioned GitHub repository must be created when the final replication
package is frozen.

The repository should contain, subject to third-party licences:

- executable source code;
- environment and dependency files;
- processed reproducible data;
- source lineage and provenance files;
- machine-readable results;
- table and figure generation scripts;
- final integrity manifests;
- README with reproduction instructions.

Third-party raw data must not be redistributed when licences prohibit it.

The final manuscript must provide the verified GitHub URL.


12. REFERENCES

Scientific-literature preference:

WoS Q1, recent, preferably 2020 and later.

Every reference must be independently verified.

DOI must be verified where one exists.

Text citation and reference-list agreement must be exact.

No orphan reference is permitted.

No missing reference is permitted.

No hallucinated DOI is permitted.

No citation may be used to support a claim that the cited source does not
actually support.


13. STYLE

Language:

Natural, human, academically sophisticated English.

Avoid:

- robotic sentence patterns;
- repetitive paragraph endings;
- excessive use of "This study..." openings;
- mechanical transition phrases;
- inflated novelty language;
- promotional wording;
- unnecessary jargon;
- repetitive conclusion sentences.

Paragraphs must have logical internal progression and independent endings.

The manuscript must resemble a strong human-written WoS-Q1 article,
not an AI-generated template.


14. TOTAL LENGTH

Target main-text length:

7,500-8,000 words.

Operational section targets:

Abstract: 140-150 words.
Introduction: 900-1,000 words.
Literature Review and Theoretical Framework: 1,200-1,300 words.
Materials and Methods: approximately 1,650-1,850 words.
Results: approximately 1,150-1,350 words.
Discussion: approximately 1,400-1,550 words.
Conclusion: 600-900 words.

References, Appendices, supplementary material, tables, figures, captions,
and Data/Code Availability are excluded from this operational main-text
target unless the target journal specifies otherwise.

Appendices are permitted where they improve transparency without
interrupting the main scientific narrative.


15. HARD CLAIM GATES

PROHIBITED CLAIMS:

- first degradation-aware EV LCA;
- first carbon-optimal battery retirement;
- resistance changes the carbon classification;
- complete engineering replacement recommendation;
- recycling assumptions cannot affect the result;
- inferred degradation time-to-state;
- hidden replacement optimization;
- unsupported aged-state power feasibility.

Headline novelty must remain:

TRAJECTORY-FREE, STATE-CONDITIONED,
SAME-BEV CONTINUE-VERSUS-IMMEDIATE-REPLACEMENT
LIFECYCLE-GHG SET IDENTIFICATION.

Headline mechanism must remain:

REPLACEMENT-BATTERY MANUFACTURING BURDEN
VERSUS ADMISSIBLE DEGRADATION-RELATED
OPERATIONAL-CARBON SAVING ASYMMETRY.


16. BENCHMARK-ARCHITECTURE RULE

Use the uploaded FIFA World Cup manuscript as a permanent architecture
benchmark for:

- hook strength;
- theory connection;
- gap positioning;
- contribution architecture;
- RQ placement;
- hypothesis/proposition placement;
- thematic literature review;
- numbered equations;
- table and figure integration;
- Results-to-Discussion transition;
- thematic Discussion;
- limitation discipline;
- strong Conclusion;
- reproducibility statement.

Do not copy its prose or topic-specific content.
"""


print("=" * 78)
print("CANONICAL MANUSCRIPT PROTOCOL REWRITE")
print("=" * 78)


# ============================================================
# 1. BACKUP CURRENT VERSION
# ============================================================

if TARGET.exists():
    shutil.copy2(
        TARGET,
        BACKUP,
    )

    print("\nBackup:")
    print(BACKUP.relative_to(ROOT))


# ============================================================
# 2. WRITE CLEAN CANONICAL VERSION
# ============================================================

TARGET.write_text(
    CONTENT,
    encoding="utf-8",
)


# ============================================================
# 3. VERIFY
# ============================================================

text = TARGET.read_text(
    encoding="utf-8"
)

sections = sorted(
    set(
        int(x)
        for x in re.findall(
            r"(?m)^(\d{1,2})\.\s+",
            text,
        )
    )
)

escaped = any(
    token in text
    for token in [
        "\\#",
        "\\_",
        "\\-",
        "\\.",
    ]
)

mojibake = any(
    token in text
    for token in [
        "â",
        "Ã",
        "Â",
    ]
)

required = {
    "VERY_STRONG":
        "VERY STRONG PUBLICATION POTENTIAL TARGET" in text,

    "ABSTRACT":
        "140-150 words" in text,

    "INTRO":
        "900-1,000 words" in text,

    "LITERATURE":
        "1,200-1,300 words" in text,

    "CONCLUSION":
        "600-900 words" in text,

    "TOTAL":
        "7,500-8,000 words" in text,

    "GITHUB":
        "verified GitHub URL" in text,

    "DOI":
        "DOI" in text,

    "LATEX":
        "LaTeX" in text,

    "HEADLINE_NOVELTY":
        (
            "TRAJECTORY-FREE, STATE-CONDITIONED"
            in text
            and "SAME-BEV" in text
        ),

    "HEADLINE_MECHANISM":
        (
            "REPLACEMENT-BATTERY MANUFACTURING BURDEN"
            in text
            and "OPERATIONAL-CARBON SAVING ASYMMETRY"
            in text
        ),
}


hard_pass = (
    sections == list(range(1, 17))
    and not escaped
    and not mojibake
    and all(required.values())
)


# ============================================================
# 4. SHA-256
# ============================================================

digest = hashlib.sha256(
    TARGET.read_bytes()
).hexdigest()


# ============================================================
# 5. DISPLAY
# ============================================================

print("\nVerification:")

print(
    "sections:",
    sections,
)

print(
    "sections_16_of_16:",
    sections == list(range(1, 17)),
)

print(
    "escaped_markdown:",
    escaped,
)

print(
    "mojibake:",
    mojibake,
)

for key, value in required.items():
    print(
        f"{key}: {value}"
    )

print(
    "bytes:",
    TARGET.stat().st_size,
)

print(
    "lines:",
    len(text.splitlines()),
)

print(
    "sha256:",
    digest,
)


print("\n" + "=" * 78)

if hard_pass:

    print(
        "MANUSCRIPT WRITING PROTOCOL CANONICAL REWRITE PASS"
    )

    print(
        "SECTIONS: 16/16"
    )

    print(
        "UTF-8 / MARKDOWN: CLEAN"
    )

    print(
        "WORD-LENGTH CONTRACT: LOCKED"
    )

    print(
        "Q1 / DOI / LATEX / GITHUB CONTRACT: LOCKED"
    )

    print(
        "HEADLINE NOVELTY / MECHANISM: LOCKED"
    )

else:

    print(
        "MANUSCRIPT WRITING PROTOCOL CANONICAL REWRITE FAIL"
    )

print("=" * 78)