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
print("P16R-D4E1B0 — FINAL ANNUAL OUTPUT HEADER BLOCK AUDIT")
print("=" * 78)


wb = load_workbook(
    WORKBOOK,
    read_only=True,
    data_only=True,
)

ws = wb["Data - Annual"]


# ============================================================
# 1. PRINT EVERY NON-EMPTY METRIC BLOCK HEADER FROM COLUMN P
# ============================================================

print("\nNON-EMPTY ROW-3 METRIC HEADERS FROM COLUMN P:")

headers = []

for col in range(16, ws.max_column + 1):

    metric = ws.cell(
        row=3,
        column=col,
    ).value

    if metric is None:
        continue

    metric = str(metric).strip()

    if metric == "":
        continue

    letter = ws.cell(
        row=3,
        column=col,
    ).column_letter

    scenario = ws.cell(
        row=4,
        column=col,
    ).value

    year = ws.cell(
        row=5,
        column=col,
    ).value

    headers.append(
        {
            "column": letter,
            "metric": metric,
            "scenario": scenario,
            "year": year,
        }
    )

    print(
        f"{letter} | "
        f"metric={metric} | "
        f"scenario={scenario} | "
        f"year={year}"
    )


# ============================================================
# 2. SHOW ONLY CO2E-RELATED BLOCK HEADERS
# ============================================================

print("\nCO2E-RELATED ROW-3 HEADERS:")

co2e_headers = []

for item in headers:

    lower = item["metric"].lower()

    if (
        "co2e" in lower
        or "co₂e" in lower
        or "co2-equivalent" in lower
        or "co2 equivalent" in lower
    ):

        co2e_headers.append(item)

        print(
            f"{item['column']} | "
            f"{item['metric']} | "
            f"{item['scenario']} | "
            f"{item['year']}"
        )


# ============================================================
# 3. DISPLAY WORKBOOK DIMENSIONS
# ============================================================

print("\nWorkbook annual-sheet dimensions:")

print(
    "max_row =",
    ws.max_row,
)

print(
    "max_column =",
    ws.max_column,
)

print(
    "non-empty metric block headers =",
    len(headers),
)

print(
    "CO2e-related metric block headers =",
    len(co2e_headers),
)


print("\n" + "=" * 78)

print(
    "P16R-D4E1B0 PASS — FINAL ANNUAL OUTPUT BLOCKS AUDITED"
)

print(
    "NO OUTPUT COLUMN SELECTED BY ASSUMPTION"
)

print(
    "NO LRMER DELTAG CALCULATED"
)

print(
    "NO NEW CARBON CLASSIFICATION PRODUCED"
)

print("=" * 78)