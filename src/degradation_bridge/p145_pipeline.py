from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src/degradation_bridge/p145_config.yaml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_parquet(frame: pd.DataFrame, path: Path, sort_by: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.sort_values(sort_by, kind="mergesort").reset_index(drop=True).to_parquet(
        path, index=False, engine="pyarrow", compression="zstd"
    )


def profile_support(observations: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    profile = observations.loc[observations.age_type.eq(3)].copy()
    baselines = (profile.sort_values(["cell_key", "elapsed_days"], kind="mergesort")
        .groupby("cell_key", sort=True).first()[["discharge_throughput_ah", "capacity_baseline_ah"]]
        .rename(columns={"discharge_throughput_ah": "baseline_discharge_throughput_ah",
                         "capacity_baseline_ah": "same_cell_capacity_baseline_ah"}))
    profile = profile.join(baselines, on="cell_key")
    profile["source_discharge_efc"] = ((profile.discharge_throughput_ah - profile.baseline_discharge_throughput_ah)
                                         / profile.same_cell_capacity_baseline_ah)
    support = (profile.groupby(["condition_id", "age_profile", "age_temp"], sort=True)
        .agg(cell_count=("cell_key", "nunique"), max_elapsed_days=("elapsed_days", "max"),
             max_source_discharge_efc=("source_discharge_efc", "max"),
             minimum_physical_capacity_retention=("reconstructed_capacity_retention", "min"),
             maximum_r10_rel=("r10_rel", "max"), maximum_r1s_rel=("r1s_rel", "max")).reset_index())
    totals = {"condition_count": int(support.condition_id.nunique()), "cell_count": int(profile.cell_key.nunique()),
              "max_elapsed_days": float(profile.elapsed_days.max()),
              "max_source_discharge_efc": float(profile.source_discharge_efc.max())}
    return support, totals


def bridge_rows(config: dict, profile_totals: dict) -> pd.DataFrame:
    inp = config["real_world_inputs"]
    baseline_state = config["state_rules"]["baseline_state"]
    calendar_limit = config["source_native_exposure"]["luh_calendar_max_elapsed_days"]
    profile_efc_limit = profile_totals["max_source_discharge_efc"]
    rows = []
    for candidate in config["candidate_bridges"]:
        for mileage_id, annual_km in inp["mileage_scenarios_km_per_year"].items():
            for window in inp["fresh_usable_window_fraction_scenarios"]:
                for year in range(config["entry_year"], config["horizon_year"] + 1):
                    age = year - config["entry_year"]
                    days = 365.25 * age
                    cumulative_km = annual_km * age
                    annual_l2 = annual_km * inp["fresh_l2_battery_side_kwh_per_km"]
                    cumulative_l2 = annual_l2 * age
                    pack_efc = cumulative_l2 / (inp["nominal_pack_energy_kwh"] * window)
                    baseline = age == 0
                    if baseline:
                        joint = "BASELINE_IDENTITY"
                        envelope = "PRIMARY PHYSICAL SPECIFICATION — BASELINE"
                        status = "VALIDATED_BASELINE_ONLY"
                    elif candidate["bridge_id"] == "A_PROFILE_THROUGHPUT":
                        joint = "USE_PROXY_ONLY; CALENDAR_COMPONENT_UNRESOLVED"
                        envelope = "NOT_ASSIGNED"
                        status = "DEGRADATION STATE OUTSIDE VALIDATED DOMAIN"
                    elif candidate["bridge_id"] == "B_CALENDAR_PLUS_USE":
                        joint = "REJECTED_NO_SEPARABLE_ADDITIVE_EVIDENCE"
                        envelope = "NOT_ASSIGNED"
                        status = "DEGRADATION STATE OUTSIDE VALIDATED DOMAIN"
                    else:
                        joint = "NO_OBSERVED_JOINT_REAL_TIME_USE_MATCH"
                        envelope = "NOT_ASSIGNED"
                        status = "DEGRADATION STATE OUTSIDE VALIDATED DOMAIN"
                    rows.append({
                        "cohort_id": config["cohort_id"], "operation_year": year,
                        "calendar_age_years": float(age), "calendar_age_days": float(days),
                        "mileage_scenario": mileage_id, "annual_km": float(annual_km),
                        "cumulative_km": float(cumulative_km), "fresh_usable_window_fraction": float(window),
                        "annual_l2_battery_side_kwh": float(annual_l2),
                        "cumulative_l2_battery_side_kwh": float(cumulative_l2),
                        "pack_energy_equivalent_cycles_proxy": float(pack_efc),
                        "bridge_id": candidate["bridge_id"], "bridge_disposition": candidate["disposition"],
                        "degradation_state_id": "FRESH_BASELINE" if baseline else None,
                        "state_available": bool(baseline),
                        "source_role": "LUH_PRIMARY_EXPERIMENTAL_STATE_SPACE; SCHREIBER_VALIDATION_ONLY",
                        "calendar_exposure_in_observed_luh_domain": bool(days <= calendar_limit + 1e-12),
                        "use_proxy_in_observed_luh_profile_efc_range": bool(pack_efc <= profile_efc_limit + 1e-12),
                        "joint_mapping_status": joint,
                        "capacity_retention": float(baseline_state["capacity_retention"]) if baseline else np.nan,
                        "r10_rel": float(baseline_state["r10_rel"]) if baseline else np.nan,
                        "r1s_rel": float(baseline_state["r1s_rel"]) if baseline else np.nan,
                        "capacity_source_field": "reconstructed_capacity_retention" if baseline else "NONE_STATE_NOT_ASSIGNED",
                        "envelope_class": envelope, "degradation_domain_status": status,
                        "lifecycle_ghg_calculated": False, "replacement_optimization_performed": False})
    return pd.DataFrame(rows)


def uncertainty_rows(config: dict, totals: dict) -> pd.DataFrame:
    reasons = {
        "A_PROFILE_THROUGHPUT": "Normalized use proxy has source support, but continuous laboratory profile ageing embeds calendar time and accelerated duty; no calendar correction is available.",
        "B_CALENDAR_PLUS_USE": "Calendar observations include check-up cycling and profile/cyclic observations already include elapsed time; separability and additivity are not established.",
        "C_EMPIRICAL_BOUNDED_STATE_TRANSITION": "Observed joint state-space ends near 449 experimental days and contains no matched low-duty multi-year field trajectory."}
    rows = []
    for candidate in config["candidate_bridges"]:
        for scenario_class in config["scenario_classes"]:
            rows.append({"bridge_id": candidate["bridge_id"], "scenario_class": scenario_class,
                "architecture": candidate["architecture"], "disposition": candidate["disposition"],
                "calendar_component_supported": False,
                "use_exposure_proxy_supported": candidate["bridge_id"] == "A_PROFILE_THROUGHPUT",
                "joint_state_mapping_supported": False,
                "calendar_use_double_counting_avoided": candidate["bridge_id"] != "B_CALENDAR_PLUS_USE",
                "luh_profile_condition_count": totals["condition_count"], "luh_profile_cell_count": totals["cell_count"],
                "luh_profile_max_elapsed_days": totals["max_elapsed_days"],
                "luh_profile_max_source_discharge_efc": totals["max_source_discharge_efc"],
                "state_assignment": "BASELINE_ONLY", "failure_reason": reasons[candidate["bridge_id"]],
                "failure_class": config["failure_class"]})
    return pd.DataFrame(rows)


def _raw_start_datetime(path: Path) -> datetime:
    with path.open("r", encoding="latin-1") as stream:
        for _ in range(20):
            match = re.match(r"~Start of Test:\s*(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2})", stream.readline())
            if match:
                return datetime.strptime(match.group(1), "%d.%m.%Y %H:%M:%S")
    raise ValueError(f"Start date missing: {path}")


def automotive_rows() -> pd.DataFrame:
    source = pd.read_parquet(ROOT / "data/processed/schreiber_automotive_validation_summary.parquet")
    starts = {}
    raw_root = ROOT / "data/raw/SRC_SCHREIBER_2025"
    for scenario in ["commuter", "highway"]:
        for path in sorted((raw_root / f"{scenario}_scenario").glob("*.txt")):
            starts[path.stem] = _raw_start_datetime(path)
    baselines = {scenario: min(starts[row.checkup_id] for row in group.itertuples(index=False))
                 for scenario, group in source.groupby("scenario", sort=True)}
    source["laboratory_elapsed_days_from_selected_cu0"] = [
        (starts[row.checkup_id] - baselines[row.scenario]).total_seconds() / 86400
        for row in source.itertuples(index=False)]
    source["validation_envelope_class"] = np.select(
        [source.scenario.eq("highway") & source.cu_index.eq(22),
         source.scenario.eq("commuter") & source.cu_index.ge(30)],
        ["EXTREME / CONDITIONAL ENVELOPE", "AUTOMOTIVE CONDITIONAL — CONTACT-SENSITIVE"],
        default="AUTOMOTIVE-COMPATIBLE ENVELOPE")
    source["exposure_alignment_to_luh"] = "NONE"
    source["primary_fit_role"] = "FORBIDDEN_VALIDATION_ONLY"
    source["real_world_bridge_conclusion"] = "DIRECTIONAL_VALIDATION_ONLY; NO_CALENDAR_USE_BRIDGE"
    return source


def generate() -> dict:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    observations = pd.read_parquet(ROOT / "data/processed/luh_degradation_state_observations.parquet")
    if config["state_rules"]["physical_capacity_field"] not in observations.columns:
        raise ValueError("Physical capacity field missing")
    support, totals = profile_support(observations)
    bridge, uncertainty, automotive = bridge_rows(config, totals), uncertainty_rows(config, totals), automotive_rows()
    outputs = {
        "bridge": (bridge, ROOT / "data/processed/p145_real_world_degradation_bridge.parquet", ["bridge_id", "mileage_scenario", "fresh_usable_window_fraction", "operation_year"]),
        "uncertainty": (uncertainty, ROOT / "data/processed/p145_degradation_bridge_uncertainty.parquet", ["bridge_id", "scenario_class"]),
        "automotive": (automotive, ROOT / "data/processed/p145_automotive_bridge_validation.parquet", ["scenario", "cu_index"])}
    for frame, path, sort_by in outputs.values():
        write_parquet(frame, path, sort_by)
    metadata_dir = ROOT / "data/processed/metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_paths = []
    for frame, path, _ in outputs.values():
        metadata_path = metadata_dir / path.name.replace(".parquet", ".yaml")
        metadata_path.write_text(yaml.safe_dump({"stage": "P14.5", "file": path.name, "row_count": len(frame),
            "processing_script": "src/degradation_bridge/p145_pipeline.py", "scientific_fitting_performed": "NONE",
            "unsupported_degradation_extrapolation_performed": "NONE", "lifecycle_ghg_calculated": "NONE",
            "replacement_optimization_performed": "NONE", "final_gate": config["final_gate"]}, sort_keys=False), encoding="utf-8")
        metadata_paths.append(metadata_path)
    calendar = observations.loc[observations.age_type.eq(1)]
    params = {"stage": "P14.5", "configuration_id": config["configuration_id"], "locked_before_lifecycle_results": True,
        "real_world_inputs": config["real_world_inputs"],
        "luh_calendar_support": {"condition_count": int(calendar.condition_id.nunique()),
            "cell_count": int(calendar.cell_key.nunique()), "max_elapsed_days": float(calendar.elapsed_days.max()),
            "operation_cycle_count_is_zero": bool(calendar.num_cycles_op.max() == 0),
            "checkup_throughput_present": bool(calendar.discharge_throughput_ah.max() > calendar.discharge_throughput_ah.min())},
        "luh_profile_support": totals, "luh_profile_condition_support": support.to_dict(orient="records"),
        "candidate_bridge_dispositions": config["candidate_bridges"], "selected_primary_bridge": "NONE",
        "nonzero_state_assignment_count": int(bridge.loc[bridge.calendar_age_years.gt(0), "capacity_retention"].notna().sum()),
        "state_mapping_rule": "Only age-zero identity is assigned; all nonzero real-world ages remain outside validated degradation domain.",
        "capacity_scaling_field": "reconstructed_capacity_retention", "source_capacity_soh_percent_physical_use": "FORBIDDEN",
        "schreiber_role": "INDEPENDENT_AUTOMOTIVE_VALIDATION_ONLY",
        "false_optimum_precursor_rejection": config["false_optimum_precursor_rejection"],
        "scientific_fitting_performed": "NONE", "lifecycle_ghg_calculated": "NONE",
        "replacement_optimization_performed": "NONE", "unsupported_degradation_extrapolation_performed": "NONE",
        "frozen_decision_changes": "NONE", "failure_class": config["failure_class"], "final_gate": config["final_gate"]}
    params_path = ROOT / "results/intermediate/p145_bridge_parameters.json"
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(json.dumps(params, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    artifacts = [CONFIG_PATH, Path(__file__), ROOT / "tests/test_p145_degradation_bridge.py",
        ROOT / "docs/P145_REAL_WORLD_DEGRADATION_BRIDGE_REPORT.md", ROOT / "docs/RESEARCH_DECISION_LOG.md", params_path,
        *[item[1] for item in outputs.values()], *metadata_paths]
    manifest = {"stage": "P14.5", "final_gate": config["final_gate"], "artifact_count": len(artifacts),
        "artifacts": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size}
                      for path in sorted(artifacts, key=lambda item: item.as_posix())]}
    manifest_path = ROOT / "results/intermediate/p145_artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"rows": {key: len(value[0]) for key, value in outputs.items()},
            "nonzero_state_assignment_count": params["nonzero_state_assignment_count"],
            "failure_class": config["failure_class"], "final_gate": config["final_gate"]}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))

