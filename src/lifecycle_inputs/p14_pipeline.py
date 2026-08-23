from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "src" / "lifecycle_inputs" / "p14_config.yaml"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_parquet(frame: pd.DataFrame, path: Path, sort_by: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.sort_values(sort_by, kind="mergesort").reset_index(drop=True).to_parquet(
        path, index=False, engine="pyarrow", compression="zstd"
    )


def weighted_quantile(values: pd.Series, weights: pd.Series, quantile: float) -> float:
    x = values.to_numpy(float)
    w = weights.to_numpy(float)
    valid = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[valid], w[valid]
    order = np.argsort(x, kind="mergesort")
    x, w = x[order], w[order]
    plotting_position = (np.cumsum(w) - 0.5 * w) / w.sum()
    return float(np.interp(quantile, plotting_position, x))


def mobility_layers(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    vehicle = pd.read_parquet(ROOT / "data/processed/nhts_vehicle_use_observations.parquet")
    trip = pd.read_parquet(ROOT / "data/processed/nhts_trip_observations.parquet")
    long = pd.read_parquet(ROOT / "data/processed/nhts_long_distance_observations.parquet")
    valid_vehicle = vehicle[vehicle.annual_miles >= 0]
    annual_rows = []
    for label, q in zip(["lower_use", "central_use", "higher_use"], config["annual_mileage_quantiles"]):
        annual_rows.append({
            "scenario_id": label,
            "source_id": "SRC_NHTS_2022",
            "dataset_version": "2.1",
            "quantile": q,
            "annual_km": weighted_quantile(valid_vehicle.annual_km, valid_vehicle.survey_weight, q),
            "weight_field": "WTHHFIN",
            "valid_observation_count": len(valid_vehicle),
            "excluded_code_minus9_count": int((vehicle.annual_miles == -9).sum()),
            "lifecycle_ghg_calculated": False,
        })
    rule = config["mobility_rule"]
    sources = {"trip": (trip[trip.trip_miles >= 0], "trip_distance_km", "WTTRDFIN"),
               "long_distance": (long[long.long_distance_miles >= 0], "long_distance_km", "WTPERFIN")}
    requirement_rows = []
    for label in ["lower", "central", "upper"]:
        spec = rule[label]
        frame, value_col, weight_name = sources[spec["dataset"]]
        requirement_rows.append({
            "scenario_id": f"mobility_{label}", "source_id": "SRC_NHTS_2022",
            "selected_rule": rule["selected"], "evidence_dataset": spec["dataset"],
            "quantile": spec["quantile"],
            "required_single_service_distance_km": weighted_quantile(frame[value_col], frame.survey_weight, spec["quantile"]),
            "weight_field": weight_name, "valid_observation_count": len(frame),
            "universal_soh_cutoff": False, "lifecycle_ghg_calculated": False,
        })
    return pd.DataFrame(annual_rows), pd.DataFrame(requirement_rows)


def survival_layer(config: dict) -> pd.DataFrame:
    spec = config["survival"]
    median_2025 = spec["published_median_years_2020"] * (1 + spec["published_median_growth_fraction_per_year"]) ** 5
    rows = []
    for scenario, scale in spec["logistic_scale_years"].items():
        ages = np.arange(0, 51, dtype=float)
        raw = 1 / (1 + np.exp((ages - median_2025) / scale))
        unconditional = raw / raw[0]
        unconditional[1:] *= spec["first_year_survival"]
        unconditional[0] = 1.0
        unconditional = np.minimum.accumulate(np.clip(unconditional, 0, 1))
        for current_age in range(0, 26):
            denom = unconditional[current_age]
            for attained_age in range(current_age, 26):
                rows.append({
                    "source_id": spec["source_id"], "doi": spec["doi"],
                    "vehicle_class": spec["class"], "survival_scenario": scenario,
                    "current_vehicle_age_years": current_age,
                    "attained_vehicle_age_years": attained_age,
                    "years_after_conditioning": attained_age - current_age,
                    "unconditional_survival": float(unconditional[attained_age]),
                    "conditional_survival": float(unconditional[attained_age] / denom),
                    "published_median_anchor_years_2020": spec["published_median_years_2020"],
                    "projected_median_anchor_years_2025": median_2025,
                    "logistic_scale_years_assumption": float(scale),
                    "parameter_status": "PUBLISHED_EQUATION_AND_MEDIAN; SCALE_BOUNDED_ASSUMPTION",
                    "mileage_dependence_assumed": False,
                })
    return pd.DataFrame(rows)


def _cambium_raw() -> pd.DataFrame:
    archive = next((ROOT / "data/raw/SRC_CAMBIUM_2024").glob("*.zip"))
    with zipfile.ZipFile(archive) as zf:
        name = next(x for x in zf.namelist() if x.endswith(".csv"))
        raw = zf.read(name)
    return pd.read_csv(io.BytesIO(raw), skiprows=5)


def grid_layer(config: dict) -> pd.DataFrame:
    canonical = pd.read_parquet(ROOT / "data/processed/cambium_2024_average_grid_ci.parquet")
    raw = _cambium_raw()[["scenario", "gea", "t", "enduse_load", "aer_load_co2e"]]
    raw = raw.rename(columns={"gea": "region", "t": "calendar_year", "aer_load_co2e": "grid_ci_gco2e_per_kwh"})
    raw = raw[raw.scenario.isin(config["grid"]["scenarios"]) & raw.calendar_year.isin([2025,2030,2035,2040,2045,2050])]
    check = canonical.merge(raw, on=["scenario", "region", "calendar_year"], suffixes=("_canonical", "_raw"))
    if not np.allclose(check.grid_ci_gco2e_per_kwh_canonical, check.grid_ci_gco2e_per_kwh_raw):
        raise ValueError("Cambium raw/canonical metric mismatch")
    rows = []
    years = np.arange(2025, 2051)
    for scenario in config["grid"]["scenarios"]:
        regional_years = []
        for region, group in raw[raw.scenario == scenario].groupby("region", sort=True):
            group = group.sort_values("calendar_year")
            ci = np.interp(years, group.calendar_year, group.grid_ci_gco2e_per_kwh)
            load = np.interp(years, group.calendar_year, group.enduse_load)
            for year, value, demand in zip(years, ci, load):
                regional_years.append((region, int(year), float(value), float(demand)))
                rows.append({"source_id":"SRC_CAMBIUM_2024", "dataset_version":2024, "pathway_role":"PRIMARY_AVERAGE_CI",
                             "scenario":scenario, "geography_level":"GEA_REGION", "region":region, "calendar_year":int(year),
                             "metric_identity":"aer_load_co2e", "grid_ci_gco2e_per_kwh":float(value),
                             "aggregation_weight":np.nan, "interpolation_method":"piecewise_linear_in_domain"})
        regional = pd.DataFrame(regional_years, columns=["region","calendar_year","ci","load"])
        for year, group in regional.groupby("calendar_year", sort=True):
            weights = group.load / group.load.sum()
            rows.append({"source_id":"SRC_CAMBIUM_2024", "dataset_version":2024, "pathway_role":"PRIMARY_AVERAGE_CI",
                         "scenario":scenario, "geography_level":"US_LOAD_WEIGHTED", "region":"US_LOAD_WEIGHTED",
                         "calendar_year":int(year), "metric_identity":"aer_load_co2e",
                         "grid_ci_gco2e_per_kwh":float(np.sum(group.ci * weights)),
                         "aggregation_weight":1.0, "interpolation_method":"piecewise_linear_in_domain"})
    return pd.DataFrame(rows)


def manufacturing_layer(config: dict) -> pd.DataFrame:
    source = pd.read_parquet(ROOT / "data/processed/llamas_pack_manufacturing_ghg.parquet")
    rows = []
    for chemistry in sorted(source.chemistry.unique()):
        base = source[(source.chemistry == chemistry) & (source.pathway == "Current")].iloc[0]
        for pathway in ["SPS", "SDS"]:
            future = source[(source.chemistry == chemistry) & (source.pathway == pathway)].sort_values("calendar_year")
            years_src = np.r_[int(base.calendar_year), future.calendar_year.to_numpy(int)]
            values_src = np.r_[float(base.pack_ghg_kgco2e_per_kwh), future.pack_ghg_kgco2e_per_kwh.to_numpy(float)]
            for year in range(2025, 2051):
                rows.append({"source_id":"SRC_LLAMAS_OROZCO_2023", "chemistry":chemistry, "pathway":pathway,
                             "benchmark_type":"PROSPECTIVE", "calendar_year":year,
                             "pack_ghg_kgco2e_per_kwh":float(np.interp(year, years_src, values_src)),
                             "system_boundary":base.system_boundary, "manufacturing_geography":None,
                             "interpolation_method":"piecewise_linear_in_domain", "lifecycle_ghg_calculated":False})
        for year in range(2025, 2051):
            rows.append({"source_id":"SRC_LLAMAS_OROZCO_2023", "chemistry":chemistry, "pathway":"Current",
                         "benchmark_type":"STATIC_SAME_SOURCE_2020", "calendar_year":year,
                         "pack_ghg_kgco2e_per_kwh":float(base.pack_ghg_kgco2e_per_kwh),
                         "system_boundary":base.system_boundary, "manufacturing_geography":None,
                         "interpolation_method":"held_constant_benchmark", "lifecycle_ghg_calculated":False})
    return pd.DataFrame(rows)


def charging_layer(config: dict) -> pd.DataFrame:
    source = pd.read_parquet(ROOT / "data/processed/sevdari_charging_efficiency_observations.parquet")
    valid = source[source.charging_efficiency_fraction.gt(0) & source.charging_efficiency_fraction.le(1)]
    rows = []
    for label, q in zip(["lower_efficiency", "central_efficiency", "higher_efficiency"], config["charging"]["quantiles"]):
        eta = float(valid.charging_efficiency_fraction.quantile(q, interpolation="linear"))
        rows.append({"source_id":"SRC_SEVDARI_2023", "scenario_id":label, "quantile":q,
                     "charging_efficiency_fraction":eta, "l2_to_l3_multiplier":1/eta,
                     "valid_observation_count":len(valid), "excluded_zero_count":int((source.charging_efficiency_fraction == 0).sum()),
                     "conversion_boundary":"L2_HV_BATTERY_SIDE_TO_L3_GRID_SIDE", "atb_epa_conversion_applied":False})
    return pd.DataFrame(rows)


def calendar_layer(config: dict, survival: pd.DataFrame) -> pd.DataFrame:
    central = survival[(survival.survival_scenario == "central") & (survival.current_vehicle_age_years == 0)]
    survival_by_age = central.set_index("attained_vehicle_age_years").conditional_survival
    rows = []
    for operation_year in range(config["entry_year"], config["horizon_year"] + 1):
        age = operation_year - config["entry_year"]
        rows.append({"cohort_id":"ENTRY_2025", "vehicle_entry_year":2025, "vehicle_current_age_at_entry":0,
                     "operation_year":operation_year, "vehicle_age_years":age, "battery_age_years":age,
                     "candidate_replacement_year":pd.NA, "grid_ci_year":operation_year,
                     "replacement_battery_manufacturing_ci_year":pd.NA, "vehicle_retirement_year":pd.NA,
                     "conditional_vehicle_survival":float(survival_by_age.loc[age]),
                     "horizon_truncated":operation_year == 2050, "replacement_optimized":False,
                     "lifecycle_ghg_calculated":False})
    return pd.DataFrame(rows)


def generate() -> dict:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    mobility, requirements = mobility_layers(config)
    survival = survival_layer(config)
    grid = grid_layer(config)
    manufacturing = manufacturing_layer(config)
    charging = charging_layer(config)
    calendar = calendar_layer(config, survival)
    outputs = {
        "mobility_use": (mobility, ["scenario_id"]),
        "mobility_service": (requirements, ["scenario_id"]),
        "vehicle_survival": (survival, ["survival_scenario","current_vehicle_age_years","attained_vehicle_age_years"]),
        "grid_pathways": (grid, ["scenario","geography_level","region","calendar_year"]),
        "battery_manufacturing": (manufacturing, ["chemistry","benchmark_type","pathway","calendar_year"]),
        "charging_conversion": (charging, ["scenario_id"]),
        "calendar_architecture": (calendar, ["operation_year"]),
    }
    paths = {}
    names = {"mobility_use":"p14_mobility_use_scenarios.parquet", "mobility_service":"p14_mobility_service_requirements.parquet",
             "vehicle_survival":"p14_vehicle_survival.parquet", "grid_pathways":"p14_grid_pathways.parquet",
             "battery_manufacturing":"p14_battery_manufacturing_pathways.parquet", "charging_conversion":"p14_charging_conversion.parquet",
             "calendar_architecture":"p14_calendar_architecture.parquet"}
    for key, (frame, sort_by) in outputs.items():
        path = ROOT / "data/processed" / names[key]
        write_parquet(frame, path, sort_by)
        paths[key] = path
    metadata_paths = []
    metadata_dir = ROOT / "data/processed/metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    for key, (frame, _) in outputs.items():
        metadata_path = metadata_dir / names[key].replace(".parquet", ".yaml")
        metadata_path.write_text(yaml.safe_dump({
            "stage": "P14", "file": names[key], "row_count": len(frame),
            "processing_script": "src/lifecycle_inputs/p14_pipeline.py",
            "scientific_filtering_performed": "P14_SOURCE_SEMANTIC_AND_PHYSICAL_DOMAIN_RULES_DISCLOSED",
            "lifecycle_ghg_calculated": "NONE", "replacement_optimization_performed": "NONE",
            "extrapolation_performed": "NONE",
        }, sort_keys=False), encoding="utf-8")
        metadata_paths.append(metadata_path)
    params = {
        "stage":"P14", "configuration_id":config["configuration_id"], "locked_before_lifecycle_results":True,
        "annual_mileage_special_codes":{"ANNMILES":{"-9":{"meaning":"Not ascertained","count":213}},
                                          "TRPMILES":{"-9":{"meaning":"Not ascertained","count":14}},
                                          "GCDTOT":{"-1":{"meaning":"Appropriate skip","count":3604},"-9":{"meaning":"Not ascertained","count":372}}},
        "annual_mileage_scenarios":mobility.to_dict(orient="records"),
        "mobility_service_scenarios":requirements.to_dict(orient="records"),
        "power_service":{"max_discharge_kw":37.745524750,"max_regen_acceptance_kw":35.614420003,"source":"P13 FASTSim UDDS/HWFET"},
        "survival":{"class":"passenger_cars","conditional_formula":"S(attained_age)/S(current_age)",
                    "projected_median_2025_years":float(survival.projected_median_anchor_years_2025.iloc[0]),
                    "status":"WITH BOUNDS: published equation/median; explicit scale envelope"},
        "grid":{"architecture":config["grid"]["geography_architecture"],"aggregation_formula":"sum_r(CI_r,y * enduse_load_r,y) / sum_r(enduse_load_r,y)",
                "interpolation":"piecewise_linear_in_domain","lrmer":"Cambium-2023 LRMER sensitivity only"},
        "manufacturing":{"interpolation":"piecewise_linear_in_domain","static":"same-source 2020 Current held constant","geography":"UNRESOLVED/IMPLICIT"},
        "charging":{"representation":"empirical p10/p50/p90","conversion":"L3 = L2 / efficiency"},
        "calendar":{"entry_year":2025,"horizon_year":2050,"rule":config["horizon"]["rule"],
                    "residual_survival_at_2050":float(calendar.conditional_vehicle_survival.iloc[-1])},
        "lifecycle_ghg_calculated":"NONE", "replacement_optimization_performed":"NONE", "extrapolation_performed":"NONE",
        "frozen_decision_changes":"NONE", "gate":"LIFECYCLE INPUT ARCHITECTURE VALIDATED WITH BOUNDS",
    }
    params_path = ROOT / "results/intermediate/p14_input_layer_parameters.json"
    params_path.parent.mkdir(parents=True, exist_ok=True)
    params_path.write_text(json.dumps(params, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    targets = [CONFIG_PATH, Path(__file__), ROOT/"tests/test_p14_lifecycle_inputs.py", ROOT/"docs/P14_LIFECYCLE_INPUT_ARCHITECTURE_REPORT.md", ROOT/"docs/RESEARCH_DECISION_LOG.md", *paths.values(), *metadata_paths, params_path]
    manifest = {"stage":"P14", "artifact_count":len(targets), "artifacts":[{"path":str(p.relative_to(ROOT)).replace("\\","/"),"sha256":sha256(p),"bytes":p.stat().st_size} for p in sorted(targets,key=lambda p:str(p))]}
    manifest_path = ROOT / "results/intermediate/p14_artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return {"rows":{k:len(v[0]) for k,v in outputs.items()},"parameters":params,"manifest":manifest}


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2, sort_keys=True))
