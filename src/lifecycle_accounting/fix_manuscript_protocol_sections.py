from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[2]

FILE = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL.md"
)

BACKUP = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL_PRE_SECTION_FIX.md"
)


print("=" * 78)
print("MANUSCRIPT PROTOCOL SECTION-NUMBER FIX")
print("=" * 78)


if not FILE.is_file():
    raise RuntimeError(
        "FAIL — MANUSCRIPT_WRITING_PROTOCOL.md not found."
    )


# ============================================================
# 1. BACKUP CURRENT CLEAN VERSION
# ============================================================

shutil.copy2(
    FILE,
    BACKUP,
)

print("\nBackup created:")
print(BACKUP.relative_to(ROOT))


# ============================================================
# 2. READ
# ============================================================

text = FILE.read_text(
    encoding="utf-8"
)


# ============================================================
# 3. NORMALIZE NUMBERED SECTION HEADINGS
#
# Examples:
#
# 1\. TITLE      -> 1. TITLE
# \1\. TITLE     -> 1. TITLE
#
# Only numbered heading lines are touched.
# ============================================================

text = re.sub(
    r"(?m)^(\s*)\\?(\d{1,2})\\\.\s+",
    lambda m: (
        f"{m.group(1)}"
        f"{m.group(2)}. "
    ),
    text,
)


# Also handle unlikely form:
#
# 1\.TITLE -> 1. TITLE
#
text = re.sub(
    r"(?m)^(\s*)(\d{1,2})\\\.(?=\S)",
    lambda m: (
        f"{m.group(1)}"
        f"{m.group(2)}. "
    ),
    text,
)


# ============================================================
# 4. WRITE
# ============================================================

FILE.write_text(
    text,
    encoding="utf-8",
)


# ============================================================
# 5. VERIFY EXACT 1–16 SECTIONS
# ============================================================

matches = re.findall(
    r"(?m)^\s*(\d{1,2})\.\s+(.+?)\s*$",
    text,
)

sections = [
    int(number)
    for number, title in matches
    if 1 <= int(number) <= 16
]

unique_sections = sorted(
    set(sections)
)


print("\nDetected numbered headings:")

for number, title in matches:
    n = int(number)

    if 1 <= n <= 16:
        print(
            f"{n}. {title}"
        )


print("\nVerification:")

print(
    "sections:",
    unique_sections,
)

print(
    "section_count:",
    len(unique_sections),
)

print(
    "all_1_to_16:",
    unique_sections == list(range(1, 17)),
)


remaining_escaped_section_periods = re.findall(
    r"(?m)^\s*\\?\d{1,2}\\\.",
    text,
)

print(
    "remaining_escaped_section_periods:",
    len(
        remaining_escaped_section_periods
    ),
)


print("\n" + "=" * 78)

if (
    unique_sections == list(range(1, 17))
    and len(
        remaining_escaped_section_periods
    ) == 0
):

    print(
        "MANUSCRIPT PROTOCOL SECTION FIX PASS"
    )

    print(
        "SECTIONS: 16/16"
    )

else:

    print(
        "MANUSCRIPT PROTOCOL SECTION FIX FAIL"
    )

print("=" * 78)