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
print("P16R-D4E1A4 — CAMBIUM-2023 ANNUAL CO2E HEADER MAP")
print("=" * 78)


wb = load_workbook(
    WORKBOOK,
    read_only=True,
    data_only=True,
)


# ============================================================
# 1. DATA - ANNUAL HEADER MAP
# ============================================================

ws = wb["Data - Annual"]

print("\nDATA - ANNUAL | A1:P10")

for r in range(1, 11):

    cells = []

    for c in range(1, 17):

        value = ws.cell(
            row=r,
            column=c,
        ).value

        if value is not None:

            coord = ws.cell(
                row=r,
                column=c,
            ).coordinate

            cells.append(
                f"{coord}={value}"
            )

    if cells:
        print(
            " | ".join(cells)
        )


# ============================================================
# 2. LOOKUPS OFFICIAL CO2E DEFINITIONS
# ============================================================

look = wb["Lookups"]

print("\nLOOKUPS | A35:C42")

for r in range(35, 43):

    values = []

    for c in range(1, 4):

        cell = look.cell(
            row=r,
            column=c,
        )

        if cell.value is not None:

            values.append(
                f"{cell.coordinate}={cell.value}"
            )

    if values:
        print(
            " | ".join(values)
        )


# ============================================================
# 3. GWP DECLARATION
# ============================================================

gwp = wb["GWP"]

print("\nGWP | A1:F12")

for r in range(1, 13):

    values = []

    for c in range(1, 7):

        cell = gwp.cell(
            row=r,
            column=c,
        )

        if cell.value is not None:

            values.append(
                f"{cell.coordinate}={cell.value}"
            )

    if values:
        print(
            " | ".join(values)
        )


print("\n" + "=" * 78)

print(
    "P16R-D4E1A4 PASS — OFFICIAL ANNUAL CO2E "
    "HEADER STRUCTURE DISPLAYED"
)

print(
    "NO CO2E COMPONENT SELECTED BY ASSUMPTION"
)

print(
    "NO GWP FACTOR SELECTED BY PROJECT"
)

print(
    "NO REGIONAL AGGREGATION CREATED"
)

print(
    "NO LRMER DELTAG CALCULATED"
)

print("=" * 78)