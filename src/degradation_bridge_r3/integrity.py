from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/metadata/P145I_PRE_IMPLEMENTATION_INTEGRITY.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frozen_paths() -> list[Path]:
    candidates: set[Path] = set()
    for pattern in (
        "data/processed/p12_*.parquet",
        "data/processed/p13_*.parquet",
        "data/processed/p14_*.parquet",
        "data/processed/p145_*.parquet",
        "results/intermediate/p12_*",
        "results/intermediate/p13_*",
        "results/intermediate/p14_*",
        "results/intermediate/p145_*",
        "docs/P12_*.md",
        "docs/P13_*.md",
        "docs/P14_*.md",
        "docs/P145_*.md",
        "docs/P145R_*.md",
        "docs/P145S_*.md",
    ):
        candidates.update(path for path in ROOT.glob(pattern) if path.is_file())
    # Mutable cross-stage ledgers are recorded separately and deliberately not
    # asserted byte-identical after the authorized P14.5I append.
    candidates.discard(ROOT / "docs/RESEARCH_DECISION_LOG.md")
    candidates.discard(ROOT / "docs/IMPLEMENTATION_SPEC.md")
    candidates.discard(ROOT / "data/metadata/SOURCE_MANIFEST.csv")
    return sorted(candidates, key=lambda p: p.relative_to(ROOT).as_posix())


def capture() -> dict:
    records = [
        {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256(p), "bytes": p.stat().st_size}
        for p in frozen_paths()
    ]
    special = {}
    for name in (
        "docs/IMPLEMENTATION_SPEC.md",
        "docs/RESEARCH_DECISION_LOG.md",
        "data/metadata/SOURCE_MANIFEST.csv",
    ):
        path = ROOT / name
        special[name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    payload = {
        "stage": "P14.5I",
        "purpose": "pre-implementation integrity envelope",
        "frozen_artifact_count": len(records),
        "frozen_artifacts": records,
        "special_pre_change_records": special,
        "p12_p13_p14_scientific_outputs_must_remain_unchanged": True,
        "p145_failure_record_must_remain": True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_frozen(payload: dict | None = None) -> list[str]:
    if payload is None:
        payload = json.loads(OUT.read_text(encoding="utf-8"))
    mismatches = []
    for item in payload.get("frozen_artifacts", payload.get("historical_stage_manifests", [])):
        if item["path"] == "results/intermediate/p145_artifact_manifest.json":
            continue  # legacy manifest embeds the authorized append-only log
        path = ROOT / item["path"]
        size_mismatch = "bytes" in item and path.is_file() and path.stat().st_size != item["bytes"]
        if not path.is_file() or sha256(path) != item["sha256"] or size_mismatch:
            mismatches.append(item["path"])
    p145_science = {
        "data/processed/p145_automotive_bridge_validation.parquet": "8724eb6c483a437ef0dd97c159ec0602b4c6604b973e992cb12499b62165db50",
        "data/processed/p145_degradation_bridge_uncertainty.parquet": "c2174807a8ec3c4f7d712cab24f3113d5840227ccf4b6685bd410a6058838ab7",
        "data/processed/p145_real_world_degradation_bridge.parquet": "297f8ad11968e47eb477dd9e2718c039f79a72d1d2867d23b2a959fc0616b482",
    }
    for name, expected in p145_science.items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            mismatches.append(name)
    return mismatches


if __name__ == "__main__":
    print(json.dumps(capture(), indent=2, sort_keys=True))
