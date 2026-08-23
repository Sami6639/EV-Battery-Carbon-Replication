from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd

from .blast_runner import MODEL_CLASSES, PRIMARY, run_model
from .exposure import aggregate_hourly, generate_profile, profile_specs
from .field_validation import reproduce_deng, validate_deng, validate_liu
from .integrity import verify_frozen
from .resistance_envelope import build_resistance_envelopes

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_NAMES = [
    "p145i_e2_exposure_profiles.parquet", "p145i_blast_capacity_trajectories.parquet",
    "p145i_capacity_field_validation.parquet", "p145i_conditional_resistance_envelopes.parquet",
    "p145i_r3_real_world_degradation_bridge.parquet", "p145i_bridge_uncertainty.parquet",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_parquet(frame: pd.DataFrame, path: Path, sort_by: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.sort_values(sort_by, kind="mergesort").reset_index(drop=True).to_parquet(
        path, index=False, engine="pyarrow", compression="zstd")


def _capacity_trajectories(exposure_summaries: pd.DataFrame, hourly: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, list[dict]]:
    frames, audits = [], []
    summary_by_id = exposure_summaries.set_index("profile_id")
    for model_name in MODEL_CLASSES:
        for profile_id in sorted(hourly):
            frame, audit = run_model(model_name, profile_id, hourly[profile_id], years=25)
            s = summary_by_id.loc[profile_id]
            frame["annual_km"] = float(s.annual_km_target)
            frame["cumulative_km"] = frame.age_years * frame.annual_km
            frame["annual_battery_throughput_kwh"] = float(s.annual_battery_throughput_kwh_target)
            frame["cumulative_battery_throughput_kwh"] = frame.age_years * frame.annual_battery_throughput_kwh
            frame["mean_cell_temperature_c"] = float(hourly[profile_id].Temperature_C.mean())
            frame["mean_soc"] = float(hourly[profile_id].SOC.mean())
            frame["min_soc"] = float(hourly[profile_id].SOC.min())
            frame["max_soc"] = float(hourly[profile_id].SOC.max())
            frames.append(frame)
            audits.append({"model_name": model_name, "profile_id": profile_id, **audit})
    return pd.concat(frames, ignore_index=True), audits


def _overall_validation(metrics: list[dict], deng_audit: dict) -> str:
    if deng_audit["status"] == "DENG FIELD VALIDATION INCOMPLETE":
        return "FAIL"
    rank = {"PASS": 0, "PASS WITH BOUNDS": 1, "FAIL": 2}
    return max((m["status"] for m in metrics), key=lambda x: rank[x])


def _bridge(capacity: pd.DataFrame, resistance: pd.DataFrame, validation_status: str) -> pd.DataFrame:
    joined = resistance.merge(capacity[["model_name", "profile_id", "age_years", "model_role",
        "input_domain_status", "capacity_state_status", "long_horizon_label", "annual_km", "cumulative_km",
        "cumulative_battery_throughput_kwh", "mean_cell_temperature_c", "mean_soc"]],
        on=["model_name", "profile_id", "age_years"], how="left", validate="many_to_one")
    joined["capacity_field_validation_status"] = validation_status
    joined["capacity_claim"] = "modeled real-world capacity trajectory"
    joined["resistance_claim"] = "conditional resistance-state envelope"
    joined["resistance_identifiability"] = "real-world resistance trajectory unidentified"
    joined["joint_bridge_admissible"] = (
        joined.input_domain_status.eq("IN_DOMAIN") &
        joined.capacity_state_status.eq("MODELED") &
        joined.resistance_state_status.eq("SUPPORTED CONDITIONAL ENVELOPE") &
        (validation_status != "FAIL"))
    joined["joint_bridge_status"] = np.where(joined.joint_bridge_admissible,
        "VALID REAL-WORLD BRIDGE DOMAIN", "JOINT R3 BRIDGE UNSUPPORTED")
    joined["p13_schema_capacity_compatible"] = joined.capacity_retention.between(0, 1, inclusive="both")
    joined["p13_schema_resistance_compatible"] = joined.automotive_outer_lower.gt(0) & joined.automotive_outer_upper.ge(joined.automotive_outer_lower)
    joined["lifecycle_ghg_calculated"] = False
    joined["replacement_optimization_performed"] = False
    return joined


def generate(output_root: Path | None = None, reproduce_field: bool = True,
             cached_deng: pd.DataFrame | None = None, cached_deng_audit: dict | None = None) -> dict:
    if verify_frozen():
        raise RuntimeError("Historical P12/P13/P14/P14.5 integrity envelope mismatch")
    output_root = Path(output_root) if output_root else ROOT
    exposure_frames, summaries, hourly = [], [], {}
    for spec in profile_specs():
        frame, summary = generate_profile(spec)
        exposure_frames.append(frame); summaries.append(summary); hourly[spec.profile_id] = aggregate_hourly(frame)
    exposure = pd.concat(exposure_frames, ignore_index=True)
    exposure_summaries = pd.DataFrame(summaries)
    if (exposure_summaries[["distance_relative_error", "throughput_relative_error"]].max().max() > 0.005):
        raise RuntimeError("E2 aggregation preservation exceeds 0.5%")
    capacity, domain_audits = _capacity_trajectories(exposure_summaries, hourly)
    liu_rows, liu_metrics = validate_liu(capacity)
    if reproduce_field:
        deng_events, deng_audit = reproduce_deng()
    else:
        if cached_deng is None or cached_deng_audit is None:
            raise ValueError("cached Deng records and audit required")
        deng_events, deng_audit = cached_deng.copy(), dict(cached_deng_audit)
    deng_rows, deng_metrics = validate_deng(deng_events, capacity)
    field = pd.concat([liu_rows, deng_rows], ignore_index=True, sort=False)
    overall = _overall_validation([liu_metrics, deng_metrics], deng_audit)
    resistance = build_resistance_envelopes(capacity)
    bridge = _bridge(capacity, resistance, overall)
    uncertainty = pd.DataFrame([
        {"uncertainty_id": "PRIMARY_MODEL_STRUCTURE", "status": "NON_AVERAGED",
         "detail": "DENSO NMC622 and LG MJ1 NMC811 remain distinct; no field-driven selection."},
        {"uncertainty_id": "CONDITIONAL_MODEL_STRUCTURE", "status": "SENSITIVITY_ONLY",
         "detail": "A/B1/B2/M50 are separately named and domain-gated."},
        {"uncertainty_id": "FIELD_CAPACITY_VALIDATION", "status": overall,
         "detail": "Worst-source pre-registered gate across accessible Liu and open Deng observations."},
        {"uncertainty_id": "LIU_LABEL_REPRODUCIBILITY", "status": "PASS WITH BOUNDS CEILING",
         "detail": "OEM OCV-SOC table withheld; publisher-plotted labels only."},
        {"uncertainty_id": "RESISTANCE_IDENTIFIABILITY", "status": "real-world resistance trajectory unidentified",
         "detail": "Only capacity/stress-conditioned R10 and separate R1s envelopes are reported."},
        {"uncertainty_id": "LONG_HORIZON", "status": "MODEL PROJECTION BEYOND DIRECT FIELD VALIDATION",
         "detail": "No knee, tail, or clipping is introduced."},
    ])
    processed = output_root / "data/processed"
    outputs = {
        OUTPUT_NAMES[0]: (exposure, ["profile_id", "interval_index"]),
        OUTPUT_NAMES[1]: (capacity, ["model_name", "profile_id", "age_years"]),
        OUTPUT_NAMES[2]: (field, ["source_id", "observation_id"]),
        OUTPUT_NAMES[3]: (resistance, ["model_name", "profile_id", "age_years", "stress_class", "resistance_endpoint"]),
        OUTPUT_NAMES[4]: (bridge, ["model_name", "profile_id", "age_years", "stress_class", "resistance_endpoint"]),
        OUTPUT_NAMES[5]: (uncertainty, ["uncertainty_id"]),
    }
    for name, (frame, sort_by) in outputs.items():
        write_parquet(frame, processed / name, sort_by)
    diagnostics = output_root / "results/diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    (diagnostics / "P145I_DENG_ARCHIVE_CHECKPOINT.json").write_text(json.dumps(deng_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (diagnostics / "P145I_BLAST_DOMAIN_AUDIT.json").write_text(json.dumps(domain_audits, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Cache source-derived Deng labels so the deterministic complete generation
    # can be repeated without another blind monolithic extraction attempt.
    deng_cache = output_root / "results/intermediate/p145i_deng_capacity_events.parquet"
    write_parquet(deng_events, deng_cache, ["vehicle_id", "time_e", "time_s"])
    final_status = "R3 REAL-WORLD DEGRADATION BRIDGE FAIL" if overall == "FAIL" or not bridge.joint_bridge_admissible.any() else (
        "R3 REAL-WORLD DEGRADATION BRIDGE VALIDATED WITH BOUNDS" if overall == "PASS WITH BOUNDS" else
        "R3 REAL-WORLD DEGRADATION BRIDGE VALIDATED — PASS")
    params = {
        "stage": "P14.5I", "architecture": "R3 — HYBRID BOUNDED MAPPING",
        "profile_count": 17, "state_resolution_minutes": 15, "model_aggregation_hours": 1,
        "profile_summaries": summaries, "primary_models": sorted(PRIMARY),
        "structural_sensitivities": sorted(set(MODEL_CLASSES) - PRIMARY),
        "degradation_scalar": 1, "scientific_fitting_performed": "NONE", "field_calibration_performed": "NONE",
        "validation_metrics": [liu_metrics, deng_metrics], "overall_capacity_validation_status": overall,
        "deng_reproduction_status": deng_audit["status"], "joint_admissible_row_count": int(bridge.joint_bridge_admissible.sum()),
        "thermal_implementation": "SOURCE-BOUNDED CELL-TEMPERATURE PROXY",
        "thermal_dependency_bound": "Wu tum_model absent; exact Wu/TUM boundary values only",
        "lifecycle_ghg_calculated": "NONE", "replacement_optimization_performed": "NONE",
        "unsupported_extrapolation_performed": "NONE", "final_status": final_status,
    }
    intermediate = output_root / "results/intermediate"
    intermediate.mkdir(parents=True, exist_ok=True)
    params_path = intermediate / "p145i_r3_parameters.json"
    params_path.write_text(json.dumps(params, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    artifact_paths = [processed / name for name in OUTPUT_NAMES] + [params_path, deng_cache,
        diagnostics / "P145I_DENG_ARCHIVE_CHECKPOINT.json", diagnostics / "P145I_BLAST_DOMAIN_AUDIT.json"]
    manifest = {"stage": "P14.5I", "final_status": final_status,
        "artifacts": [{"path": p.relative_to(output_root).as_posix(), "sha256": sha256(p), "bytes": p.stat().st_size}
                      for p in sorted(artifact_paths, key=lambda x: x.as_posix())]}
    manifest["artifact_count"] = len(manifest["artifacts"])
    manifest_path = intermediate / "p145i_artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"final_status": final_status, "parameters": params, "manifest": manifest,
            "deng_events": deng_events, "deng_audit": deng_audit}


if __name__ == "__main__":
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-p145i"))
    result = generate()
    print(json.dumps({"final_status": result["final_status"],
                      "validation": result["parameters"]["validation_metrics"]}, indent=2, sort_keys=True))
