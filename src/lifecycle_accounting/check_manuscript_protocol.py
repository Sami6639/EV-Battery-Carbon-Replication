from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL.md"
)


print("=" * 78)
print("MANUSCRIPT WRITING PROTOCOL INTEGRITY CHECK")
print("=" * 78)


if not FILE.is_file():
    raise RuntimeError(
        "FAIL — MANUSCRIPT_WRITING_PROTOCOL.md not found."
    )


text = FILE.read_text(
    encoding="utf-8"
)


# ============================================================
# 1. BASIC FILE IDENTITY
# ============================================================

sections = sorted(
    set(
        int(x)
        for x in re.findall(
            r"(?m)^\s*(\d{1,2})\.\s+",
            text,
        )
    )
)


print("\nFILE")
print("exists:", FILE.exists())
print("bytes:", FILE.stat().st_size)
print("lines:", len(text.splitlines()))

print("\nSECTIONS")
print("found:", sections)
print(
    "all 1-16 present:",
    sections == list(range(1, 17)),
)


# ============================================================
# 2. ENCODING / MARKDOWN CLEANLINESS
# ============================================================

mojibake = any(
    ch in text
    for ch in [
        "\u00e2",  # â
        "\u00c3",  # Ã
        "\u00c2",  # Â
    ]
)

escaped_markdown = any(
    token in text
    for token in [
        "\\#",
        "\\_",
        "\\-",
    ]
)


print("\nENCODING")
print("mojibake_in_file:", mojibake)
print("escaped_markdown_in_file:", escaped_markdown)


# ============================================================
# 3. CORE SCIENTIFIC / WRITING RULES
# ============================================================

checks = {
    "VERY_STRONG_STATUS":
        (
            "VERY STRONG PUBLICATION POTENTIAL TARGET"
            in text
        ),

    "ABSTRACT_140_150":
        bool(
            re.search(
                r"140[\u2013-]150",
                text,
            )
        ),

    "INTRO_900_1000":
        bool(
            re.search(
                r"900[\u2013-]1,?000",
                text,
            )
        ),

    "LITERATURE_1200_1300":
        bool(
            re.search(
                r"1,?200[\u2013-]1,?300",
                text,
            )
        ),

    "CONCLUSION_600_900":
        bool(
            re.search(
                r"600[\u2013-]900",
                text,
            )
        ),

    "TOTAL_7500_8000":
        bool(
            re.search(
                r"7,?500[\u2013-]8,?000",
                text,
            )
        ),

    "GITHUB_RULE":
        (
            "GitHub"
            in text
        ),

    "DOI_RULE":
        (
            "DOI"
            in text
        ),

    "LATEX_RULE":
        (
            "LaTeX"
            in text
        ),

    "Q1_REFERENCE_RULE":
        (
            "WoS Q1"
            in text
            or "WOS-Q1"
            in text
        ),

    "HEADLINE_NOVELTY":
        (
            "TRAJECTORY-FREE"
            in text
            and "STATE-CONDITIONED"
            in text
            and "SAME-BEV"
            in text
        ),

    "HEADLINE_MECHANISM":
        (
            "REPLACEMENT-BATTERY MANUFACTURING BURDEN"
            in text
            and "OPERATIONAL-CARBON SAVING"
            in text
        ),
}


print("\nREQUIRED RULES")

for key, value in checks.items():
    print(f"{key}: {value}")


# ============================================================
# 4. FINAL HARD GATE
# ============================================================

hard_pass = (
    sections == list(range(1, 17))
    and not mojibake
    and not escaped_markdown
    and all(checks.values())
)


print("\nFIRST 5 STORED LINES")

for line in text.splitlines()[:5]:
    print(repr(line))


print("\nLAST 5 STORED LINES")

for line in text.splitlines()[-5:]:
    print(repr(line))


print("\n" + "=" * 78)

if hard_pass:

    print(
        "MANUSCRIPT WRITING PROTOCOL INTEGRITY PASS"
    )

    print(
        "SECTIONS: 16/16"
    )

    print(
        "UTF-8 CONTENT: CLEAN"
    )

    print(
        "WORD-LENGTH RULES: PRESENT"
    )

    print(
        "Q1 / DOI / LATEX / GITHUB RULES: PRESENT"
    )

    print(
        "HEADLINE NOVELTY / MECHANISM: PRESENT"
    )

else:

    print(
        "MANUSCRIPT WRITING PROTOCOL INTEGRITY FAIL"
    )

    print(
        "DO NOT LOCK UNTIL FAILED CHECKS ARE CORRECTED"
    )

print("=" * 78)