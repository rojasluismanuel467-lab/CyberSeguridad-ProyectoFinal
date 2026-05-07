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


def feature_eventos_por_usuario(logs: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering: total events per user from logs."""
    if logs.empty:
        return pd.DataFrame(columns=["usuario_id", "eventos_por_usuario"])

    return (
        logs.groupby("usuario_id", as_index=False)
        .size()
        .rename(columns={"size": "eventos_por_usuario"})
    )


def feature_modificaciones_por_mesa(logs: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering: total result modifications per mesa."""
    if logs.empty:
        return pd.DataFrame(columns=["mesa_id", "modificaciones_por_mesa"])

    modifications = logs[logs["accion"] == "modificar_resultado"].copy()
    if modifications.empty:
        return pd.DataFrame(columns=["mesa_id", "modificaciones_por_mesa"])

    return (
        modifications.groupby("mesa_id", as_index=False)
        .size()
        .rename(columns={"size": "modificaciones_por_mesa"})
    )
