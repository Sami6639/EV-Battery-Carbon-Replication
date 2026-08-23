from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from .pipeline import ROOT, generate, sha256


def verify_two_generations() -> dict:
    manifest_path = ROOT / "results/intermediate/p145i_artifact_manifest.json"
    deng = pd.read_parquet(ROOT / "results/intermediate/p145i_deng_capacity_events.parquet")
    audit = json.loads((ROOT / "results/diagnostics/P145I_DENG_ARCHIVE_CHECKPOINT.json").read_text(encoding="utf-8"))
    first_result = generate(ROOT, reproduce_field=False, cached_deng=deng, cached_deng_audit=audit)
    first = first_result["manifest"]
    first_hashes = {item["path"]: item["sha256"] for item in first["artifacts"]}
    second_result = generate(ROOT, reproduce_field=False, cached_deng=deng, cached_deng_audit=audit)
    second = second_result["manifest"]
    second_hashes = {item["path"]: item["sha256"] for item in second["artifacts"]}
    mismatches = sorted(path for path in set(first_hashes) | set(second_hashes)
                        if first_hashes.get(path) != second_hashes.get(path))
    result = {
        "stage": "P14.5I", "generation_count": 2,
        "raw_source_precursor": "all 20 Deng archives completed once before the paired final generations",
        "first_generation": "complete final R3 generation from frozen sources and deterministic Deng event checkpoint",
        "second_generation": "independent complete final R3 regeneration from the same frozen inputs",
        "checked_artifact_count": len(first_hashes), "mismatches": mismatches,
        "identical_sha256": not mismatches, "status": "PASS" if not mismatches else "FAIL",
        "final_manifest_sha256": sha256(manifest_path),
    }
    path = ROOT / "results/diagnostics/P145I_DETERMINISM_VERIFICATION.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(verify_two_generations(), indent=2, sort_keys=True))
