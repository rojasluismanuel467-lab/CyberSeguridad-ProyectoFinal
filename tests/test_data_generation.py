"""Tests for synthetic dataset generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.generate_synthetic_data import main as generate_data_main
from src.domain.schemas import DATASET_ORDER, DATASET_SCHEMAS

BASE_PATH = Path("data/synthetic")


def test_generated_files_exist() -> None:
    generate_data_main()
    for filename in DATASET_ORDER:
        assert (BASE_PATH / filename).exists(), f"Missing generated file: {filename}"


def test_generated_files_have_rows_and_expected_columns() -> None:
    generate_data_main()
    for filename in DATASET_ORDER:
        df = pd.read_csv(BASE_PATH / filename)
        expected_columns = DATASET_SCHEMAS[filename]
        for col in expected_columns:
            assert col in df.columns, f"Column {col} missing in {filename}"
        assert len(df) > 0, f"Dataset {filename} should not be empty"


def test_expected_alerts_not_empty() -> None:
    generate_data_main()
    alerts = pd.read_csv(BASE_PATH / "08_alertas_esperadas.csv")
    assert len(alerts) > 0
    assert {"codigo_alerta", "entidad_tipo", "entidad_id"}.issubset(alerts.columns)
