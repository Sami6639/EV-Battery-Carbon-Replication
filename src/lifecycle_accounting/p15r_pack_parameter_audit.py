from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

PARAM_FILE = (
    ROOT
    / "results"
    / "intermediate"
    / "p13_vehicle_energy_model_parameters.json"
)

with PARAM_FILE.open(encoding="utf-8") as f:
    data = json.load(f)


KEYWORDS = (
    "pack",
    "capacity",
    "nominal",
    "kwh",
    "energy",
)


def walk(obj, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            walk(value, f"{path}.{key}")

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            walk(value, f"{path}[{i}]")

    else:
        lower_path = path.lower()

        if any(keyword in lower_path for keyword in KEYWORDS):
            print(f"{path} = {obj}")


print("=" * 78)
print("P13 PACK / CAPACITY PARAMETER AUDIT")
print("=" * 78)

walk(data)

print("=" * 78)
print("AUDIT COMPLETE — NO FILES MODIFIED")
print("=" * 78)