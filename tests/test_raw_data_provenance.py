"""P10 provenance checks only; no scientific data processing is performed."""

import csv
import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "metadata" / "SOURCE_MANIFEST.csv"

ALLOWED_ACQUISITION_STATUSES = {
    "ACQUIRED_AND_CHECKSUMMED",
    "PARTIALLY_ACQUIRED_AND_CHECKSUMMED",
    "MANUAL_SUBSET_SELECTION_REQUIRED",
    "ACCESS_VERIFIED_DOWNLOAD_DEFERRED",
    "MANUAL_OR_STAGED_DOWNLOAD_REQUIRED",
    "ARTICLE_ONLY_PARAMETER_SOURCE",
    "SUPPLEMENTARY_DATA_NOT_VERIFIED",
    "ACCESS_BLOCKED",
    "NOT_FOUND",
    "FULL_REQUIRED_ARTIFACTS_ACQUIRED",
    "REQUIRED_REFERENCE_ARTIFACTS_ACQUIRED",
    "OFFICIAL_SAMPLE_AND_SUPPLEMENTS_ACQUIRED",
    "METADATA_ONLY_NO_EXECUTABLE_RAW_DATA",
}

CRITICAL_SOURCE_IDS = {
    "SRC_LUH_2024",
    "SRC_SCHREIBER_2025",
    "SRC_TUM_ID3",
    "SRC_NHTS_2022",
    "SRC_CAMBIUM_2024",
    "SRC_LLAMAS_OROZCO_2023",
}


def manifest_rows() -> list[dict[str, str]]:
    assert MANIFEST.is_file()
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def test_manifest_represents_required_frozen_sources() -> None:
    rows = manifest_rows()
    source_ids = [row["source_id"] for row in rows]
    assert len(rows) >= 15
    assert len(source_ids) == len(set(source_ids))
    assert CRITICAL_SOURCE_IDS <= set(source_ids)
    assert all(row["acquisition_status"] in ALLOWED_ACQUISITION_STATUSES for row in rows)


def test_acquired_files_have_metadata_and_valid_sha256() -> None:
    acquired = {
        row["source_id"]: row
        for row in manifest_rows()
        if row["acquisition_status"] in {"ACQUIRED_AND_CHECKSUMMED", "PARTIALLY_ACQUIRED_AND_CHECKSUMMED"}
    }
    assert acquired

    documented_paths: set[Path] = set()
    for source_id in acquired:
        metadata_path = ROOT / "data" / "metadata" / f"{source_id}.yaml"
        assert metadata_path.is_file()
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        assert metadata["source_id"] == source_id
        assert metadata["transformation_status"] == "RAW_UNMODIFIED"
        assert metadata["files"]

        for record in metadata["files"]:
            raw_file = ROOT / record["raw_relative_path"]
            assert raw_file.is_file()
            assert raw_file.is_relative_to(ROOT / "data" / "raw")
            assert raw_file.stat().st_size > 0
            assert raw_file.stat().st_size == record["file_size_bytes"]
            assert len(record["sha256"]) == 64
            assert sha256(raw_file) == record["sha256"]
            documented_paths.add(raw_file.resolve())

    p145s_freeze = ROOT / "data" / "metadata" / "P145S_SOURCE_ARTIFACT_FREEZE.csv"
    if p145s_freeze.is_file():
        with p145s_freeze.open(encoding="utf-8", newline="") as handle:
            for record in csv.DictReader(handle):
                raw_file = ROOT / record["relative_path"]
                assert raw_file.is_file()
                assert raw_file.is_relative_to(ROOT / "data" / "raw")
                assert raw_file.stat().st_size == int(record["byte_size"])
                assert sha256(raw_file) == record["sha256"].upper()
                documented_paths.add(raw_file.resolve())

    actual_raw_files = {
        path.resolve()
        for path in (ROOT / "data" / "raw").rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT / "data" / "raw").parts
    }
    assert actual_raw_files == documented_paths


def test_acquired_raw_filenames_are_not_duplicated_outside_raw_storage() -> None:
    acquired_filenames = {
        record["original_filename"]
        for row in manifest_rows()
        if row["acquisition_status"] in {"ACQUIRED_AND_CHECKSUMMED", "PARTIALLY_ACQUIRED_AND_CHECKSUMMED"}
        for record in yaml.safe_load(
            (ROOT / "data" / "metadata" / f"{row['source_id']}.yaml").read_text(
                encoding="utf-8"
            )
        )["files"]
    }
    for directory in (ROOT / "data" / "processed", ROOT / "results"):
        assert not any(
            path.name in acquired_filenames for path in directory.rglob("*") if path.is_file()
        )
