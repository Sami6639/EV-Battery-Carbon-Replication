from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[2]

WORKBOOK = (
    ROOT
    / "data"
    / "raw"
    / "SRC_CAMBIUM_LRMER_2023"
    / "1707947178-Cambium23_LRMER_GEAregions_0.xlsx"
)


print("=" * 78)
print("P16R-D4E1B1 — CAMBIUM-2023 CO2E FORMULA / GWP CONTRACT AUDIT")
print("=" * 78)


# ============================================================
# 1. LOAD FORMULA AND CACHED-VALUE VERSIONS
# ============================================================

wb_formula = load_workbook(
    WORKBOOK,
    read_only=False,
    data_only=False,
)

wb_value = load_workbook(
    WORKBOOK,
    read_only=False,
    data_only=True,
)


# ============================================================
# 2. LEVELIZED LRMER CONTROL SHEET
# ============================================================

ws_f = wb_formula["Levelized LRMER"]
ws_v = wb_value["Levelized LRMER"]

print("\nLEVELIZED LRMER CONTROL CELLS | A1:J20")

for r in range(1, 21):

    items = []

    for c in range(1, 11):

        formula_value = ws_f.cell(
            row=r,
            column=c,
        ).value

        cached_value = ws_v.cell(
            row=r,
            column=c,
        ).value

        if (
            formula_value is not None
            or cached_value is not None
        ):

            coord = ws_f.cell(
                row=r,
                column=c,
            ).coordinate

            items.append(
                f"{coord}: "
                f"formula={formula_value!r}; "
                f"cached={cached_value!r}"
            )

    if items:
        print(" | ".join(items))


# ============================================================
# 3. GWP SHEET
# ============================================================

gwp_f = wb_formula["GWP"]
gwp_v = wb_value["GWP"]

print("\nGWP SHEET | A1:F15")

for r in range(1, 16):

    items = []

    for c in range(1, 7):

        fv = gwp_f.cell(
            row=r,
            column=c,
        ).value

        cv = gwp_v.cell(
            row=r,
            column=c,
        ).value

        if fv is not None or cv is not None:

            coord = gwp_f.cell(
                row=r,
                column=c,
            ).coordinate

            items.append(
                f"{coord}: "
                f"formula={fv!r}; "
                f"cached={cv!r}"
            )

    if items:
        print(" | ".join(items))


# ============================================================
# 4. DATA - ANNUAL INTERMEDIATE CO2E FORMULAS
#
# Previously audited:
#
# F = Combustion CO2e
# J = Precombustion CO2e
# N = Combined CO2e
#
# Inspect representative region rows.
# ============================================================

annual_f = wb_formula["Data - Annual"]
annual_v = wb_value["Data - Annual"]

print("\nDATA - ANNUAL REPRESENTATIVE CO2E CELLS")

for row in [6, 7, 8, 9, 10]:

    region = annual_v.cell(
        row=row,
        column=2,
    ).value

    print(f"\nRegion row {row}: {region}")

    for col in [6, 10, 14]:

        cell_f = annual_f.cell(
            row=row,
            column=col,
        )

        cell_v = annual_v.cell(
            row=row,
            column=col,
        )

        print(
            f"{cell_f.coordinate}: "
            f"formula={cell_f.value!r}; "
            f"cached={cell_v.value!r}"
        )


# ============================================================
# 5. SEARCH CO2E FORMULAS FOR GWP REFERENCES
# ============================================================

print("\nCO2E FORMULAS REFERENCING GWP / LOOKUPS")

formula_hits = []

for row in range(6, annual_f.max_row + 1):

    for col in [6, 10, 14]:

        cell = annual_f.cell(
            row=row,
            column=col,
        )

        value = cell.value

        if not isinstance(value, str):
            continue

        if not value.startswith("="):
            continue

        lower = value.lower()

        if (
            "gwp" in lower
            or "lookup" in lower
            or "vlookup" in lower
            or "xlookup" in lower
            or "index" in lower
            or "match" in lower
        ):

            formula_hits.append(
                (
                    cell.coordinate,
                    value,
                )
            )


for coord, formula in formula_hits[:60]:
    print(
        f"{coord}: {formula}"
    )

print(
    "formula-hit count:",
    len(formula_hits),
)


# ============================================================
# 6. DATA VALIDATIONS ON CONTROL SHEET
# ============================================================

print("\nLEVELIZED LRMER DATA VALIDATIONS")

try:

    validations = list(
        ws_f.data_validations.dataValidation
    )

    print(
        "validation count:",
        len(validations),
    )

    for dv in validations:

        print(
            "sqref=",
            dv.sqref,
            "| type=",
            dv.type,
            "| formula1=",
            dv.formula1,
            "| formula2=",
            dv.formula2,
        )

except Exception as exc:

    print(
        "Could not inspect validations:",
        repr(exc),
    )


# ============================================================
# 7. WORKBOOK DEFINED NAMES
# ============================================================

print("\nGWP / EMISSION RELATED DEFINED NAMES")

name_hits = []

try:

    for name, definition in wb_formula.defined_names.items():

        text = (
            str(name)
            + " "
            + str(definition)
        )

        lower = text.lower()

        if any(
            token in lower
            for token in [
                "gwp",
                "co2e",
                "emission",
                "levelized",
                "lrmer",
            ]
        ):

            name_hits.append(
                (
                    name,
                    definition,
                )
            )

except Exception as exc:

    print(
        "Defined-name inspection error:",
        repr(exc),
    )


for name, definition in name_hits:
    print(
        name,
        "=>",
        definition,
    )

print(
    "defined-name hit count:",
    len(name_hits),
)


# ============================================================
# 8. SCIENTIFIC DECISION STATUS
# ============================================================

print("\n" + "=" * 78)

print(
    "P16R-D4E1B1 PASS — CAMBIUM-2023 CO2E "
    "FORMULA/GWP CONTRACT AUDITED"
)

print(
    "NO PROJECT GWP VALUE SELECTED"
)

print(
    "NO CO2E RECONSTRUCTION PERFORMED"
)

print(
    "NO NATIONAL LRMER AGGREGATION CREATED"
)

print(
    "NO LRMER DELTAG CALCULATED"
)

print(
    "NO NEW CARBON CLASSIFICATION PRODUCED"
)

print("=" * 78)