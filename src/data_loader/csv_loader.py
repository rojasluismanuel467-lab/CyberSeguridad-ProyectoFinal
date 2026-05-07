"""CSV loading utilities for Electoral Integrity Analyzer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.schemas import DATASET_ORDER


class DatasetLoadError(RuntimeError):
    """Raised when required datasets cannot be loaded."""


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load one CSV file from disk."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise DatasetLoadError(f"No existe el archivo CSV: {csv_path}")
    return pd.read_csv(csv_path)


def load_all_datasets(base_path: str | Path = "data/synthetic") -> dict[str, pd.DataFrame]:
    """Load all required synthetic datasets from base directory."""
    path = Path(base_path)
    datasets: dict[str, pd.DataFrame] = {}

    missing = [name for name in DATASET_ORDER if not (path / name).exists()]
    if missing:
        missing_str = ", ".join(missing)
        raise DatasetLoadError(f"Faltan datasets requeridos: {missing_str}")

    for filename in DATASET_ORDER:
        datasets[filename] = load_csv(path / filename)

    return datasets


def load_datasets(base_path: str | Path = "data/synthetic") -> dict[str, pd.DataFrame]:
    """Backward-compatible alias for loading all datasets."""
    return load_all_datasets(base_path)
