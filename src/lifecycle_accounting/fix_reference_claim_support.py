from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]

PROTOCOL = ROOT / "docs" / "MANUSCRIPT_WRITING_PROTOCOL.md"

BACKUP = (
    ROOT
    / "docs"
    / "MANUSCRIPT_WRITING_PROTOCOL_PRE_CLAIM_SUPPORT_FIX.md"
)

REQUIRED_SENTENCE = (
    "Every claim supported by a citation must be supported by evidence "
    "that the cited source actually supports."
)


print("=" * 78)
print("REFERENCE CLAIM-SUPPORT FIX")
print("=" * 78)


if not PROTOCOL.is_file():
    raise RuntimeError(
        "FAIL - MANUSCRIPT_WRITING_PROTOCOL.md not found."
    )


shutil.copy2(
    PROTOCOL,
    BACKUP,
)

print("\nBackup created:")
print(BACKUP.relative_to(ROOT))


text = PROTOCOL.read_text(
    encoding="utf-8"
)


if "cited source actually supports" not in text:

    text = (
        text.rstrip()
        + "\n\n"
        + REQUIRED_SENTENCE
        + "\n"
    )

    PROTOCOL.write_text(
        text,
        encoding="utf-8",
    )

    print("\nRequired claim-support rule added.")

else:

    print("\nClaim-support rule already present.")


final_text = PROTOCOL.read_text(
    encoding="utf-8"
)


passed = (
    "cited source actually supports"
    in final_text
)


print(
    "\nCLAIM_SUPPORT:",
    passed,
)


print("\n" + "=" * 78)

if passed:
    print("REFERENCE CLAIM-SUPPORT FIX PASS")
else:
    print("REFERENCE CLAIM-SUPPORT FIX FAIL")

print("=" * 78)