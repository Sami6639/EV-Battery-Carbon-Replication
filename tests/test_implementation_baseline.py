"""Non-scientific implementation-preflight checks.

These tests verify only the frozen governing files, project structure, and
runtime imports. They do not execute scientific models or produce results.
"""

from importlib.metadata import version
from pathlib import Path
import sys

import fastsim
import matplotlib
import numpy
import openpyxl
import pandas
import pyarrow
import pytest
import scipy
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_python_and_required_package_versions() -> None:
    assert sys.version_info[:2] == (3, 11)
    assert version("fastsim") == "3.0.6"

    expected = {
        "numpy": "2.3.2",
        "pandas": "3.0.5",
        "scipy": "1.17.1",
        "matplotlib": "3.11.1",
        "pyarrow": "25.0.1",
        "openpyxl": "3.1.5",
        "pytest": "9.1.1",
        "PyYAML": "6.0.2",
    }
    assert {package: version(package) for package in expected} == expected


def test_required_imports_are_available() -> None:
    assert all(
        module is not None
        for module in (
            fastsim,
            numpy,
            pandas,
            scipy,
            matplotlib,
            pyarrow,
            openpyxl,
            pytest,
            yaml,
        )
    )


def test_governing_files_are_readable() -> None:
    required_files = (
        "PROJECT_INSTRUCTIONS.md",
        "docs/IMPLEMENTATION_SPEC.md",
        "environment.yml",
        "requirements-lock.txt",
    )
    for relative_path in required_files:
        path = ROOT / relative_path
        assert path.is_file()
        assert path.read_text(encoding="utf-8")


def test_required_directory_structure_exists() -> None:
    required_directories = (
        "data/raw",
        "data/processed",
        "data/metadata",
        "docs",
        "figures",
        "literature",
        "manuscript",
        "results",
        "src",
        "tables",
        "tests",
    )
    assert all((ROOT / relative_path).is_dir() for relative_path in required_directories)


def test_frozen_specification_baseline_markers() -> None:
    specification = (ROOT / "docs/IMPLEMENTATION_SPEC.md").read_text(encoding="utf-8")
    required_markers = (
        "FASTSim / vehicle physics",
        "HV battery-side electrical energy",
        "independently parameterized charging conversion",
        "Cambium-2023 LRMER sensitivity",
        "A fixed SOH threshold must **not** be used",
        "A percentage increase in cell resistance must NEVER be mapped directly",
    )
    assert all(marker in specification for marker in required_markers)
