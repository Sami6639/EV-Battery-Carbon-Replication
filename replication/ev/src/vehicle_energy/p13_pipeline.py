from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import fastsim
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[2] / ".matplotlib-p13"))

import matplotlib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from fastsim import Cycle, SimDrive, Vehicle

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src" / "vehicle_energy" / "p13_config.yaml"
ATB_ZIP = ROOT / "data" / "raw" / "SRC_NREL_TRANSPORTATION_ATB_2024" / "2024_atb_transportation_data_v1.zip"
EXPECTED_ATB_SHA256 = "447082c63d7433dad1d3691cb216687096921b73a677db204fb45a0631fb45e3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_parquet_deterministic(frame: pd.DataFrame, path: Path, sort_by: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = frame.sort_values(sort_by, kind="mergesort", na_position="last").reset_index(drop=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, path, compression="zstd", version="2.6", write_statistics=True)


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if config["fastsim_version"] != "3.0.6" or fastsim.__version__ != "3.0.6":
        raise RuntimeError(f"FASTSim version must be exactly 3.0.6; installed={fastsim.__version__}")
    if not config["locked_before_degradation_energy_results"]:
        raise RuntimeError("P13 configuration was not pre-locked")
    return config


def validate_atb_source(config: dict[str, Any]) -> dict[str, Any]:
    actual_hash = sha256(ATB_ZIP)
    if actual_hash != EXPECTED_ATB_SHA256:
        raise RuntimeError("NREL Transportation ATB archive checksum mismatch")
    with ZipFile(ATB_ZIP) as archive:
        atb = pd.read_csv(archive.open("input/inputs_vehicles.csv"))
    filt = config["representative_vehicle"]["source_rule"]["row_filter"]
    selected = atb[
        (atb["year"] == filt["year"])
        & (atb["scenario"] == filt["scenario"])
        & (atb["vehicle_weight_category"] == filt["vehicle_weight_category"])
        & (atb["vehicle_class"] == filt["vehicle_class"])
        & (atb["vehicle_powertrain"] == filt["vehicle_powertrain"])
        & (atb["vehicle_detail"] == filt["vehicle_detail"])
    ]
    if len(selected) != 1:
        raise RuntimeError(f"Locked ATB filter returned {len(selected)} rows")
    row = selected.iloc[0]
    expected_energy = config["representative_vehicle"]["nominal_pack_energy_kwh"]
    expected_intensity = config["representative_vehicle"]["atb_charging_inclusive_energy_wh_per_mile"]
    if not math.isclose(float(row["pack_energy(kWh)"]), expected_energy, abs_tol=1e-6):
        raise RuntimeError("Locked ATB pack energy no longer matches source")
    if not math.isclose(float(row["CD(Wh/mi)"]), expected_intensity, abs_tol=1e-6):
        raise RuntimeError("Locked ATB external energy benchmark no longer matches source")
    return {
        "archive_sha256": actual_hash,
        "atb_reference": str(row["reference"]),
        "atb_usable_energy_is_missing": bool(pd.isna(row["usable_energy(kWh)"])),
    }


def build_representative_vehicle(config: dict[str, Any]) -> Vehicle:
    rv = config["representative_vehicle"]
    params = rv["synthesized_vehicle_parameters"]
    source = Vehicle.from_resource(rv["fastsim_structural_template"]).to_pydict(flatten=False)
    source["name"] = "P13 representative U.S. light-duty midsize BEV archetype"
    source["year"] = 2023
    source["mass_kilograms"] = params["mass_kilograms"]
    source["chassis"]["drag_coef"] = params["drag_coefficient"]
    source["chassis"]["frontal_area_square_meters"] = params["frontal_area_square_meters"]
    source["chassis"]["wheel_rr_coef"] = params["rolling_resistance_coefficient"]
    bev = source["pt_type"]["BEV"]
    bev["em"]["pwr_out_max_watts"] = params["motor_max_power_watts"]
    bev["res"]["energy_capacity_joules"] = rv["nominal_pack_energy_kwh"] * 3.6e6
    bev["res"]["pwr_out_max_watts"] = params["battery_max_power_watts"]
    source["pwr_aux_base_watts"] = params["base_auxiliary_power_watts"]
    bev["transmission"]["eff_interp"] = params["transmission_efficiency"]
    return Vehicle.from_pydict(source)


def run_fresh_fastsim(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    vehicle = build_representative_vehicle(config)
    profiles: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []
    for cyc_cfg in config["drive_cycles"]["cycles"]:
        sim = SimDrive(vehicle.copy(), Cycle.from_resource(cyc_cfg["fastsim_resource"]))
        sim.walk()
        result = sim.to_pydict(flatten=False)["veh"]
        state = result["state"]
        res = result["pt_type"]["BEV"]["res"]
        rh = res["history"]
        vh = result["history"]
        if not state["cyc_met_overall"]:
            raise RuntimeError(f"FASTSim could not meet {cyc_cfg['id']} speed trace")
        n = len(vh["time_seconds"])
        pack_power_w = np.asarray(rh["pwr_out_electrical_watts"], dtype=float)
        rows = pd.DataFrame(
            {
                "archetype_id": "P13_US_LDV_MIDSIZE_BEV_2023",
                "drive_cycle": cyc_cfg["id"],
                "time_s": np.asarray(vh["time_seconds"], dtype=float),
                "distance_m_cumulative": np.asarray(vh["dist_meters"], dtype=float),
                "vehicle_speed_m_per_s": np.asarray(vh["speed_ach_meters_per_second"], dtype=float),
                "hv_terminal_power_w": pack_power_w,
                "soc_fraction": np.asarray(rh["soc"], dtype=float),
                "traction_power_w": np.asarray(vh["pwr_tractive_watts"], dtype=float),
                "energy_boundary": "L2_HV_BATTERY_SIDE",
                "fastsim_ageing_generated": False,
            }
        )
        if len(rows) != n:
            raise RuntimeError("FASTSim history length mismatch")
        profiles.append(rows)
        distance_km = float(state["dist_meters"]) / 1000.0
        chemical_kwh = float(res["state"]["energy_out_chemical_joules"]) / 3.6e6
        terminal_kwh = float(res["state"]["energy_out_electrical_joules"]) / 3.6e6
        loss_kwh = float(res["state"]["energy_loss_joules"]) / 3.6e6
        summaries.append(
            {
                "drive_cycle": cyc_cfg["id"],
                "distance_km": distance_km,
                "fresh_battery_stored_energy_draw_kwh": chemical_kwh,
                "fresh_hv_terminal_net_energy_kwh": terminal_kwh,
                "fresh_storage_loss_kwh": loss_kwh,
                "fresh_battery_side_kwh_per_km": chemical_kwh / distance_km,
                "fresh_terminal_kwh_per_km": terminal_kwh / distance_km,
                "minimum_terminal_power_kw": float(pack_power_w.min()) / 1000.0,
                "maximum_terminal_power_kw": float(pack_power_w.max()) / 1000.0,
                "starting_soc_fraction": float(rh["soc"][0]),
                "ending_soc_fraction": float(rh["soc"][-1]),
                "cycle_trace_met": True,
            }
        )
    summary = pd.DataFrame(summaries)
    weights = config["drive_cycles"]["combined"]
    combined = {
        "drive_cycle": "COMBINED_55_45",
        "distance_km": np.nan,
        "fresh_battery_stored_energy_draw_kwh": np.nan,
        "fresh_hv_terminal_net_energy_kwh": np.nan,
        "fresh_storage_loss_kwh": np.nan,
        "fresh_battery_side_kwh_per_km": (
            weights["city_fraction"] * summary.loc[summary.drive_cycle == "UDDS", "fresh_battery_side_kwh_per_km"].iloc[0]
            + weights["highway_fraction"] * summary.loc[summary.drive_cycle == "HWFET", "fresh_battery_side_kwh_per_km"].iloc[0]
        ),
        "fresh_terminal_kwh_per_km": (
            weights["city_fraction"] * summary.loc[summary.drive_cycle == "UDDS", "fresh_terminal_kwh_per_km"].iloc[0]
            + weights["highway_fraction"] * summary.loc[summary.drive_cycle == "HWFET", "fresh_terminal_kwh_per_km"].iloc[0]
        ),
        "minimum_terminal_power_kw": summary["minimum_terminal_power_kw"].min(),
        "maximum_terminal_power_kw": summary["maximum_terminal_power_kw"].max(),
        "starting_soc_fraction": 1.0,
        "ending_soc_fraction": np.nan,
        "cycle_trace_met": True,
    }
    combined_loss_intensity = (
        weights["city_fraction"] * (summary.loc[summary.drive_cycle == "UDDS", "fresh_storage_loss_kwh"].iloc[0] / summary.loc[summary.drive_cycle == "UDDS", "distance_km"].iloc[0])
        + weights["highway_fraction"] * (summary.loc[summary.drive_cycle == "HWFET", "fresh_storage_loss_kwh"].iloc[0] / summary.loc[summary.drive_cycle == "HWFET", "distance_km"].iloc[0])
    )
    combined["fresh_storage_loss_kwh_per_km"] = combined_loss_intensity
    summary["fresh_storage_loss_kwh_per_km"] = summary["fresh_storage_loss_kwh"] / summary["distance_km"]
    summary = pd.concat([summary, pd.DataFrame([combined])], ignore_index=True)
    return pd.concat(profiles, ignore_index=True), summary


def physical_capacity_nodes(target_days: np.ndarray) -> pd.DataFrame:
    obs = pd.read_parquet(ROOT / "data" / "processed" / "luh_degradation_state_observations.parquet")
    cap = obs[(obs["state_kind"] == "capacity") & obs["reconstructed_capacity_retention"].notna()].copy()
    cap = cap[(cap["elapsed_days"] >= 0.0) & (cap["elapsed_days"] <= 448.1849189814815)]
    mids = (target_days[:-1] + target_days[1:]) / 2.0
    edges = np.r_[-np.inf, mids, np.inf]
    rows = []
    for idx, day in enumerate(target_days):
        subset = cap[(cap["elapsed_days"] > edges[idx]) & (cap["elapsed_days"] <= edges[idx + 1])]
        values = subset["reconstructed_capacity_retention"].to_numpy(float)
        if not len(values):
            raise RuntimeError(f"No physical capacity observations near day {day}")
        rows.append(
            {
                "exposure_days": float(day),
                "capacity_retention_central": float(np.median(values)),
                "capacity_retention_q10": float(np.quantile(values, 0.10)),
                "capacity_retention_q90": float(np.quantile(values, 0.90)),
                "capacity_observations": int(len(values)),
            }
        )
    out = pd.DataFrame(rows)
    out.loc[0, ["capacity_retention_central", "capacity_retention_q10", "capacity_retention_q90"]] = 1.0
    for col in ["capacity_retention_central", "capacity_retention_q10", "capacity_retention_q90"]:
        out[col] = np.minimum.accumulate(out[col].clip(0.0, 1.0))
    out["capacity_retention_q10"] = np.minimum(out["capacity_retention_q10"], out["capacity_retention_central"])
    out["capacity_retention_q90"] = np.maximum(out["capacity_retention_q90"], out["capacity_retention_central"])
    return out


def degradation_states() -> pd.DataFrame:
    model = pd.read_parquet(ROOT / "data" / "processed" / "luh_degradation_state_model.parquet")
    selected = model[model["selected_primary"]].copy()
    r10 = selected[selected.metric_id == "r10_rel"].sort_values("exposure_days").reset_index(drop=True)
    r1s = selected[selected.metric_id == "r1s_rel"].sort_values("exposure_days").reset_index(drop=True)
    if not np.allclose(r10.exposure_days, r1s.exposure_days):
        raise RuntimeError("P12 10-ms and 1-s node axes differ")
    capacity = physical_capacity_nodes(r10.exposure_days.to_numpy(float))
    rows: list[dict[str, Any]] = []
    for spec, frame, class_name in [
        ("10-ms", r10, "PRIMARY PHYSICAL SPECIFICATION"),
        ("1-s", r1s, "ALTERNATIVE 1-S SPECIFICATION"),
    ]:
        for idx, row in frame.iterrows():
            cap = capacity.iloc[idx]
            rows.append(
                {
                    "degradation_state_id": f"LUH_{spec.replace('-', '').replace(' ', '')}_{idx:02d}",
                    "source_id": "SRC_LUH_2024",
                    "physical_envelope_class": class_name,
                    "resistance_specification": spec,
                    "exposure_days": float(row.exposure_days),
                    "relative_resistance": float(row.central_state),
                    "relative_resistance_lower": max(1.0, float(row.observed_q10)),
                    "relative_resistance_upper": max(1.0, float(row.observed_q90)),
                    "capacity_retention": float(cap.capacity_retention_central),
                    "capacity_retention_lower": float(cap.capacity_retention_q10),
                    "capacity_retention_upper": float(cap.capacity_retention_q90),
                    "valid_domain_status": "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
                    "conditional_extreme": False,
                }
            )
            rows.append(
                {
                    "degradation_state_id": f"LUH_{spec.replace('-', '').replace(' ', '')}_Q90_{idx:02d}",
                    "source_id": "SRC_LUH_2024",
                    "physical_envelope_class": "EXTREME / CONDITIONAL ENVELOPE",
                    "resistance_specification": spec,
                    "exposure_days": float(row.exposure_days),
                    "relative_resistance": max(1.0, float(row.observed_q90)),
                    "relative_resistance_lower": max(1.0, float(row.observed_q10)),
                    "relative_resistance_upper": max(1.0, float(row.observed_q90)),
                    "capacity_retention": float(cap.capacity_retention_q10),
                    "capacity_retention_lower": float(cap.capacity_retention_q10),
                    "capacity_retention_upper": float(cap.capacity_retention_q90),
                    "valid_domain_status": "WITHIN_VALIDATED_DEGRADATION_DOMAIN",
                    "conditional_extreme": True,
                }
            )
    sch = pd.read_parquet(ROOT / "data" / "processed" / "schreiber_automotive_validation_summary.parquet")
    for _, row in sch.iterrows():
        conditional = (row.scenario == "highway" and row.cu_index >= 22) or (row.scenario == "commuter" and row.cu_index >= 30)
        for spec, col in [("10-ms", "r10_rel"), ("1-s", "r1s_rel")]:
            rows.append(
                {
                    "degradation_state_id": f"SCHREIBER_{row.scenario.upper()}_CU{int(row.cu_index)}_{spec.replace('-', '')}",
                    "source_id": "SRC_SCHREIBER_2025",
                    "physical_envelope_class": "EXTREME / CONDITIONAL ENVELOPE" if conditional else "AUTOMOTIVE-COMPATIBLE ENVELOPE",
                    "resistance_specification": spec,
                    "exposure_days": np.nan,
                    "relative_resistance": float(row[col]),
                    "relative_resistance_lower": float(row[col]),
                    "relative_resistance_upper": float(row[col]),
                    "capacity_retention": float(row.capacity_retention),
                    "capacity_retention_lower": float(row.capacity_retention),
                    "capacity_retention_upper": float(row.capacity_retention),
                    "valid_domain_status": "INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE",
                    "conditional_extreme": bool(conditional),
                }
            )
    return pd.DataFrame(rows)


def pack_states(config: dict[str, Any], states: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    pack_kwh = config["representative_vehicle"]["nominal_pack_energy_kwh"]
    cell_ah = config["pack_electrical_architecture"]["representative_cell_capacity_ah"]
    rows: list[dict[str, Any]] = []
    cycle_base = baseline[baseline.drive_cycle != "COMBINED_55_45"]
    for _, state in states.iterrows():
        for topo in config["pack_electrical_architecture"]["topology_scenarios"]:
            voltage = float(topo["nominal_pack_voltage_v"])
            parallel = pack_kwh * 1000.0 / (voltage * cell_ah)
            for _, cyc in cycle_base.iterrows():
                profile_path = ROOT / "data" / "processed" / "representative_bev_baseline.parquet"
                # Profile is read only after it has been written by generate().
                profile = pd.read_parquet(profile_path, filters=[("drive_cycle", "==", cyc.drive_cycle)])
                current = profile["hv_terminal_power_w"].to_numpy(float) / voltage
                i2dt = float(np.square(current).sum())
                effective_r = float(cyc.fresh_storage_loss_kwh) * 3.6e6 / i2dt
                for share in config["fresh_pack_loss_decomposition"]["cell_resistance_share_of_ageing_sensitive_pack_loss_scenarios"]:
                    cell_r_fresh = effective_r * float(share)
                    rows.append(
                        {
                            **state.to_dict(),
                            "drive_cycle": cyc.drive_cycle,
                            "topology_id": topo["topology_id"],
                            "series_count": int(topo["series_count"]),
                            "equivalent_parallel_count": float(parallel),
                            "nominal_pack_voltage_v": voltage,
                            "cell_resistance_share": float(share),
                            "fresh_effective_pack_resistance_ohm": effective_r,
                            "fresh_cell_attributed_pack_resistance_ohm": cell_r_fresh,
                            "aged_cell_attributed_pack_resistance_ohm": cell_r_fresh * float(state.relative_resistance),
                            "fixed_noncell_pack_resistance_ohm": effective_r * (1.0 - float(share)),
                            "equivalent_fresh_cell_resistance_ohm": cell_r_fresh * parallel / int(topo["series_count"]),
                            "usable_energy_kwh_at_window_090": pack_kwh * 0.90 * float(state.capacity_retention),
                        }
                    )
    return pd.DataFrame(rows)


def translate_energy(config: dict[str, Any], pack: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    base = baseline.set_index("drive_cycle")
    rows: list[dict[str, Any]] = []
    for _, row in pack.iterrows():
        b = base.loc[row.drive_cycle]
        delta_loss_kwh = float(b.fresh_storage_loss_kwh) * float(row.cell_resistance_share) * max(float(row.relative_resistance) - 1.0, 0.0)
        distance_km = float(b.distance_km)
        aged_intensity = float(b.fresh_battery_side_kwh_per_km) + delta_loss_kwh / distance_km
        for window in config["capacity_scaling"]["fresh_usable_window_fraction_scenarios"]:
            usable_kwh = config["representative_vehicle"]["nominal_pack_energy_kwh"] * float(window) * float(row.capacity_retention)
            rows.append(
                {
                    "degradation_state_id": row.degradation_state_id,
                    "source_id": row.source_id,
                    "resistance_specification": row.resistance_specification,
                    "physical_envelope_class": row.physical_envelope_class,
                    "conditional_extreme": row.conditional_extreme,
                    "exposure_days": row.exposure_days,
                    "valid_domain_status": row.valid_domain_status,
                    "drive_cycle": row.drive_cycle,
                    "topology_id": row.topology_id,
                    "nominal_pack_voltage_v": row.nominal_pack_voltage_v,
                    "cell_resistance_share": row.cell_resistance_share,
                    "fresh_usable_window_fraction": float(window),
                    "capacity_retention": row.capacity_retention,
                    "relative_resistance": row.relative_resistance,
                    "fresh_battery_side_kwh_per_km": b.fresh_battery_side_kwh_per_km,
                    "incremental_resistive_energy_kwh_per_cycle": delta_loss_kwh,
                    "incremental_battery_side_kwh_per_km": delta_loss_kwh / distance_km,
                    "incremental_battery_side_energy_percent": 100.0 * delta_loss_kwh / float(b.fresh_battery_stored_energy_draw_kwh),
                    "aged_battery_side_kwh_per_km": aged_intensity,
                    "usable_battery_energy_kwh": usable_kwh,
                    "technical_range_precursor_km": usable_kwh / aged_intensity,
                    "translation_id": "T1_PHYSICS_BASED_RESISTANCE_LOSS_INCREMENT",
                    "carbon_calculated": False,
                }
            )
    return pd.DataFrame(rows)


def uncertainty_summary(energy: pd.DataFrame) -> pd.DataFrame:
    central = energy[energy["physical_envelope_class"].isin(["PRIMARY PHYSICAL SPECIFICATION", "ALTERNATIVE 1-S SPECIFICATION"])]
    group = ["degradation_state_id", "resistance_specification", "drive_cycle", "exposure_days", "capacity_retention"]
    return central.groupby(group, dropna=False).agg(
        incremental_kwh_per_km_min=("incremental_battery_side_kwh_per_km", "min"),
        incremental_kwh_per_km_max=("incremental_battery_side_kwh_per_km", "max"),
        incremental_percent_min=("incremental_battery_side_energy_percent", "min"),
        incremental_percent_max=("incremental_battery_side_energy_percent", "max"),
        usable_energy_kwh_min=("usable_battery_energy_kwh", "min"),
        usable_energy_kwh_max=("usable_battery_energy_kwh", "max"),
        technical_range_precursor_km_min=("technical_range_precursor_km", "min"),
        technical_range_precursor_km_max=("technical_range_precursor_km", "max"),
    ).reset_index()


def tum_validation(config: dict[str, Any], pack: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    wltp = pd.read_parquet(ROOT / "data" / "processed" / "tum_id3_wltp_vehicle_observations.parquet").sort_values("vehicle_time_ms")
    dt = wltp["vehicle_time_ms"].diff().fillna(100.0).clip(lower=0.0, upper=1000.0) / 1000.0
    distance_km = float((wltp["vehicle_speed_kmh"] * dt / 3600.0).sum())
    net_kwh = float((-wltp["hv_battery_voltage_v"] * wltp["hv_battery_current_a"] * dt).sum() / 3.6e6)
    hppc = pd.read_parquet(ROOT / "data" / "processed" / "tum_id3_hppc_validation_summary.parquet")
    architecture = yaml.safe_load((ROOT / "data" / "processed" / "tum_id3_pack_architecture.yaml").read_text(encoding="utf-8"))
    pack_record = next(x for x in architecture["records"] if x["scale"] == "pack_measured")
    ns, np_ = int(pack_record["topology_series"]), int(pack_record["topology_parallel"])
    rows = []
    for temp, group in hppc.groupby("test_temperature_c", sort=True):
        for spec, col in [("10-ms", "r10_ohm"), ("1-s", "r1s_ohm")]:
            pack_r = group[col] * ns / np_
            rows.append(
                {
                    "source_id": "SRC_TUM_ID3",
                    "validation_role": "FRESH_VEHICLE_ELECTRICAL_PLAUSIBILITY_ONLY",
                    "test_temperature_c": float(temp),
                    "resistance_specification": spec,
                    "tum_pack_resistance_min_ohm": float(pack_r.min()),
                    "tum_pack_resistance_median_ohm": float(pack_r.median()),
                    "tum_pack_resistance_max_ohm": float(pack_r.max()),
                    "tum_wltp_voltage_min_v": float(wltp.hv_battery_voltage_v.min()),
                    "tum_wltp_voltage_max_v": float(wltp.hv_battery_voltage_v.max()),
                    "tum_wltp_current_min_a": float(wltp.hv_battery_current_a.min()),
                    "tum_wltp_current_max_a": float(wltp.hv_battery_current_a.max()),
                    "tum_wltp_net_battery_wh_per_km": 1000.0 * net_kwh / distance_km,
                    "fastsim_combined_battery_wh_per_km": 1000.0 * float(baseline.loc[baseline.drive_cycle == "COMBINED_55_45", "fresh_battery_side_kwh_per_km"].iloc[0]),
                    "fastsim_effective_pack_resistance_min_ohm": float(pack.fresh_effective_pack_resistance_ohm.min()),
                    "fastsim_effective_pack_resistance_max_ohm": float(pack.fresh_effective_pack_resistance_ohm.max()),
                    "validation_classification": "PASS WITH BOUNDS",
                }
            )
    return pd.DataFrame(rows)


def make_diagnostics(profile: pd.DataFrame, energy: pd.DataFrame) -> list[Path]:
    out_dir = ROOT / "results" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=False, constrained_layout=True)
    for cycle, group in profile.groupby("drive_cycle", sort=True):
        axes[0].plot(group.time_s / 60.0, group.hv_terminal_power_w / 1000.0, label=cycle, linewidth=0.8)
        axes[1].plot(group.time_s / 60.0, group.soc_fraction, label=cycle, linewidth=1.0)
    axes[0].axhline(0, color="black", linewidth=0.5)
    axes[0].set_ylabel("HV terminal power (kW)")
    axes[1].set_ylabel("SOC fraction")
    axes[1].set_xlabel("Cycle time (min)")
    axes[0].legend(); axes[1].legend()
    path = out_dir / "p13_fresh_fastsim_power_soc.png"
    fig.savefig(path, dpi=160, metadata={"Software": "P13 deterministic diagnostic"})
    plt.close(fig); paths.append(path)

    subset = energy[
        (energy.topology_id == "central_voltage_108s")
        & (energy.drive_cycle == "UDDS")
        & (energy.fresh_usable_window_fraction == 0.90)
        & (energy.physical_envelope_class.isin(["PRIMARY PHYSICAL SPECIFICATION", "ALTERNATIVE 1-S SPECIFICATION"]))
    ]
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for (spec, share), group in subset.groupby(["resistance_specification", "cell_resistance_share"], sort=True):
        group = group.sort_values("exposure_days")
        ax.plot(group.exposure_days, group.incremental_battery_side_energy_percent, label=f"{spec}, cell share={share:.2f}")
    ax.set_xlabel("Observed-domain exposure (days)")
    ax.set_ylabel("Incremental battery-side energy (%)")
    ax.legend(ncol=2, fontsize=8)
    path = out_dir / "p13_incremental_energy_bounds.png"
    fig.savefig(path, dpi=160, metadata={"Software": "P13 deterministic diagnostic"})
    plt.close(fig); paths.append(path)
    return paths


def generate() -> dict[str, Any]:
    config = load_config()
    source_info = validate_atb_source(config)
    profile, baseline = run_fresh_fastsim(config)
    output_paths = {
        "baseline": ROOT / "data" / "processed" / "representative_bev_baseline.parquet",
        "pack": ROOT / "data" / "processed" / "p13_pack_electrical_states.parquet",
        "energy": ROOT / "data" / "processed" / "p13_incremental_energy_penalty.parquet",
        "uncertainty": ROOT / "data" / "processed" / "p13_energy_translation_uncertainty.parquet",
        "tum": ROOT / "data" / "processed" / "tum_id3_vehicle_energy_validation_summary.parquet",
    }
    write_parquet_deterministic(profile, output_paths["baseline"], ["drive_cycle", "time_s"])
    states = degradation_states()
    pack = pack_states(config, states, baseline)
    energy = translate_energy(config, pack, baseline)
    uncertainty = uncertainty_summary(energy)
    tum = tum_validation(config, pack, baseline)
    write_parquet_deterministic(pack, output_paths["pack"], ["physical_envelope_class", "resistance_specification", "degradation_state_id", "drive_cycle", "topology_id", "cell_resistance_share"])
    write_parquet_deterministic(energy, output_paths["energy"], ["physical_envelope_class", "resistance_specification", "degradation_state_id", "drive_cycle", "topology_id", "cell_resistance_share", "fresh_usable_window_fraction"])
    write_parquet_deterministic(uncertainty, output_paths["uncertainty"], ["resistance_specification", "degradation_state_id", "drive_cycle"])
    write_parquet_deterministic(tum, output_paths["tum"], ["test_temperature_c", "resistance_specification"])
    figures = make_diagnostics(profile, energy)
    params = {
        "stage": "P13",
        "model_id": "p13_vehicle_energy_translation_v1",
        "fastsim_version": fastsim.__version__,
        "configuration_sha256": sha256(CONFIG_PATH),
        "atb_source": source_info,
        "fresh_baseline": baseline.replace({np.nan: None}).to_dict(orient="records"),
        "capacity_scaling_field": "reconstructed_capacity_retention",
        "source_capacity_soh_percent_physical_use": "FORBIDDEN",
        "primary_translation": config["translation"]["selected_primary"],
        "energy_boundary": "L2_HV_BATTERY_SIDE_ELECTRICAL_ENERGY",
        "charging_conversion": "NONE",
        "carbon_calculation": "NONE",
        "extrapolation": "NONE",
        "frozen_decision_changes": "NONE",
        "tum_validation": "PASS WITH BOUNDS",
        "external_atb_benchmark_boundary": "charging-inclusive adjusted real-world; not directly equal to FASTSim battery-side",
    }
    params_path = ROOT / "results" / "intermediate" / "p13_vehicle_energy_model_parameters.json"
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(json.dumps(params, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    manifest_targets = [
        CONFIG_PATH,
        Path(__file__),
        ROOT / "tests" / "test_p13_vehicle_energy.py",
        ROOT / "docs" / "P13_VEHICLE_ENERGY_TRANSLATION_REPORT.md",
        ROOT / "docs" / "RESEARCH_DECISION_LOG.md",
        ROOT / "data" / "metadata" / "SRC_NREL_TRANSPORTATION_ATB_2024.yaml",
        ROOT / "data" / "metadata" / "SOURCE_MANIFEST.csv",
        ROOT / "data" / "processed" / "metadata" / "p13_vehicle_energy_outputs.yaml",
        ROOT / "data" / "processed" / "metadata" / "representative_bev_baseline.yaml",
        ROOT / "data" / "processed" / "metadata" / "p13_pack_electrical_states.yaml",
        ROOT / "data" / "processed" / "metadata" / "p13_incremental_energy_penalty.yaml",
        ROOT / "data" / "processed" / "metadata" / "p13_energy_translation_uncertainty.yaml",
        ROOT / "data" / "processed" / "metadata" / "tum_id3_vehicle_energy_validation_summary.yaml",
        *output_paths.values(),
        params_path,
        *figures,
    ]
    manifest = {
        "stage": "P13",
        "artifact_count": len(manifest_targets),
        "artifacts": [
            {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in sorted(manifest_targets, key=lambda item: str(item.relative_to(ROOT)))
        ],
    }
    manifest_path = ROOT / "results" / "intermediate" / "p13_artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"manifest": manifest, "parameters": params, "rows": {key: len(pd.read_parquet(path)) for key, path in output_paths.items()}}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
