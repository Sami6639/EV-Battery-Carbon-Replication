from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil


ROOT = Path(__file__).resolve().parents[2]

PROTOCOL = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL.md"
)

BACKUP = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL_PRE_REFERENCE_LOCK.md"
)

RECEIPT = (
    ROOT
    / "data"
    / "metadata"
    / "MANUSCRIPT_REFERENCE_CONTRACT.json"
)


MARKER = "## REFERENCE CONTRACT ADDENDUM - LOCKED"


ADDENDUM = r"""

## REFERENCE CONTRACT ADDENDUM - LOCKED

This addendum is binding and supersedes any earlier inconsistent
reference-count wording in this protocol.

FINAL REFERENCE-LIST SIZE

- The final References section must contain no fewer than 25 and no more
  than 30 total reference-list entries.
- The 25-30 limit applies to the complete References section, not only to
  journal articles.
- Peer-reviewed scientific journal articles must constitute the dominant
  share of the final reference list.
- Necessary datasets, official reports, software documentation, or other
  provenance records are counted within the same 25-30 total when they
  appear in the References section.

REFERENCE QUALITY

- Scientific literature should be predominantly Web of Science indexed.
- WoS Q1 sources are strongly preferred.
- Sources published in 2020 or later are preferred.
- Older sources may be retained only when seminal, theoretically
  indispensable, methodologically necessary, or required for provenance.
- Reference quantity must never substitute for scientific relevance.

APA FORMAT

- The complete References section must follow APA style using the current
  APA 7th-edition conventions.
- References must be ordered alphabetically by the surname of the first
  author.
- Multiple works by the same author or author group must follow APA
  chronological and same-year ordering rules.
- Bibliographic metadata must be complete and internally consistent.

DOI REQUIREMENT

- Every reference for which a DOI exists must include the exact,
  independently verified DOI.
- DOI strings must never be guessed, inferred, reconstructed, or generated
  from incomplete metadata.
- DOI verification must use an authoritative record such as the publisher,
  Crossref, DOI.org, PubMed, or the official journal record.
- The canonical DOI presentation format is:

  https://doi.org/10.xxxx/xxxxx

- Inconsistent forms such as "doi:", "DOI:", or "http://dx.doi.org/"
  must not be used in the final References section.
- If an authoritative source genuinely has no DOI, no DOI may be fabricated.

CITATION-REFERENCE INTEGRITY

- Every in-text citation must have exactly one corresponding References
  entry.
- Every References entry must be cited in the manuscript text.
- No orphan citation is permitted.
- No orphan reference is permitted.
- Duplicate References entries are prohibited.
- Author names, publication year, article title, journal title, volume,
  issue where applicable, article/page number, and DOI must be verified.
- A citation may only support a claim that the cited source actually
  supports.

FINAL VERIFICATION GATE

Before manuscript completion, the full bibliography must pass a dedicated
reference-integrity audit covering:

1. Total reference count: 25-30 inclusive.
2. APA 7th-edition formatting.
3. Alphabetical ordering.
4. DOI verification.
5. In-text citation to References agreement.
6. References to in-text citation agreement.
7. Duplicate detection.
8. Bibliographic metadata accuracy.
9. WoS/Q1 and publication-year profile review.
10. Claim-to-source support verification.

The manuscript is not reference-ready until this audit passes.
"""


print("=" * 78)
print("MANUSCRIPT REFERENCE CONTRACT LOCK")
print("=" * 78)


if not PROTOCOL.is_file():
    raise RuntimeError(
        "FAIL - MANUSCRIPT_WRITING_PROTOCOL.md not found."
    )


# ============================================================
# 1. BACKUP
# ============================================================

shutil.copy2(
    PROTOCOL,
    BACKUP,
)

print("\nBackup created:")
print(BACKUP.relative_to(ROOT))


# ============================================================
# 2. READ PROTOCOL
# ============================================================

text = PROTOCOL.read_text(
    encoding="utf-8"
)


# ============================================================
# 3. APPEND CONTRACT ONLY ONCE
# ============================================================

if MARKER not in text:

    text = text.rstrip() + "\n" + ADDENDUM.strip() + "\n"

    PROTOCOL.write_text(
        text,
        encoding="utf-8",
    )

    print("\nReference contract appended.")

else:

    print("\nReference contract already present.")
    print("No duplicate addendum created.")


# ============================================================
# 4. RE-READ FINAL PROTOCOL
# ============================================================

text = PROTOCOL.read_text(
    encoding="utf-8"
)


# ============================================================
# 5. VERIFY ORIGINAL 16-SECTION ARCHITECTURE
# ============================================================

sections = sorted(
    set(
        int(x)
        for x in re.findall(
            r"(?m)^(\d{1,2})\.\s+",
            text,
        )
    )
)


# ============================================================
# 6. VERIFY REFERENCE CONTRACT
# ============================================================

checks = {

    "MARKER_SINGLE":
        text.count(MARKER) == 1,

    "TOTAL_25_30":
        (
            "no fewer than 25 and no more"
            in text
            and "than 30 total reference-list entries"
            in text
        ),

    "TOTAL_MEANS_COMPLETE_REFERENCES":
        (
            "complete References section"
            in text
        ),

    "APA_7":
        "APA 7th-edition" in text,

    "ALPHABETICAL":
        (
            "alphabetically by the surname"
            in text
        ),

    "DOI_VERIFIED":
        (
            "independently verified DOI"
            in text
        ),

    "CANONICAL_DOI":
        (
            "https://doi.org/10.xxxx/xxxxx"
            in text
        ),

    "NO_GUESSED_DOI":
        (
            "must never be guessed"
            in text
        ),

    "IN_TEXT_TO_REFERENCE":
        (
            "Every in-text citation"
            in text
        ),

    "REFERENCE_TO_IN_TEXT":
        (
            "Every References entry"
            in text
        ),

    "NO_ORPHANS":
        (
            "No orphan citation"
            in text
            and "No orphan reference"
            in text
        ),

    "NO_DUPLICATES":
        (
            "Duplicate References entries"
            in text
        ),

    "WOS_Q1":
        (
            "Web of Science"
            in text
            and "WoS Q1"
            in text
        ),

    "RECENT_PRIORITY":
        (
            "2020 or later"
            in text
        ),

    "CLAIM_SUPPORT":
        (
            "cited source actually supports"
            in text
        ),

    "FINAL_AUDIT":
        (
            "reference-integrity audit"
            in text
        ),
}


mojibake = any(
    token in text
    for token in [
        "â",
        "Ã",
        "Â",
    ]
)


# ============================================================
# 7. HASH FINAL PROTOCOL
# ============================================================

protocol_bytes = PROTOCOL.read_bytes()

sha256 = hashlib.sha256(
    protocol_bytes
).hexdigest()


# ============================================================
# 8. MACHINE-READABLE RECEIPT
# ============================================================

RECEIPT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

receipt = {

    "contract":
        "MANUSCRIPT_REFERENCE_CONTRACT",

    "status":
        "LOCKED",

    "reference_count": {
        "minimum": 25,
        "maximum": 30,
        "scope":
            "TOTAL_FINAL_REFERENCES_SECTION",
    },

    "format": {
        "style": "APA",
        "edition": 7,
        "ordering":
            "ALPHABETICAL_BY_FIRST_AUTHOR_SURNAME",
    },

    "doi": {
        "required_when_available": True,
        "independent_verification_required": True,
        "canonical_format":
            "https://doi.org/...",
        "guessing_prohibited": True,
    },

    "citation_integrity": {
        "in_text_to_reference": True,
        "reference_to_in_text": True,
        "orphan_citations_prohibited": True,
        "orphan_references_prohibited": True,
        "duplicates_prohibited": True,
    },

    "literature_profile": {
        "wos_preferred": True,
        "q1_strongly_preferred": True,
        "prefer_2020_or_later": True,
        "older_seminal_sources_allowed": True,
    },

    "protocol_file":
        str(
            PROTOCOL.relative_to(ROOT)
        ),

    "protocol_sha256":
        sha256,

    "locked_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "checks":
        checks,
}


RECEIPT.write_text(
    json.dumps(
        receipt,
        indent=2,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# 9. FINAL PASS/FAIL
# ============================================================

hard_pass = (
    sections == list(range(1, 17))
    and all(checks.values())
    and not mojibake
)


print("\nVerification:")
print(
    "sections_16_of_16:",
    sections == list(range(1, 17)),
)

for key, value in checks.items():
    print(
        f"{key}: {value}"
    )

print(
    "mojibake:",
    mojibake,
)

print(
    "protocol_sha256:",
    sha256,
)

print(
    "receipt:",
    RECEIPT.relative_to(ROOT),
)


print("\n" + "=" * 78)

if hard_pass:

    print(
        "MANUSCRIPT REFERENCE CONTRACT LOCK PASS"
    )

    print(
        "TOTAL REFERENCES: 25-30 LOCKED"
    )

    print(
        "APA 7 + ALPHABETICAL ORDER: LOCKED"
    )

    print(
        "VERIFIED DOI REQUIREMENT: LOCKED"
    )

    print(
        "CITATION-REFERENCE INTEGRITY: LOCKED"
    )

else:

    print(
        "MANUSCRIPT REFERENCE CONTRACT LOCK FAIL"
    )

print("=" * 78)