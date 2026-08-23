from pathlib import Path
import shutil
import re


ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL.md"
)

BACKUP = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL_PRE_CLEAN_BACKUP.md"
)


print("=" * 78)
print("MANUSCRIPT WRITING PROTOCOL CLEANUP")
print("=" * 78)


if not FILE.is_file():
    raise RuntimeError(
        "FAIL — MANUSCRIPT_WRITING_PROTOCOL.md not found."
    )


# ============================================================
# 1. BACKUP ORIGINAL FILE
# ============================================================

shutil.copy2(
    FILE,
    BACKUP,
)

print("\nBackup created:")
print(BACKUP.relative_to(ROOT))


# ============================================================
# 2. READ UTF-8
# ============================================================

text = FILE.read_text(
    encoding="utf-8"
)


# ============================================================
# 3. REMOVE ARTIFICIAL LEADING BACKSLASHES
#
# Examples:
# \# TITLE  -> # TITLE
# \1. TITLE -> 1. TITLE
# \======== -> ========
#
# Only beginning-of-line backslashes are removed here.
# ============================================================

lines = []

for line in text.splitlines():

    if line.startswith("\\"):
        line = line[1:]

    lines.append(line)


text = "\n".join(lines) + "\n"


# ============================================================
# 4. REMOVE ARTIFICIAL MARKDOWN ESCAPES
#
# Protocol is plain Markdown/text.
# These escapes are not scientifically meaningful.
# ============================================================

replacements = {
    "\\#": "#",
    "\\_": "_",
    "\\-": "-",
    "\\*": "*",
    "\\(": "(",
    "\\)": ")",
    "\\[": "[",
    "\\]": "]",
}

for old, new in replacements.items():
    text = text.replace(
        old,
        new,
    )


# ============================================================
# 5. WRITE CLEAN UTF-8
# ============================================================

FILE.write_text(
    text,
    encoding="utf-8",
)


# ============================================================
# 6. VERIFY SECTIONS
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


escaped_remaining = any(
    token in text
    for token in [
        "\\#",
        "\\_",
        "\\-",
    ]
)


mojibake = any(
    ch in text
    for ch in [
        "â",
        "Ã",
        "Â",
    ]
)


print("\nVerification:")

print(
    "sections:",
    sections,
)

print(
    "all_1_to_16:",
    sections == list(range(1, 17)),
)

print(
    "escaped_markdown_remaining:",
    escaped_remaining,
)

print(
    "mojibake_present:",
    mojibake,
)

print(
    "bytes_after_cleanup:",
    FILE.stat().st_size,
)


print("\nFirst 5 cleaned lines:")

for line in text.splitlines()[:5]:
    print(repr(line))


print("\n" + "=" * 78)

if (
    sections == list(range(1, 17))
    and not escaped_remaining
    and not mojibake
):
    print(
        "MANUSCRIPT PROTOCOL CLEANUP PASS"
    )
else:
    print(
        "MANUSCRIPT PROTOCOL CLEANUP WITH CHECK REQUIRED"
    )

print("=" * 78)