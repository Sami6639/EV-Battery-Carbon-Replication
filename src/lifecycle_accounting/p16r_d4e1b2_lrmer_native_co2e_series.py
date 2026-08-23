from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cambium_lrmer_2023_components.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cambium_2023_lrmer_co2e_combined.parquet"
)


print("=" * 78)
print("P16R-D4E1B2 — WORKBOOK-NATIVE CAMBIUM-2023 LRMER CO2E SERIES")
print("=" * 78)


# ============================================================
# 1. LOAD VERIFIED FINAL LEVELIZED COMPONENTS
# ============================================================

d = pd.read_parquet(INPUT_FILE)

assert not d.empty

if d["parse_issue_flag"].fillna(False).any():
    raise RuntimeError(
        "P16R-D4E1B2 FAIL — parse-issue rows present."
    )


# ============================================================
# 2. MAP THE SIX OFFICIAL COMPONENT METRICS
#
# CO2 : kg/MWh end-use
# CH4 : g/MWh end-use
# N2O : g/MWh end-use
#
# Direct combustion + precombustion.
# ============================================================

def component_key(metric):

    x = str(metric).strip().lower()

    if x.startswith("co2 from direct combustion"):
        return "co2_direct"

    if x.startswith("ch4 from direct combustion"):
        return "ch4_direct"

    if x.startswith("n2o from direct combustion"):
        return "n2o_direct"

    if x.startswith("co2 from precombustion"):
        return "co2_precombustion"

    if x.startswith("ch4 from precombustion"):
        return "ch4_precombustion"

    if x.startswith("n2o from precombustion"):
        return "n2o_precombustion"

    return None


d["component_key"] = (
    d["metric_identity"]
    .map(component_key)
)

if d["component_key"].isna().any():
    unknown = (
        d.loc[
            d["component_key"].isna(),
            "metric_identity",
        ]
        .drop_duplicates()
        .tolist()
    )

    raise RuntimeError(
        "P16R-D4E1B2 FAIL — unknown component metric(s): "
        + str(unknown)
    )


EXPECTED_COMPONENTS = {
    "co2_direct",
    "ch4_direct",
    "n2o_direct",
    "co2_precombustion",
    "ch4_precombustion",
    "n2o_precombustion",
}

assert set(d["component_key"].unique()) == EXPECTED_COMPONENTS


# ============================================================
# 3. EXACT PANEL CONTRACT
# ============================================================

KEY = [
    "scenario",
    "region",
    "calendar_year",
]

duplicate_rows = int(
    d.duplicated(
        subset=KEY + ["component_key"],
        keep=False,
    ).sum()
)

if duplicate_rows != 0:
    raise RuntimeError(
        "P16R-D4E1B2 FAIL — duplicate "
        "scenario-region-year-component rows."
    )


component_counts = (
    d.groupby(KEY)["component_key"]
    .nunique()
)

if not (component_counts == 6).all():
    raise RuntimeError(
        "P16R-D4E1B2 FAIL — incomplete six-component panel."
    )


# ============================================================
# 4. WIDE COMPONENT TABLE
# ============================================================

wide = (
    d.pivot(
        index=KEY,
        columns="component_key",
        values="metric_value",
    )
    .reset_index()
)

assert set(EXPECTED_COMPONENTS) <= set(wide.columns)


# ============================================================
# 5. WORKBOOK-NATIVE GWP CONVENTION
#
# Audited from the untouched official workbook:
#
# Levelized LRMER D13 = 100-year (AR6)
#
# Active Lookups row 24:
# CO2 = 1
# CH4 = 29.8
# N2O = 273
#
# Exact workbook formula:
#
# CO2e =
# CO2 * GWP_CO2
# + CH4 / 1000 * GWP_CH4
# + N2O / 1000 * GWP_N2O
#
# Project does NOT select an external GWP convention.
# ============================================================

GWP_CO2 = 1.0
GWP_CH4 = 29.8
GWP_N2O = 273.0


wide["co2e_direct_kg_per_mwh"] = (
    wide["co2_direct"] * GWP_CO2
    + wide["ch4_direct"] / 1000.0 * GWP_CH4
    + wide["n2o_direct"] / 1000.0 * GWP_N2O
)


wide["co2e_precombustion_kg_per_mwh"] = (
    wide["co2_precombustion"] * GWP_CO2
    + wide["ch4_precombustion"] / 1000.0 * GWP_CH4
    + wide["n2o_precombustion"] / 1000.0 * GWP_N2O
)


wide["lrmer_co2e_combined_kg_per_mwh_end_use"] = (
    wide["co2e_direct_kg_per_mwh"]
    + wide["co2e_precombustion_kg_per_mwh"]
)


# Numerically:
#
# 1 kg / MWh = 1 g / kWh
#
wide["lrmer_gco2e_per_kwh"] = (
    wide[
        "lrmer_co2e_combined_kg_per_mwh_end_use"
    ]
)


# ============================================================
# 6. SCIENTIFIC PROVENANCE
# ============================================================

wide["source_id"] = "SRC_CAMBIUM_LRMER_2023"

wide["dataset_version"] = 2023

wide["metric_identity"] = (
    "Cambium-2023 LRMER CO2e Combined"
)

wide["metric_role"] = (
    "MARGINAL_EMISSIONS_SENSITIVITY"
)

wide["delivery_boundary"] = "END_USE"

wide["levelization_horizon_years"] = 20

wide["gwp_convention"] = (
    "WORKBOOK_SAVED_100_YEAR_AR6"
)

wide["gwp_co2"] = GWP_CO2
wide["gwp_ch4"] = GWP_CH4
wide["gwp_n2o"] = GWP_N2O

wide["gwp_selected_by_project"] = False

wide["gwp_source"] = (
    "CAMBIUM_2023_WORKBOOK_ACTIVE_LOOKUPS_ROW_24"
)

wide["co2e_formula_source"] = (
    "CAMBIUM_2023_WORKBOOK_NATIVE_FORMULA"
)

wide["regional_average_created"] = False

wide["us_load_weighted_lrmer_invented"] = False

wide["delta_g_calculated"] = False

wide["carbon_classification_calculated"] = False


# ============================================================
# 7. HARD SOURCE-SUPPORT CONTRACT
# ============================================================

assert wide["scenario"].nunique() == 8

assert wide["region"].nunique() == 18

assert sorted(
    wide["calendar_year"]
    .unique()
    .tolist()
) == [
    2025,
    2030,
    2035,
    2040,
    2045,
    2050,
]

assert len(wide) == (
    8 * 18 * 6
)

assert (
    wide["lrmer_gco2e_per_kwh"]
    .notna()
    .all()
)

assert not (
    wide["region"]
    == "US_LOAD_WEIGHTED"
).any()

assert not wide[
    "gwp_selected_by_project"
].any()

assert not wide[
    "regional_average_created"
].any()

assert not wide[
    "us_load_weighted_lrmer_invented"
].any()

assert not wide[
    "delta_g_calculated"
].any()

assert not wide[
    "carbon_classification_calculated"
].any()


# ============================================================
# 8. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

wide.to_parquet(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# 9. SUMMARY
# ============================================================

print("\nPanel identity:")

print(
    "scenarios:",
    wide["scenario"].nunique(),
)

print(
    "regions:",
    wide["region"].nunique(),
)

print(
    "years:",
    sorted(
        wide["calendar_year"]
        .unique()
        .tolist()
    ),
)

print(
    "rows:",
    len(wide),
)


print("\nWorkbook-native GWP convention:")

print(
    "100-year AR6"
)

print(
    "CO2:",
    GWP_CO2,
)

print(
    "CH4:",
    GWP_CH4,
)

print(
    "N2O:",
    GWP_N2O,
)


print("\nCombined LRMER CO2e range:")

print(
    float(
        wide[
            "lrmer_gco2e_per_kwh"
        ].min()
    ),
    "to",
    float(
        wide[
            "lrmer_gco2e_per_kwh"
        ].max()
    ),
    "g CO2e/kWh",
)


print("\nScenario names:")

for x in sorted(
    wide["scenario"]
    .unique()
    .tolist()
):
    print(" -", x)


print("\nOutput:")

print(
    OUTPUT_FILE.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4E1B2 PASS — WORKBOOK-NATIVE "
    "CAMBIUM-2023 LRMER CO2E SERIES GENERATED"
)

print(
    "OFFICIAL SIX LEVELIZED COMPONENTS: USED"
)

print(
    "WORKBOOK-SAVED GWP: 100-YEAR AR6"
)

print(
    "PROJECT-SELECTED GWP: NONE"
)

print(
    "CO2E FORMULA: WORKBOOK-NATIVE"
)

print(
    "SCENARIOS: 8/8"
)

print(
    "GEA REGIONS: 18/18"
)

print(
    "US_LOAD_WEIGHTED LRMER: NOT INVENTED"
)

print(
    "LRMER DELTAG CALCULATED: NO"
)

print(
    "NEW CARBON CLASSIFICATION PRODUCED: NO"
)

print("=" * 78)