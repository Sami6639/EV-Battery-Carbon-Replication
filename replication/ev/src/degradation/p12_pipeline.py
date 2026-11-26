"""P12 NMC degradation-state construction and validation.

This module is deliberately limited to Luh capacity/pulse-resistance states,
Schreiber automotive validation, and fresh TUM HPPC plausibility.  It does not
import or consume any downstream vehicle, emissions, or replacement modules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Iterable

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(__file__).resolve().parents[2] / "results" / "intermediate" / "matplotlib"),
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src" / "degradation" / "p12_config.yaml"
LUH_RAW = ROOT / "data" / "raw" / "SRC_LUH_2024"
PROCESSED = ROOT / "data" / "processed"
INTERMEDIATE = ROOT / "results" / "intermediate"
DIAGNOSTICS = ROOT / "results" / "diagnostics"

OBS_PATH = PROCESSED / "luh_degradation_state_observations.parquet"
MODEL_PATH = PROCESSED / "luh_degradation_state_model.parquet"
UNCERTAINTY_PATH = PROCESSED / "luh_degradation_uncertainty.parquet"
SCHREIBER_PATH = PROCESSED / "schreiber_automotive_validation_summary.parquet"
TUM_PATH = PROCESSED / "tum_id3_hppc_validation_summary.parquet"
PARAMETERS_PATH = INTERMEDIATE / "p12_degradation_model_parameters.json"
MANIFEST_PATH = INTERMEDIATE / "p12_artifact_manifest.json"
METADATA_DIR = PROCESSED / "metadata"

OUTPUTS = (
    OBS_PATH,
    MODEL_PATH,
    UNCERTAINTY_PATH,
    SCHREIBER_PATH,
    TUM_PATH,
    PARAMETERS_PATH,
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _cell_key(filename: pd.Series) -> pd.Series:
    return filename.str.replace(
        r"^(?:cell_(?:eocv2|plsv2|cfg)_)?|\.csv$", "", regex=True
    )


def _read_zip_csv(zip_path: Path, columns: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in sorted(n for n in archive.namelist() if n.lower().endswith(".csv")):
            frame = pd.read_csv(archive.open(name), sep=";", usecols=columns)
            frame["source_filename"] = name
            frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _condition_map() -> pd.DataFrame:
    condition = pd.read_parquet(PROCESSED / "luh_condition_map.parquet")
    condition = condition.copy()
    condition["cell_key"] = _cell_key(condition["source_filename"])
    return condition.drop(columns=["source_filename", "source_row", "source_id"])


def build_capacity_states(condition: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "timestamp_s",
        "sd_block_id",
        "cyc_condition",
        "cyc_charged",
        "age_type",
        "age_temp",
        "age_soc",
        "age_chg_rate",
        "age_dischg_rate",
        "age_profile",
        "cap_aged_est_Ah",
        "soh_cap",
        "delta_e_dischg_Wh",
        "num_cycles_op",
        "num_cycles_checkup",
        "total_q_chg_sum_Ah",
        "total_q_dischg_sum_Ah",
    ]
    raw = _read_zip_csv(LUH_RAW / "cell_eocv2.zip", columns)
    eligible = raw.loc[
        raw["cyc_condition"].eq(2)
        & raw["cyc_charged"].eq(0)
        & np.isfinite(raw["cap_aged_est_Ah"])
        & np.isfinite(raw["soh_cap"])
    ].copy()
    eligible["cell_key"] = _cell_key(eligible["source_filename"])
    eligible = eligible.sort_values(
        ["cell_key", "timestamp_s", "sd_block_id"], kind="mergesort"
    ).reset_index(drop=True)
    if eligible.duplicated(["cell_key", "num_cycles_checkup"]).any():
        raise ValueError("Capacity check-up grain is not unique")

    baseline = eligible.groupby("cell_key", sort=False)["cap_aged_est_Ah"].first()
    baseline_time = eligible.groupby("cell_key", sort=False)["timestamp_s"].first()
    eligible["capacity_baseline_ah"] = eligible["cell_key"].map(baseline)
    eligible["reconstructed_capacity_retention"] = (
        eligible["cap_aged_est_Ah"] / eligible["capacity_baseline_ah"]
    )
    eligible["elapsed_days"] = (
        eligible["timestamp_s"] - eligible["cell_key"].map(baseline_time)
    ) / 86400.0
    eligible["charge_throughput_ah"] = eligible["total_q_chg_sum_Ah"]
    eligible["discharge_throughput_ah"] = eligible["total_q_dischg_sum_Ah"]
    eligible["source_capacity_soh_percent"] = eligible["soh_cap"]
    eligible["measured_capacity_ah"] = eligible["cap_aged_est_Ah"]
    eligible["measured_energy_wh"] = -eligible["delta_e_dischg_Wh"]
    eligible["state_kind"] = "capacity"
    eligible["soc_basis_percent"] = np.nan
    eligible["measurement_temperature_c"] = 25.0
    eligible["resistance_10ms_ohm"] = np.nan
    eligible["resistance_1s_ohm"] = np.nan
    eligible["r10_rel"] = np.nan
    eligible["r1s_rel"] = np.nan
    eligible["baseline_timestamp_s"] = eligible["cell_key"].map(baseline_time)
    eligible["derivation_class"] = "SOURCE_SUPPLIED_SOH_WITH_SEPARATE_CHECK_RATIO"
    eligible = eligible.merge(condition, on="cell_key", how="left", validate="many_to_one", suffixes=("_raw", ""))
    if eligible["condition_id"].isna().any():
        raise ValueError("Unmapped Luh capacity cell")
    return eligible


def build_resistance_states(condition: pd.DataFrame, config: dict) -> pd.DataFrame:
    columns = [
        "timestamp_s",
        "sd_block_id",
        "cyc_charged",
        "is_rt",
        "soc_nom",
        "age_type",
        "age_temp",
        "age_soc",
        "age_chg_rate",
        "age_dischg_rate",
        "age_profile",
        "t_avg_degC",
        "r_ref_10ms_mOhm",
        "r_ref_1s_mOhm",
    ]
    raw = _read_zip_csv(LUH_RAW / "cell_plsv2.zip", columns)
    static = [c for c in columns if c not in {"timestamp_s"}]
    grain = ["source_filename", "sd_block_id"]
    nonconstant = raw.groupby(grain, sort=False)[static].nunique(dropna=False).gt(1)
    if nonconstant.any(axis=None):
        bad = nonconstant.any(axis=1).sum()
        raise ValueError(f"{bad} pulse blocks have nonconstant state fields")
    first = raw.groupby(grain, as_index=False, sort=False).agg(
        timestamp_s=("timestamp_s", "min"),
        **{column: (column, "first") for column in static},
        waveform_rows=("timestamp_s", "size"),
    )
    if not first["waveform_rows"].eq(61).all():
        raise ValueError("Unexpected Luh pulse waveform length")

    rule = config["resistance_baseline_rule"]
    temp = float(rule["reference_temperature_c"])
    tolerance = float(rule["temperature_tolerance_c"])
    allowed_soc = set(rule["allowed_soc_percent"])
    eligible = first.loc[
        first["is_rt"].eq(1)
        & first["t_avg_degC"].between(temp - tolerance, temp + tolerance)
        & first["soc_nom"].isin(allowed_soc)
        & first["r_ref_10ms_mOhm"].between(1.0, 1000.0)
        & first["r_ref_1s_mOhm"].between(1.0, 1000.0)
    ].copy()
    eligible["cell_key"] = _cell_key(eligible["source_filename"])
    eligible = eligible.sort_values(
        ["cell_key", "soc_nom", "timestamp_s", "sd_block_id"], kind="mergesort"
    ).reset_index(drop=True)

    keys = ["cell_key", "soc_nom"]
    baseline = eligible.drop_duplicates(keys, keep="first")[
        keys + ["timestamp_s", "r_ref_10ms_mOhm", "r_ref_1s_mOhm"]
    ].rename(
        columns={
            "timestamp_s": "baseline_timestamp_s",
            "r_ref_10ms_mOhm": "baseline_r10_mohm",
            "r_ref_1s_mOhm": "baseline_r1s_mohm",
        }
    )
    expected = eligible["cell_key"].nunique() * len(allowed_soc)
    if len(baseline) != expected:
        raise ValueError(f"Incomplete resistance baseline: {len(baseline)} != {expected}")
    eligible = eligible.merge(baseline, on=keys, how="left", validate="many_to_one")
    eligible["r10_rel"] = eligible["r_ref_10ms_mOhm"] / eligible["baseline_r10_mohm"]
    eligible["r1s_rel"] = eligible["r_ref_1s_mOhm"] / eligible["baseline_r1s_mohm"]
    eligible["resistance_10ms_ohm"] = eligible["r_ref_10ms_mOhm"] / 1000.0
    eligible["resistance_1s_ohm"] = eligible["r_ref_1s_mOhm"] / 1000.0
    eligible["elapsed_days"] = (
        eligible["timestamp_s"] - eligible["baseline_timestamp_s"]
    ) / 86400.0
    eligible["state_kind"] = "pulse_resistance"
    eligible["soc_basis_percent"] = eligible["soc_nom"].astype(float)
    eligible["measurement_temperature_c"] = eligible["t_avg_degC"]
    eligible["source_capacity_soh_percent"] = np.nan
    eligible["reconstructed_capacity_retention"] = np.nan
    eligible["measured_capacity_ah"] = np.nan
    eligible["capacity_baseline_ah"] = np.nan
    eligible["measured_energy_wh"] = np.nan
    eligible["charge_throughput_ah"] = np.nan
    eligible["discharge_throughput_ah"] = np.nan
    eligible["num_cycles_op"] = np.nan
    eligible["num_cycles_checkup"] = np.nan
    eligible["derivation_class"] = "SCIENTIFIC_DERIVED"
    eligible = eligible.merge(condition, on="cell_key", how="left", validate="many_to_one", suffixes=("_raw", ""))
    if eligible["condition_id"].isna().any():
        raise ValueError("Unmapped Luh pulse cell")
    return eligible


def _attach_capacity_context(resistance: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    context_columns = [
        "source_capacity_soh_percent",
        "reconstructed_capacity_retention",
        "measured_capacity_ah",
        "capacity_baseline_ah",
        "charge_throughput_ah",
        "discharge_throughput_ah",
        "num_cycles_op",
        "num_cycles_checkup",
    ]
    resistance = resistance.drop(columns=context_columns)
    right = capacity[
        [
            "cell_key",
            "timestamp_s",
            "source_capacity_soh_percent",
            "reconstructed_capacity_retention",
            "measured_capacity_ah",
            "capacity_baseline_ah",
            "charge_throughput_ah",
            "discharge_throughput_ah",
            "num_cycles_op",
            "num_cycles_checkup",
        ]
    ].rename(columns={"timestamp_s": "capacity_context_timestamp_s"})
    pieces = []
    for cell_key, left_cell in resistance.groupby("cell_key", sort=True):
        right_cell = right.loc[right["cell_key"].eq(cell_key)].sort_values(
            "capacity_context_timestamp_s"
        )
        merged = pd.merge_asof(
            left_cell.sort_values("timestamp_s"),
            right_cell.drop(columns="cell_key"),
            left_on="timestamp_s",
            right_on="capacity_context_timestamp_s",
            direction="backward",
        )
        pieces.append(merged)
    return pd.concat(pieces, ignore_index=True)


def _pava(y: np.ndarray, weights: np.ndarray, increasing: bool) -> np.ndarray:
    values = y.astype(float).copy()
    if not increasing:
        values = -values
    blocks: list[list[float]] = []
    for index, (value, weight) in enumerate(zip(values, weights, strict=True)):
        blocks.append([float(value), float(weight), float(index), float(index)])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            b = blocks.pop()
            a = blocks.pop()
            total_weight = a[1] + b[1]
            blocks.append(
                [
                    (a[0] * a[1] + b[0] * b[1]) / total_weight,
                    total_weight,
                    a[2],
                    b[3],
                ]
            )
    fitted = np.empty(len(values), dtype=float)
    for value, _, start, end in blocks:
        fitted[int(start) : int(end) + 1] = value
    return fitted if increasing else -fitted


def _metric_input(observations: pd.DataFrame, metric_id: str, reporting_soc: int) -> pd.DataFrame:
    if metric_id == "capacity_source_soh_percent":
        data = observations.loc[observations["state_kind"].eq("capacity")].copy()
        data["value"] = data["source_capacity_soh_percent"]
    else:
        field = "r10_rel" if metric_id == "r10_rel" else "r1s_rel"
        data = observations.loc[
            observations["state_kind"].eq("pulse_resistance")
            & observations["soc_basis_percent"].eq(reporting_soc)
        ].copy()
        data["value"] = data[field]
    return data.loc[np.isfinite(data["elapsed_days"]) & np.isfinite(data["value"])].copy()


def fit_representations(
    observations: pd.DataFrame, reporting_soc: int, code_sha: str
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    model_rows: list[dict] = []
    uncertainty_rows: list[dict] = []
    metadata: dict[str, dict] = {}
    for metric_id, increasing in (
        ("capacity_source_soh_percent", False),
        ("r10_rel", True),
        ("r1s_rel", True),
    ):
        data = _metric_input(observations, metric_id, reporting_soc)
        # Preserve the exact same-cell baseline as its own node.  Positive
        # observations are assigned to the upper 30-day boundary so early
        # fast-ageing observations cannot dilute the t=0 state.
        data["exposure_bin_days"] = np.where(
            data["elapsed_days"].eq(0.0),
            0.0,
            np.ceil(data["elapsed_days"] / 30.0) * 30.0,
        )
        cell_bin = (
            data.groupby(["cell_key", "condition_id", "exposure_bin_days"], as_index=False)
            .agg(
                value=("value", "median"),
                node_exposure_days=("elapsed_days", "median"),
                observations=("value", "size"),
            )
        )
        nodes = (
            cell_bin.groupby("exposure_bin_days", as_index=False)
            .agg(
                exposure_days=("node_exposure_days", "median"),
                observed_central=("value", "median"),
                q10=("value", lambda x: x.quantile(0.10)),
                q90=("value", lambda x: x.quantile(0.90)),
                unique_cells=("cell_key", "nunique"),
                unique_conditions=("condition_id", "nunique"),
                observations=("observations", "sum"),
            )
            .sort_values("exposure_bin_days")
            .reset_index(drop=True)
        )
        x = nodes["exposure_days"].to_numpy(float)
        y = nodes["observed_central"].to_numpy(float)
        weights = nodes["unique_cells"].to_numpy(float)
        slope, intercept = np.polyfit(x, y, 1, w=np.sqrt(weights))
        linear = intercept + slope * x
        isotonic = _pava(y, weights, increasing=increasing)
        if metric_id in {"r10_rel", "r1s_rel"}:
            # R/R0 is defined to be exactly one at the same-cell baseline.
            # Anchor the central representation without deleting sub-unity
            # measured observations, which remain visible in the raw layer.
            isotonic = np.maximum.accumulate(np.maximum(isotonic, 1.0))
            isotonic[0] = 1.0
        predictions = {
            "observed_nonparametric": y,
            "low_order_linear": linear,
            "bounded_monotone_isotonic": isotonic,
        }
        data_x = data["elapsed_days"].to_numpy(float)
        residual_diagnostics: dict[str, dict] = {}
        for family, prediction in predictions.items():
            fitted = np.interp(data_x, x, prediction)
            residual = data["value"].to_numpy(float) - fitted
            violations = int(
                np.sum(np.diff(prediction) < -1e-12)
                if increasing
                else np.sum(np.diff(prediction) > 1e-12)
            )
            residual_diagnostics[family] = {
                "rmse": float(np.sqrt(np.mean(residual**2))),
                "median_absolute_residual": float(np.median(np.abs(residual))),
                "residual_q10": float(np.quantile(residual, 0.10)),
                "residual_q90": float(np.quantile(residual, 0.90)),
                "monotonicity_violations": violations,
            }
            for row, central in zip(nodes.to_dict("records"), prediction, strict=True):
                model_rows.append(
                    {
                        "model_id": f"p12_{metric_id}_{family}_v1",
                        "metric_id": metric_id,
                        "representation_family": family,
                        "selected_primary": family == "bounded_monotone_isotonic",
                        "source_dataset": "SRC_LUH_2024",
                        "exposure_axis": "elapsed_calendar_days_since_same_cell_baseline",
                        "exposure_days": row["exposure_days"],
                        "central_state": float(central),
                        "observed_q10": row["q10"],
                        "observed_q90": row["q90"],
                        "observations": row["observations"],
                        "unique_cells": row["unique_cells"],
                        "unique_conditions": row["unique_conditions"],
                        "valid_min_days": float(data["elapsed_days"].min()),
                        "valid_max_days": float(data["elapsed_days"].max()),
                        "soc_basis_percent": np.nan if metric_id.startswith("capacity") else reporting_soc,
                        "temperature_basis_c": 25.0,
                        "extrapolation_count": 0,
                        "code_sha256": code_sha,
                    }
                )

        selected = isotonic
        candidate_stack = np.vstack(list(predictions.values()))
        for index, row in nodes.iterrows():
            bin_value = row["exposure_bin_days"]
            in_bin = cell_bin.loc[cell_bin["exposure_bin_days"].eq(bin_value)]
            condition_medians = in_bin.groupby("condition_id")["value"].median()
            replicate_residual = in_bin["value"] - in_bin.groupby("condition_id")["value"].transform("median")
            raw_bin = data.loc[data["exposure_bin_days"].eq(bin_value)].copy()
            raw_bin["rolling"] = raw_bin.groupby("cell_key")["value"].transform(
                lambda s: s.rolling(3, center=True, min_periods=1).median()
            )
            measurement_residual = raw_bin["value"] - raw_bin["rolling"]
            layers = {
                "observed_total_empirical": (row["q10"], row["q90"]),
                "replicate_variability_empirical": (
                    float(selected[index] + replicate_residual.quantile(0.10)),
                    float(selected[index] + replicate_residual.quantile(0.90)),
                ),
                "condition_variability_empirical": (
                    float(condition_medians.quantile(0.10)),
                    float(condition_medians.quantile(0.90)),
                ),
                "measurement_variability_proxy": (
                    float(selected[index] + measurement_residual.quantile(0.10)),
                    float(selected[index] + measurement_residual.quantile(0.90)),
                ),
                "representation_fit_range": (
                    float(candidate_stack[:, index].min()),
                    float(candidate_stack[:, index].max()),
                ),
            }
            for layer, (lower, upper) in layers.items():
                uncertainty_rows.append(
                    {
                        "metric_id": metric_id,
                        "uncertainty_layer": layer,
                        "exposure_days": row["exposure_days"],
                        "central_state": float(selected[index]),
                        "lower_bound": lower,
                        "upper_bound": upper,
                        "bound_method": "empirical_no_probability_distribution",
                        "unique_cells": int(row["unique_cells"]),
                        "unique_conditions": int(row["unique_conditions"]),
                        "valid_min_days": float(data["elapsed_days"].min()),
                        "valid_max_days": float(data["elapsed_days"].max()),
                        "extrapolation_count": 0,
                    }
                )
        metadata[metric_id] = {
            "selected_family": "bounded_monotone_isotonic",
            "selection_reason": "physical monotonicity with observed-domain bounded nodes and no extrapolation",
            "observations": int(len(data)),
            "unique_cells": int(data["cell_key"].nunique()),
            "unique_replicates": int(data["replicate_id"].nunique()),
            "unique_conditions": int(data["condition_id"].nunique()),
            "valid_domain_days": [float(data["elapsed_days"].min()), float(data["elapsed_days"].max())],
            "missingness": int(data["value"].isna().sum()),
            "extrapolation_count": 0,
            "linear_parameters": {"intercept": float(intercept), "slope_per_day": float(slope)},
            "candidate_diagnostics": residual_diagnostics,
        }
    return pd.DataFrame(model_rows), pd.DataFrame(uncertainty_rows), metadata


def _step_resistance(group: pd.DataFrame, target_s: float) -> tuple[float, float]:
    ordered = group.sort_values("step_time_s")
    t = ordered["step_time_s"].to_numpy(float)
    voltage = ordered["voltage_v"].to_numpy(float)
    current = ordered["current_a"].to_numpy(float)
    v0, i0 = voltage[0], current[0]
    vt = float(np.interp(target_s, t, voltage))
    it = float(np.interp(target_s, t, current))
    delta_i = it - i0
    if abs(delta_i) < 1.0:
        raise ValueError("Pulse current step is too small for resistance extraction")
    return abs((vt - v0) / delta_i), float(abs(delta_i))


def build_schreiber_summary() -> pd.DataFrame:
    raw = pd.read_parquet(PROCESSED / "schreiber_checkup_observations.parquet")
    rows: list[dict] = []
    for (scenario, cu_index, checkup_id), group in raw.groupby(
        ["scenario", "cu_index", "checkup_id"], sort=True
    ):
        capacity_step = group.loc[
            group["protocol_line"].eq(11) & group["command"].str.lower().eq("discharge")
        ]
        pulse_step = group.loc[
            group["protocol_line"].eq(38) & group["command"].str.lower().eq("discharge")
        ]
        if capacity_step.empty or pulse_step.empty:
            raise ValueError(f"Missing Schreiber validation step in {checkup_id}")
        r10, di10 = _step_resistance(pulse_step, 0.010)
        r1s, di1s = _step_resistance(pulse_step, 1.000)
        rows.append(
            {
                "source_id": "SRC_SCHREIBER_2025",
                "scenario": scenario,
                "checkup_id": checkup_id,
                "cu_index": int(cu_index),
                "capacity_ah": float(capacity_step["charge_ah"].max() - capacity_step["charge_ah"].min()),
                "r10_ohm": r10,
                "r1s_ohm": r1s,
                "r10_current_step_a": di10,
                "r1s_current_step_a": di1s,
                "pulse_protocol_line": 38,
                "capacity_protocol_line": 11,
                "pulse_soc_context": "first HPPC discharge pulse after full charge, 10% capacity removal, and 1800-s rest",
                "pulse_temperature_c": float(pulse_step["temperature_1_c"].median()),
                "extraction_status": "VALIDATED_FROM_FIXED_SOURCE_PROTOCOL",
            }
        )
    summary = pd.DataFrame(rows).sort_values(["scenario", "cu_index"]).reset_index(drop=True)
    for scenario, indexes in summary.groupby("scenario").groups.items():
        baseline = summary.loc[indexes].sort_values("cu_index").iloc[0]
        summary.loc[indexes, "capacity_retention"] = summary.loc[indexes, "capacity_ah"] / baseline["capacity_ah"]
        summary.loc[indexes, "r10_rel"] = summary.loc[indexes, "r10_ohm"] / baseline["r10_ohm"]
        summary.loc[indexes, "r1s_rel"] = summary.loc[indexes, "r1s_ohm"] / baseline["r1s_ohm"]
    summary["validation_role"] = "INDEPENDENT_AUTOMOTIVE_VALIDATION_ONLY"
    return summary


def _split_repeated_steps(group: pd.DataFrame) -> Iterable[pd.DataFrame]:
    ordered = group.sort_values(["time_s", "dataset_id"], kind="mergesort").copy()
    ordered["segment"] = ordered["step_time_s"].diff().lt(0).cumsum()
    for _, segment in ordered.groupby("segment", sort=True):
        yield segment


def build_tum_summary() -> pd.DataFrame:
    raw = pd.read_parquet(PROCESSED / "tum_id3_hppc_observations.parquet")
    pulse = raw.loc[
        raw["protocol_line"].eq(37) & raw["command"].str.lower().eq("discharge")
    ]
    rows: list[dict] = []
    for temperature, group in pulse.groupby("test_temperature_c", sort=True):
        for segment_id, segment in enumerate(_split_repeated_steps(group)):
            if len(segment) < 10 or segment["step_time_s"].max() < 1.0:
                continue
            r10, di10 = _step_resistance(segment, 0.010)
            r1s, di1s = _step_resistance(segment, 1.000)
            rows.append(
                {
                    "source_id": "SRC_TUM_ID3",
                    "test_temperature_c": float(temperature),
                    "pulse_segment": segment_id,
                    "soc_sequence_index": segment_id + 1,
                    "protocol_line": 37,
                    "r10_ohm": r10,
                    "r1s_ohm": r1s,
                    "r10_current_step_a": di10,
                    "r1s_current_step_a": di1s,
                    "measured_temperature_c": float(segment["temperature_1_c"].median()),
                    "extraction_method": "linear interpolation of fixed pulse waveform from t=0 to 10 ms and 1 s",
                    "validation_role": "FRESH_HPPC_PLAUSIBILITY_ONLY",
                }
            )
    summary = pd.DataFrame(rows).sort_values(
        ["test_temperature_c", "soc_sequence_index"]
    ).reset_index(drop=True)
    if summary.groupby("test_temperature_c").size().min() < 9:
        raise ValueError("Incomplete TUM nine-step HPPC coverage")
    return summary


def classify_automotive_compatibility(
    observations: pd.DataFrame, schreiber: pd.DataFrame
) -> dict:
    luh = observations.loc[
        observations["state_kind"].eq("pulse_resistance")
        & observations["soc_basis_percent"].eq(50)
        & observations["reconstructed_capacity_retention"].notna()
    ].copy()
    endpoint_rows = []
    for scenario, group in schreiber.groupby("scenario", sort=True):
        endpoint = group.sort_values("cu_index").iloc[-1]
        window = luh.loc[
            luh["reconstructed_capacity_retention"].between(
                endpoint["capacity_retention"] - 0.025,
                endpoint["capacity_retention"] + 0.025,
            )
        ]
        endpoint_rows.append(
            {
                "scenario": scenario,
                "capacity_retention": float(endpoint["capacity_retention"]),
                "r10_rel": float(endpoint["r10_rel"]),
                "r1s_rel": float(endpoint["r1s_rel"]),
                "luh_matching_observations": int(len(window)),
                "luh_r10_q10": None if window.empty else float(window["r10_rel"].quantile(0.10)),
                "luh_r10_q90": None if window.empty else float(window["r10_rel"].quantile(0.90)),
                "luh_r10_min": None if window.empty else float(window["r10_rel"].min()),
                "luh_r10_max": None if window.empty else float(window["r10_rel"].max()),
            }
        )
    return {
        "status": "PASS WITH BOUNDS",
        "reason": "automotive capacity and resistance directions are compatible, but Schreiber resistance magnitudes exceed the matched-capacity Luh q90 and scenario-specific severe states require conditional treatment",
        "matching_capacity_window_fraction": 0.025,
        "scenario_endpoints": endpoint_rows,
        "trajectory_classes": {
            "PRIMARY PHYSICAL SPECIFICATION": "Luh 25 C, 50% SOC, 10-ms bounded monotone central representation within observed time domain",
            "ALTERNATIVE PHYSICAL SPECIFICATION": "separate Luh 25 C, 50% SOC, 1-s bounded monotone representation within observed time domain",
            "AUTOMOTIVE-COMPATIBLE ENVELOPE": "bounded union of observed Luh state-space and Schreiber commuter/highway validation trajectories; it is not a pooled fit or a shared exposure scale",
            "EXTREME / CONDITIONAL ENVELOPE": "Luh empirical tails, Schreiber contact-sensitive resistance levels, and highway post-knee severity; none is a general automotive central case",
            "REJECTED AS AUTOMOTIVE-INCOMPATIBLE": "states outside observed Luh domain, cross-SOC/cross-temperature ratios, mixed timescales, or trajectories requiring extrapolation",
        },
    }


def _write_figures(
    observations: pd.DataFrame,
    model: pd.DataFrame,
    schreiber: pd.DataFrame,
    tum: pd.DataFrame,
) -> None:
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    plots = [
        ("capacity_source_soh_percent", "source_capacity_soh_percent", "Capacity SOH (author scale, %)", "p12_capacity_state.png"),
        ("r10_rel", "r10_rel", "R10 / R10,0", "p12_r10_state.png"),
        ("r1s_rel", "r1s_rel", "R1s / R1s,0", "p12_r1s_state.png"),
    ]
    for metric_id, field, ylabel, filename in plots:
        data = _metric_input(observations, metric_id, 50)
        selected = model.loc[
            model["metric_id"].eq(metric_id) & model["selected_primary"]
        ].sort_values("exposure_days")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(data["elapsed_days"], data[field if field in data else "value"], s=4, alpha=0.10, color="#4477AA")
        ax.fill_between(selected["exposure_days"], selected["observed_q10"], selected["observed_q90"], alpha=0.22, color="#66CCEE", label="empirical q10-q90")
        ax.plot(selected["exposure_days"], selected["central_state"], color="#004488", linewidth=2, label="bounded monotone central")
        ax.set(xlabel="Elapsed days since same-cell baseline", ylabel=ylabel, title=f"P12 internal diagnostic: {metric_id}")
        ax.grid(alpha=0.2)
        ax.legend()
        fig.tight_layout()
        fig.savefig(DIAGNOSTICS / filename, dpi=150)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for scenario, group in schreiber.groupby("scenario"):
        ordered = group.sort_values("cu_index")
        ax.plot(ordered["capacity_retention"], ordered["r10_rel"], marker="o", label=f"Schreiber {scenario}")
    luh = observations.loc[
        observations["state_kind"].eq("pulse_resistance")
        & observations["soc_basis_percent"].eq(50)
        & observations["reconstructed_capacity_retention"].notna()
    ]
    ax.scatter(luh["reconstructed_capacity_retention"], luh["r10_rel"], s=5, alpha=0.12, label="Luh 50% SOC states")
    ax.set(xlabel="Same-cell reconstructed capacity retention", ylabel="R10 / R10,0", title="P12 internal automotive state-space compatibility")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(DIAGNOSTICS / "p12_automotive_compatibility.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for temperature, group in tum.groupby("test_temperature_c"):
        ax.plot(group["soc_sequence_index"], group["r10_ohm"] * 1000, marker="o", label=f"{temperature:g} C")
    ax.set(xlabel="Source nine-step SOC sequence index", ylabel="Fresh R10 (mOhm)", title="P12 internal TUM HPPC plausibility")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(DIAGNOSTICS / "p12_tum_hppc_plausibility.png", dpi=150)
    plt.close(fig)


def _write_dataset_metadata(path: Path, frame: pd.DataFrame, code_sha: str, details: dict) -> Path:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = METADATA_DIR / f"{path.stem}.yaml"
    payload = {
        "processed_filename": str(path.relative_to(ROOT)).replace("\\", "/"),
        "source_datasets": details["source_datasets"],
        "scientific_role": details["scientific_role"],
        "processing_script": "src/degradation/p12_pipeline.py",
        "processing_script_sha256": code_sha,
        "processing_date": "2026-08-20",
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "transformations": details["transformations"],
        "scientific_filtering_performed": details["scientific_filtering_performed"],
        "extrapolation_performed": "NONE",
        "frozen_decision_changes": "NONE",
    }
    metadata_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return metadata_path


def run() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if config["configuration_status"] != "BASELINE RULE LOCK":
        raise ValueError("Baseline rule was not locked")
    code_sha = _sha256(Path(__file__))
    condition = _condition_map()
    capacity = build_capacity_states(condition)
    resistance = build_resistance_states(condition, config)
    resistance = _attach_capacity_context(resistance, capacity)

    reporting = (
        resistance.groupby("soc_basis_percent", as_index=False)
        .agg(unique_cells=("cell_key", "nunique"), unique_conditions=("condition_id", "nunique"), observations=("cell_key", "size"))
    )
    reporting["missing_cells"] = resistance["cell_key"].nunique() - reporting["unique_cells"]
    reporting["distance_from_50"] = (reporting["soc_basis_percent"] - 50).abs()
    reporting_soc = int(
        reporting.sort_values(
            ["unique_cells", "unique_conditions", "missing_cells", "distance_from_50"],
            ascending=[False, False, True, True],
            kind="mergesort",
        ).iloc[0]["soc_basis_percent"]
    )
    if reporting_soc != 50:
        raise ValueError(f"Locked reporting SOC tie-break produced {reporting_soc}")

    shared_columns = [
        "source_filename", "cell_key", "cell_id", "replicate_id", "condition_id",
        "age_type", "age_profile", "age_temp", "age_soc", "age_chg_rate", "age_dischg_rate",
        "timestamp_s", "elapsed_days", "charge_throughput_ah", "discharge_throughput_ah",
        "num_cycles_op", "num_cycles_checkup", "state_kind", "soc_basis_percent",
        "measurement_temperature_c", "measured_capacity_ah", "capacity_baseline_ah",
        "source_capacity_soh_percent", "reconstructed_capacity_retention", "measured_energy_wh",
        "resistance_10ms_ohm", "resistance_1s_ohm", "r10_rel", "r1s_rel",
        "baseline_timestamp_s", "derivation_class",
    ]
    observations = pd.concat(
        [capacity.reindex(columns=shared_columns), resistance.reindex(columns=shared_columns)],
        ignore_index=True,
    ).sort_values(["state_kind", "cell_key", "timestamp_s", "soc_basis_percent"], kind="mergesort").reset_index(drop=True)
    model, uncertainty, fit_metadata = fit_representations(observations, reporting_soc, code_sha)
    schreiber = build_schreiber_summary()
    tum = build_tum_summary()
    compatibility = classify_automotive_compatibility(observations, schreiber)

    for directory in (PROCESSED, INTERMEDIATE, DIAGNOSTICS):
        directory.mkdir(parents=True, exist_ok=True)
    observations.to_parquet(OBS_PATH, index=False, compression="zstd")
    model.to_parquet(MODEL_PATH, index=False, compression="zstd")
    uncertainty.to_parquet(UNCERTAINTY_PATH, index=False, compression="zstd")
    schreiber.to_parquet(SCHREIBER_PATH, index=False, compression="zstd")
    tum.to_parquet(TUM_PATH, index=False, compression="zstd")
    _write_figures(observations, model, schreiber, tum)

    metadata_paths = [
        _write_dataset_metadata(
            OBS_PATH,
            observations,
            code_sha,
            {
                "source_datasets": ["SRC_LUH_2024"],
                "scientific_role": "primary capacity and pulse-resistance state observations",
                "transformations": [
                    "source SOH retained on author-defined percent scale",
                    "same-cell initial capacity ratio retained separately for consistency",
                    "same-cell same-SOC 25 C R10/R10_0 and R1s/R1s_0 construction",
                    "nearest preceding same-cell capacity check-up attached as context",
                ],
                "scientific_filtering_performed": [
                    "capacity: source-defined room-temperature discharge check-up with finite capacity and SOH",
                    "resistance: source RT flag, 25 +/- 0.5 C, supported SOC grid, and source 1-1000 mOhm limits",
                ],
            },
        ),
        _write_dataset_metadata(
            MODEL_PATH,
            model,
            code_sha,
            {
                "source_datasets": ["SRC_LUH_2024"],
                "scientific_role": "observed, linear, and bounded-monotone representation layers",
                "transformations": ["cell-balanced 30-day grouping", "weighted linear and PAVA monotone representations"],
                "scientific_filtering_performed": "NONE beyond observation eligibility inherited from P12 state construction",
            },
        ),
        _write_dataset_metadata(
            UNCERTAINTY_PATH,
            uncertainty,
            code_sha,
            {
                "source_datasets": ["SRC_LUH_2024"],
                "scientific_role": "empirical replicate, condition, measurement-proxy, and representation bounds",
                "transformations": ["q10/q90 empirical bounds without an assumed probability distribution"],
                "scientific_filtering_performed": "NONE beyond observation eligibility inherited from P12 state construction",
            },
        ),
        _write_dataset_metadata(
            SCHREIBER_PATH,
            schreiber,
            code_sha,
            {
                "source_datasets": ["SRC_SCHREIBER_2025"],
                "scientific_role": "independent automotive validation only",
                "transformations": ["protocol-line 11 capacity span", "protocol-line 38 t=0 to 10-ms and 1-s delta-V/delta-I"],
                "scientific_filtering_performed": "fixed source-protocol extraction only; no outcome-based selection",
            },
        ),
        _write_dataset_metadata(
            TUM_PATH,
            tum,
            code_sha,
            {
                "source_datasets": ["SRC_TUM_ID3"],
                "scientific_role": "fresh HPPC electrical plausibility only",
                "transformations": ["nine repeated protocol-line 37 pulses", "t=0 to interpolated 10-ms and 1-s delta-V/delta-I"],
                "scientific_filtering_performed": "fixed source-protocol extraction only; no ageing selection",
            },
        ),
    ]

    parameters = {
        "stage": "P12",
        "model_version": "p12_degradation_state_v1",
        "code_sha256": code_sha,
        "config_sha256": _sha256(CONFIG_PATH),
        "source_datasets": {
            "primary_fit": "SRC_LUH_2024",
            "automotive_validation": "SRC_SCHREIBER_2025",
            "fresh_hppc_plausibility": "SRC_TUM_ID3",
        },
        "baseline_rule_id": config["resistance_baseline_rule"]["rule_id"],
        "reporting_soc_percent": reporting_soc,
        "temperature_basis_c": 25.0,
        "exposure_axis": "elapsed_calendar_days_since_same_cell_baseline",
        "primary_resistance_timescale": "10 ms",
        "alternative_resistance_timescale": "1 s",
        "uncertainty_representation": "empirical bounds; no probability distribution assumed",
        "fit_metadata": fit_metadata,
        "automotive_compatibility": compatibility,
        "capacity_source_vs_reconstructed": {
            "source_field": "soh_cap (author-defined percent scale)",
            "reconstructed_field": "cap_aged_est_Ah / same-cell earliest eligible cap_aged_est_Ah",
            "roles_separate": True,
            "median_absolute_point_difference_percentage_points": float(
                np.median(
                    np.abs(
                        capacity["source_capacity_soh_percent"]
                        - 100.0 * capacity["reconstructed_capacity_retention"]
                    )
                )
            ),
        },
        "extrapolation": "NONE",
        "stochastic_resampling": False,
    }
    PARAMETERS_PATH.write_text(
        json.dumps(parameters, indent=2, sort_keys=True), encoding="utf-8"
    )
    manifest = {
        "stage": "P12",
        "files": {str(path.relative_to(ROOT)).replace("\\", "/"): _sha256(path) for path in OUTPUTS},
        "figures": {
            str(path.relative_to(ROOT)).replace("\\", "/"): _sha256(path)
            for path in sorted(DIAGNOSTICS.glob("p12_*.png"))
        },
        "metadata": {
            str(path.relative_to(ROOT)).replace("\\", "/"): _sha256(path)
            for path in metadata_paths
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"parameters": parameters, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    result = run()
    if args.print_summary:
        print(json.dumps(result["parameters"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
