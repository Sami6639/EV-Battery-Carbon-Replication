from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "src" / "vehicle_energy" / "p13_config.yaml"

with CONFIG.open(encoding="utf-8") as f:
    data = yaml.safe_load(f)


def find_key(obj, target, path="root"):
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}"

            if key == target:
                print(f"{new_path} = {value}")

            find_key(value, target, new_path)

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            find_key(
                value,
                target,
                f"{path}[{i}]",
            )


print("=" * 78)
print("BATTERY MAX POWER EXACT YAML PATH")
print("=" * 78)

find_key(
    data,
    "battery_max_power_watts",
)

print("=" * 78)