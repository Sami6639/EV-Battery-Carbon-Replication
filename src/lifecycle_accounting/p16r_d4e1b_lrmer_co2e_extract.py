from pathlib import Path
import hashlib

import pandas as pd
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[2]

WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "SRC_CAMBIUM_LRMER_2023"
    / "1707947178-Cambium23_LRMER_GEAregions_0.xlsx"
)

OUTPUT = (
    ROOT
    / "data"
    / "processed"
    / "cambium_2023_lrmer_co2e_combined.parquet"
)


print("=" * 78)
print("P16R-D4E1B — OFFICIAL CAMBIUM-2023 LRMER CO2E EXTRACTION")
print("=" * 78)


# ============================================================
# 1. SOURCE IDENTITY
# ============================================================

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)
    return h.hexdigest()


source_sha256 = sha256(WORKBOOK)

print("\nSource SHA-256:")
print(source_sha256)


# ============================================================
# 2. OPEN OFFICIAL WORKBOOK
# ============================================================

wb = load_workbook(
    WORKBOOK,
    read_only=True,
    data_only=True,
)

ws = wb["Data - Annual"]


# ============================================================
# 3. IDENTIFY FINAL PUBLISHED OUTPUT COLUMNS
#
# Header structure established in D4E1A4:
#
# row 3 = metric identity
# row 4 = scenario
# row 5 = calendar year
#
# We select ONLY final annual output columns whose metric
# explicitly identifies CO2-equivalent COMBINED emissions.
#
# We do NOT use intermediate calculation columns C:N.
# ============================================================

selected_columns = []

for col in range(16, ws.max_column + 1):

    metric = ws.cell(
        row=3,
        column=col,
    ).value

    scenario = ws.cell(
        row=4,
        column=col,
    ).value

    year = ws.cell(
        row=5,
        column=col,
    ).value

    if metric is None:
        continue

    metric_text = str(metric).strip()
    metric_lower = metric_text.lower()

    is_co2e = (
        "co2e" in metric_lower
        or "co2-equivalent" in metric_lower
        or "co2 equivalent" in metric_lower
    )

    is_combined = (
        "combined" in metric_lower
    )

    if not (
        is_co2e
        and is_combined
    ):
        continue

    if scenario is None or year is None:
        continue

    try:
        year_int = int(year)
    except Exception:
        continue

    selected_columns.append(
        {
            "column_index": col,
            "column_letter":
                ws.cell(
                    row=3,
                    column=col,
                ).column_letter,

            "metric_identity":
                metric_text,

            "scenario":
                str(scenario).strip(),

            "calendar_year":
                year_int,
        }
    )


if not selected_columns:
    raise RuntimeError(
        "P16R-D4E1B FAIL — no official final "
        "CO2e-Combined annual columns found."
    )


print("\nSelected final CO2e-Combined columns:")
print("count =", len(selected_columns))

for item in selected_columns[:20]:
    print(
        item["column_letter"],
        "|",
        item["metric_identity"],
        "|",
        item["scenario"],
        "|",
        item["calendar_year"],
    )


# ============================================================
# 4. EXTRACT 18 GEA REGIONS
#
# Annual data rows begin at row 6.
# Column B contains GEA region.
# ============================================================

rows = []

for item in selected_columns:

    col = item["column_index"]

    for row_idx in range(6, ws.max_row + 1):

        region = ws.cell(
            row=row_idx,
            column=2,
        ).value

        value = ws.cell(
            row=row_idx,
            column=col,
        ).value

        if region is None:
            continue

        region = str(region).strip()

        if region == "":
            continue

        if value is None:
            continue

        try:
            metric_value = float(value)
        except Exception:
            continue

        rows.append(
            {
                "source_id":
                    "SRC_CAMBIUM_LRMER_2023",

                "dataset_version":
                    2023,

                "scenario":
                    item["scenario"],

                "region":
                    region,

                "calendar_year":
                    item["calendar_year"],

                "metric_identity":
                    item["metric_identity"],

                "metric_role":
                    "LRMER_CO2E_COMBINED",

                "metric_value_kgco2e_per_mwh_end_use":
                    metric_value,

                # Numerically:
                # 1 kg/MWh = 1 g/kWh
                "lrmer_gco2e_per_kwh":
                    metric_value,

                "source_sheet":
                    "Data - Annual",

                "source_column":
                    item["column_letter"],

                "source_row":
                    row_idx,

                "gwp_selected_by_project":
                    False,

                "regional_average_created":
                    False,

                "us_load_weighted_invented":
                    False,
            }
        )


out = pd.DataFrame(rows)

if out.empty:
    raise RuntimeError(
        "P16R-D4E1B FAIL — extraction returned no rows."
    )


# ============================================================
# 5. HARD PANEL CONTRACT
# ============================================================

key = [
    "scenario",
    "region",
    "calendar_year",
]

dup = int(
    out.duplicated(
        subset=key,
        keep=False,
    ).sum()
)

if dup != 0:
    raise RuntimeError(
        "P16R-D4E1B FAIL — duplicate "
        "scenario-region-year rows."
    )


print("\nPanel identity:")

print(
    "scenarios:",
    out["scenario"].nunique(),
)

print(
    "regions:",
    out["region"].nunique(),
)

print(
    "years:",
    sorted(
        out["calendar_year"]
        .unique()
        .tolist()
    ),
)

print(
    "rows:",
    len(out),
)

print(
    "duplicate rows:",
    dup,
)


# ============================================================
# 6. EXPECTED SOURCE SUPPORT
#
# Cambium 2023 annual LRMER workbook:
# 8 scenarios × 18 GEA regions × 6 years
# = 864 CO2e-Combined annual observations.
# ============================================================

assert out["scenario"].nunique() == 8
assert out["region"].nunique() == 18

assert sorted(
    out["calendar_year"]
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

assert len(out) == (
    8 * 18 * 6
)


# ============================================================
# 7. VALUE DOMAIN
# ============================================================

assert (
    out["lrmer_gco2e_per_kwh"]
    .notna()
    .all()
)

print("\nLRMER CO2e range:")

print(
    float(
        out[
            "lrmer_gco2e_per_kwh"
        ].min()
    ),
    "to",
    float(
        out[
            "lrmer_gco2e_per_kwh"
        ].max()
    ),
    "g CO2e/kWh",
)


# ============================================================
# 8. NO NATIONAL AGGREGATION
# ============================================================

assert not (
    out["region"]
    == "US_LOAD_WEIGHTED"
).any()

assert not out[
    "gwp_selected_by_project"
].any()

assert not out[
    "regional_average_created"
].any()

assert not out[
    "us_load_weighted_invented"
].any()


# ============================================================
# 9. SAVE
# ============================================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

out.to_parquet(
    OUTPUT,
    index=False,
)


# ============================================================
# 10. SUMMARY
# ============================================================

print("\nScenario names:")

for x in sorted(
    out["scenario"]
    .unique()
    .tolist()
):
    print(" -", x)


print("\nGEA regions:")

for x in sorted(
    out["region"]
    .unique()
    .tolist()
):
    print(" -", x)


print("\nOutput:")
print(
    OUTPUT.relative_to(ROOT)
)


print("\n" + "=" * 78)

print(
    "P16R-D4E1B PASS — OFFICIAL CAMBIUM-2023 "
    "LRMER CO2E-COMBINED SERIES EXTRACTED"
)

print(
    "OFFICIAL CO2E-COMBINED METRIC: USED"
)

print(
    "GWP CONVERSION BY PROJECT: NONE"
)

print(
    "GEA REGIONS: 18/18"
)

print(
    "SOURCE SCENARIOS: 8/8"
)

print(
    "SOURCE YEARS: 2025–2050 / 5-YEAR STEPS"
)

print(
    "US_LOAD_WEIGHTED LRMER: NOT INVENTED"
)

print(
    "LRMER DELTAG CALCULATED: NO"
)

print("=" * 78)