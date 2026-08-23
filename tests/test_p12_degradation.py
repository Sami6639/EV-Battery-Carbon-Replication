"""Scientific-layer invariants for P12 degradation-state construction."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.degradation import p12_pipeline as p12


ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _observations() -> pd.DataFrame:
    return pd.read_parquet(p12.OBS_PATH)


def test_baseline_is_deterministic_same_cell_soc_and_temperature_matched() -> None:
    data = _observations()
    pulse = data.loc[data["state_kind"].eq("pulse_resistance")]
    baseline = pulse.loc[
        pulse["timestamp_s"].eq(pulse["baseline_timestamp_s"])
    ]
    assert len(baseline) == 228 * 5
    assert not baseline.duplicated(["cell_key", "soc_basis_percent"]).any()
    assert np.allclose(baseline["r10_rel"], 1.0)
    assert np.allclose(baseline["r1s_rel"], 1.0)
    assert pulse["measurement_temperature_c"].between(24.5, 25.5).all()
    first = pulse.groupby(["cell_key", "soc_basis_percent"])["timestamp_s"].min()
    recorded = baseline.set_index(["cell_key", "soc_basis_percent"])["timestamp_s"]
    pd.testing.assert_series_equal(first.sort_index(), recorded.sort_index(), check_names=False)


def test_resistance_ratios_are_correct_and_timescales_are_not_mixed() -> None:
    data = _observations()
    pulse = data.loc[data["state_kind"].eq("pulse_resistance")].copy()
    base10 = pulse.loc[np.isclose(pulse["r10_rel"], 1.0)].groupby(
        ["cell_key", "soc_basis_percent"]
    )["resistance_10ms_ohm"].first()
    base1s = pulse.loc[np.isclose(pulse["r1s_rel"], 1.0)].groupby(
        ["cell_key", "soc_basis_percent"]
    )["resistance_1s_ohm"].first()
    keys = pd.MultiIndex.from_frame(pulse[["cell_key", "soc_basis_percent"]])
    assert np.allclose(pulse["r10_rel"], pulse["resistance_10ms_ohm"] / base10.reindex(keys).to_numpy())
    assert np.allclose(pulse["r1s_rel"], pulse["resistance_1s_ohm"] / base1s.reindex(keys).to_numpy())
    assert not np.allclose(pulse["r10_rel"], pulse["r1s_rel"])


def test_source_roles_and_primary_fit_are_protected() -> None:
    parameters = json.loads(p12.PARAMETERS_PATH.read_text(encoding="utf-8"))
    assert parameters["source_datasets"] == {
        "primary_fit": "SRC_LUH_2024",
        "automotive_validation": "SRC_SCHREIBER_2025",
        "fresh_hppc_plausibility": "SRC_TUM_ID3",
    }
    model = pd.read_parquet(p12.MODEL_PATH)
    assert set(model["source_dataset"]) == {"SRC_LUH_2024"}
    tree = ast.parse(Path(p12.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert not any(name.startswith(("src.vehicle", "src.carbon", "src.lifecycle")) for name in imported)


def test_primary_domain_has_no_extrapolation() -> None:
    model = pd.read_parquet(p12.MODEL_PATH)
    primary = model.loc[model["selected_primary"]]
    assert primary["extrapolation_count"].eq(0).all()
    assert primary["exposure_days"].between(
        primary["valid_min_days"], primary["valid_max_days"]
    ).all()
    for _, group in primary.groupby("metric_id"):
        assert group["valid_min_days"].nunique() == 1
        assert group["valid_max_days"].nunique() == 1


def test_outputs_are_role_labeled_and_manifest_matches() -> None:
    schreiber = pd.read_parquet(p12.SCHREIBER_PATH)
    tum = pd.read_parquet(p12.TUM_PATH)
    assert set(schreiber["validation_role"]) == {"INDEPENDENT_AUTOMOTIVE_VALIDATION_ONLY"}
    assert set(tum["validation_role"]) == {"FRESH_HPPC_PLAUSIBILITY_ONLY"}
    assert len(schreiber) == 9
    assert len(tum) == 27
    manifest = json.loads(p12.MANIFEST_PATH.read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        assert _sha(ROOT / relative) == expected


def test_locked_configuration_and_distinct_capacity_fields() -> None:
    config = yaml.safe_load(p12.CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["configuration_status"] == "BASELINE RULE LOCK"
    assert config["primary_extrapolation"] == "NONE"
    capacity = _observations().query("state_kind == 'capacity'")
    assert capacity["source_capacity_soh_percent"].notna().all()
    assert capacity["reconstructed_capacity_retention"].notna().all()
    assert not np.allclose(
        capacity["source_capacity_soh_percent"],
        100.0 * capacity["reconstructed_capacity_retention"],
    )
