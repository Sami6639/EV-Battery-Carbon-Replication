"""P10.5 staged-acquisition checks only; no scientific values are inspected."""

import csv
import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "metadata" / "SOURCE_MANIFEST.csv"
CORE_IDS = {"SRC_LUH_2024", "SRC_SCHREIBER_2025", "SRC_TUM_ID3"}
P105_IDS = CORE_IDS | {"SRC_SEVDARI_2023"}
LIMIT_BYTES = 2 * 1024**3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def metadata(source_id: str) -> dict:
    path = ROOT / "data" / "metadata" / f"{source_id}.yaml"
    assert path.is_file()
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_core_selection_records_are_frozen_and_complete() -> None:
    headings = {
        "### Scientific Role",
        "### Full Dataset Size",
        "### Full File Count",
        "### Required Variables",
        "### Selected Files",
        "### Excluded File Categories",
        "### Reason for Exclusion",
        "### Expected Coverage",
        "### Remaining Limitations",
        "### Is Full Dataset Required Later? YES / NO / CONDITIONAL",
    }
    for source_id in CORE_IDS:
        record = ROOT / "data" / "metadata" / f"{source_id}_SELECTION.md"
        assert record.is_file()
        text = record.read_text(encoding="utf-8")
        assert all(heading in text for heading in headings)


def test_staged_files_exist_in_source_directories_and_match_metadata() -> None:
    for source_id in P105_IDS:
        source_metadata = metadata(source_id)
        assert source_metadata["source_id"] == source_id
        assert source_metadata["transformation_status"] == "RAW_UNMODIFIED"
        assert source_metadata["files"]
        source_root = ROOT / "data" / "raw" / source_id
        for record in source_metadata["files"]:
            raw_file = ROOT / record["raw_relative_path"]
            assert raw_file.is_file()
            assert raw_file.is_relative_to(source_root)
            assert raw_file.name == record["original_filename"]
            assert raw_file.stat().st_size == record["file_size_bytes"] > 0
            assert sha256(raw_file) == record["sha256"]
            assert record["transformation_status"] == "RAW_UNMODIFIED"


def test_p105_new_downloads_stay_under_controlled_limit() -> None:
    files = [
        ROOT / record["raw_relative_path"]
        for source_id in P105_IDS
        for record in metadata(source_id)["files"]
        if record.get("acquisition_stage", "P10.5") == "P10.5"
    ]
    assert len(files) == 29
    assert sum(path.stat().st_size for path in files) == 1_082_475_875
    assert sum(path.stat().st_size for path in files) <= LIMIT_BYTES
    assert all(path.stat().st_size < LIMIT_BYTES for path in files)


def test_manifest_staged_statuses_are_unique_and_valid() -> None:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["source_id"] for row in rows]
    assert len(ids) == len(set(ids))
    by_id = {row["source_id"]: row for row in rows}
    for source_id in CORE_IDS:
        assert by_id[source_id]["acquisition_status"] == "PARTIALLY_ACQUIRED_AND_CHECKSUMMED"
        assert by_id[source_id]["checksum_status"] == "SHA-256 RECORDED"
    assert by_id["SRC_SEVDARI_2023"]["acquisition_status"] == "ACQUIRED_AND_CHECKSUMMED"


def test_no_staged_raw_filename_was_copied_to_processed_or_results() -> None:
    staged_names = {
        record["original_filename"]
        for source_id in P105_IDS
        for record in metadata(source_id)["files"]
    }
    for directory in (ROOT / "data" / "processed", ROOT / "results"):
        assert not any(
            path.name in staged_names for path in directory.rglob("*") if path.is_file()
        )
