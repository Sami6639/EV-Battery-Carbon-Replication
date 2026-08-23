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
print("P16R-D4E1A3 — OFFICIAL CAMBIUM-2023 LRMER CO2E HEADER AUDIT")
print("=" * 78)


if not WORKBOOK.is_file():
    raise RuntimeError(
        f"Workbook not found: {WORKBOOK}"
    )


# ============================================================
# 1. OPEN READ-ONLY
# ============================================================

wb = load_workbook(
    WORKBOOK,
    read_only=True,
    data_only=True,
)


print("\nWorkbook sheets:")

for sheet_name in wb.sheetnames:
    print(" -", sheet_name)


# ============================================================
# 2. SEARCH HEADER AREA ONLY
#
# Official documentation states that Cambium 2023 contains
# lrmer_co2e / CO2e metrics.
#
# We do NOT calculate CO2e ourselves.
# We search only for the official workbook metric.
# ============================================================

SEARCH_TERMS = (
    "co2e",
    "co₂e",
    "carbon dioxide equivalent",
    "co2 equivalent",
)

matches = []


for ws in wb.worksheets:

    # Header/metadata zone only.
    # No need to scan entire large workbook.
    max_rows_to_scan = min(
        ws.max_row or 100,
        100,
    )

    max_cols_to_scan = min(
        ws.max_column or 100,
        120,
    )

    for row in ws.iter_rows(
        min_row=1,
        max_row=max_rows_to_scan,
        min_col=1,
        max_col=max_cols_to_scan,
    ):

        for cell in row:

            value = cell.value

            if value is None:
                continue

            text = str(value).strip()

            lower = text.lower()

            if any(
                term in lower
                for term in SEARCH_TERMS
            ):
                matches.append(
                    {
                        "sheet": ws.title,
                        "cell": cell.coordinate,
                        "value": text,
                    }
                )


# ============================================================
# 3. DISPLAY EXACT OFFICIAL MATCHES
# ============================================================

print("\nOfficial CO2e-related workbook matches:")

if not matches:
    print("NONE FOUND IN FIRST 100 HEADER ROWS")
else:
    for item in matches:
        print(
            f"{item['sheet']} | "
            f"{item['cell']} | "
            f"{item['value']}"
        )


# ============================================================
# 4. SCIENTIFIC STATUS
# ============================================================

ready = len(matches) > 0


print("\n" + "=" * 78)

if ready:

    print(
        "P16R-D4E1A3 PASS — OFFICIAL CAMBIUM-2023 "
        "CO2E METRIC LOCATED IN RAW WORKBOOK"
    )

else:

    print(
        "P16R-D4E1A3 WITH BOUNDS — OFFICIAL CO2E "
        "HEADER NOT LOCATED IN HEADER SCAN"
    )

print(
    "GWP CONVERSION BY PROJECT: NONE"
)

print(
    "REGIONAL AVERAGE INVENTED: NO"
)

print(
    "US_LOAD_WEIGHTED LRMER INVENTED: NO"
)

print(
    "LRMER DELTAG CALCULATED: NO"
)

print(
    "NEW CARBON CLASSIFICATION PRODUCED: NO"
)

print("=" * 78)