import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "P145S_R3_REVISION_SPECIFICATION_REPORT.md"
EXPECTED_SECTIONS = [
"Governing Files Read", "Revision Scope", "Preserved P14.5 Failure", "R3 Scientific Architecture",
"New Source Audit", "Source Provenance and Licenses", "BLAST NMC Model Inventory", "Capacity Model Eligibility",
"Capacity Model Selection Architecture", "Long-Horizon Projection Rule", "Liu Field Dataset Audit",
"Deng Field Dataset Audit", "Independent Validation Architecture", "Validation Metrics",
"Pre-Registered Validation Thresholds", "Exposure Generator Candidates", "Selected Exposure Architecture",
"Temperature Treatment", "Parked-SOC / Charging Treatment", "Calendar/Use Interaction",
"Resistance Identifiability", "Proposed Resistance-Envelope Algorithm", "R10/R1s Separation",
"Unsupported-State Rule", "Compatibility with P12", "Compatibility with P13", "Compatibility with P14",
"False-Optimum Gate", "RQ Preservation Test", "Proposed IMPLEMENTATION_SPEC Revision", "Files Created",
"Files Modified", "Tests / Integrity Checks", "Lifecycle GHG Calculated", "Replacement Optimization Performed",
"Scientific Bridge Implemented", "Hard Blockers", "Final Status"]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def test_report_has_exact_required_38_sections():
    text = REPORT.read_text(encoding="utf-8")
    found = re.findall(r"^## (\d+)\. (.+)$", text, flags=re.MULTILINE)
    assert len(found) == 38
    assert [int(n) for n, _ in found] == list(range(1, 39))
    assert [title for _, title in found] == EXPECTED_SECTIONS


def test_required_invariants_and_disclosures_are_exact():
    text = REPORT.read_text(encoding="utf-8")
    proposal = (ROOT / "docs" / "IMPLEMENTATION_SPEC_P145S_REVISION_PROPOSAL.md").read_text(encoding="utf-8")
    required = [
        "modeled real-world capacity trajectory",
        "conditional resistance-state envelope",
        "real-world resistance trajectory unidentified",
        "BLAST REAL-WORLD RESISTANCE OUTPUT = NOT AVAILABLE / NOT APPROVED",
        "MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION",
        "RESISTANCE STATE UNSUPPORTED",
        "RQ PRESERVED — INTERPRETATION BOUNDED",
        "Lifecycle GHG Calculated: NONE",
        "Replacement Optimization Performed: NONE",
        "Scientific Bridge Implemented: NONE",
        "Existing P12/P13/P14 Scientific Outputs Modified: NONE",
        "P14.5 Failure Record Removed: NO",
        "R3 METHODOLOGICAL REVISION SPECIFIED WITH BOUNDS",
    ]
    for item in required:
        assert item in text
        if item in required[:7]:
            assert item in proposal


def test_machine_readable_preregistration_and_eligibility():
    prereg = json.loads((ROOT / "data" / "metadata" / "P145S_R3_PREREGISTRATION.json").read_text(encoding="utf-8"))
    assert prereg["exposure_generator"]["selected"] == "E2_BOUNDED_DUTY_CYCLE_FAMILY"
    assert prereg["capacity"]["parameter_rule"].find("degradation_scalar=1") >= 0
    assert prereg["resistance"]["unsupported_return"] == "RESISTANCE STATE UNSUPPORTED"
    assert prereg["long_horizon_label"] == "MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION"
    with (ROOT / "data" / "metadata" / "P145S_BLAST_NMC_MODEL_ELIGIBILITY.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 9
    primary = {r["model_class"] for r in rows if r["eligibility_class"] == "ELIGIBLE_PRIMARY_FAMILY"}
    assert primary == {"Nmc622_Gr_DENSO50Ah_Battery", "Nmc811_GrSi_LGMJ1_4Ah_Battery"}


def test_source_manifest_is_append_only_and_well_formed():
    path = ROOT / "data" / "metadata" / "SOURCE_MANIFEST.csv"
    raw = path.read_bytes()
    first_16_lines = b"".join(raw.splitlines(keepends=True)[:16])
    assert len(first_16_lines) == 9583
    assert sha256_bytes(first_16_lines) == "d2889702f49b0ece440f57915d84491908d6c8428f86d535a3695db7e79867a9"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 20
    assert len({r["source_id"] for r in rows}) == 20
    assert [r["source_id"] for r in rows[-5:]] == ["SRC_BLAST_LITE", "SRC_WU_2026", "SRC_LIU_2025", "SRC_DENG_2023", "SRC_QIUSHI_WANG_2023"]
    assert rows[0]["scientific_role"] == "Primary NMC capacity and pulse-resistance degradation source"


def test_source_freeze_matches_pinned_commits():
    summary = json.loads((ROOT / "data" / "metadata" / "P145S_SOURCE_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["artifact_count"] == 260
    assert summary["per_source"]["SRC_BLAST_LITE"]["git_head"] == "b093495b47dc40dd96dba865d91f553619501e94"
    assert summary["per_source"]["SRC_WU_2026"]["git_head"] == "25dd34bd04c1184c22746843c909fb426af741f1"
    assert summary["per_source"]["SRC_LIU_2025"]["git_head"] == "56c1ef4dd0c5efe005368624e17a1c76a32b6c16"
    assert summary["per_source"]["SRC_DENG_2023"]["git_head"] == "36fef4bd99f626561e2d138a40ccff3d1f3ddfc2"
    assert summary["per_source"]["SRC_QIUSHI_WANG_2023"]["artifact_count"] == 0


def test_revision_is_proposed_only_and_p15_not_started():
    proposal = (ROOT / "docs" / "IMPLEMENTATION_SPEC_P145S_REVISION_PROPOSAL.md").read_text(encoding="utf-8")
    assert "PROPOSED ONLY — NOT AUTHORITATIVE" in proposal
    assert "IMPLEMENTATION_SPEC.md` remains authoritative" in proposal
    assert "no R3 bridge" in proposal

def test_deng_reproduction_limit_is_fail_closed():
    audit = json.loads((ROOT / "results" / "diagnostics" / "P145S_DENG_CAPACITY_EXTRACTION_AUDIT.json").read_text(encoding="utf-8"))
    assert audit["direct_source_execution"]["status"] == "FAIL_IMPORT"
    assert audit["compatibility_attempt"]["status"] == "NOT EXACT / NOT COMPLETED"
    assert audit["compatibility_attempt"]["capacity_records_produced_or_used"] == "NONE"
    assert audit["compatibility_attempt"]["model_fitting_performed"] == "NONE"