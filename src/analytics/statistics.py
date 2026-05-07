"""Statistical helpers based on Z-score detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import zscore

from src.config.rules_config import Z_SCORE_THRESHOLD


def zscore_series(series: pd.Series) -> pd.Series:
    """Return z-score per value, handling low-variance edge cases."""
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    if len(numeric) < 2 or float(numeric.std(ddof=0)) == 0.0:
        return pd.Series(np.zeros(len(numeric)), index=series.index)
    z_values = zscore(numeric, nan_policy="omit")
    z_values = np.nan_to_num(z_values)
    return pd.Series(z_values, index=series.index)


def detect_outliers(series: pd.Series, threshold: float = Z_SCORE_THRESHOLD) -> pd.Series:
    """Return boolean mask where abs(z-score) exceeds threshold."""
    z_values = zscore_series(series)
    return z_values.abs() >= threshold
