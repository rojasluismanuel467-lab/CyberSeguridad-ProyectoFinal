"""CSV loading utilities for Electoral Integrity Analyzer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.schemas import DATASET_ORDER


class DatasetLoadError(RuntimeError):
    """Raised when required datasets cannot be loaded."""


def load_datasets(base_path: str | Path = "data/synthetic") -> dict[str, pd.DataFrame]:
    """Load required CSV files from the synthetic data directory."""
    path = Path(base_path)
    datasets: dict[str, pd.DataFrame] = {}

    missing = [name for name in DATASET_ORDER if not (path / name).exists()]
    if missing:
        missing_str = ", ".join(missing)
        raise DatasetLoadError(f"Faltan datasets requeridos: {missing_str}")

    for filename in DATASET_ORDER:
        datasets[filename] = pd.read_csv(path / filename)

    return datasets
