"""Risk scoring and ranking utilities."""

from __future__ import annotations

import pandas as pd

from src.config.rules_config import CRITICAL_SCORE, HIGH_SCORE, MEDIUM_SCORE

SEVERITY_TO_SCORE = {
    "critica": CRITICAL_SCORE,
    "alta": HIGH_SCORE,
    "media": MEDIUM_SCORE,
}


def normalize_scores(alerts: pd.DataFrame) -> pd.DataFrame:
    """Ensure score column is aligned with severity labels."""
    if alerts.empty:
        return alerts.copy()

    normalized = alerts.copy()
    normalized["score"] = normalized["severidad"].map(SEVERITY_TO_SCORE).fillna(MEDIUM_SCORE).astype(int)
    return normalized


def classify_risk(score_total: int) -> str:
    """Risk level from guide thresholds."""
    if score_total <= 0:
        return "Sin alerta"
    if 1 <= score_total <= 3:
        return "Riesgo bajo"
    if 4 <= score_total <= 7:
        return "Riesgo medio"
    if 8 <= score_total <= 12:
        return "Riesgo alto"
    return "Revisión prioritaria"


def generate_risk_ranking(alerts: pd.DataFrame) -> pd.DataFrame:
    """Generate risk ranking for key entity dimensions."""
    if alerts.empty:
        return pd.DataFrame(
            columns=["entidad_tipo", "entidad_id", "score_total", "total_alertas", "max_severidad", "clasificacion_riesgo"]
        )

    normalized = normalize_scores(alerts)
    allowed_entity_types = {"mesa_id", "voter_id", "usuario_id", "archivo_id", "evento_id"}
    filtered = normalized[normalized["entidad_tipo"].isin(allowed_entity_types)].copy()

    if filtered.empty:
        return pd.DataFrame(
            columns=["entidad_tipo", "entidad_id", "score_total", "total_alertas", "max_severidad", "clasificacion_riesgo"]
        )

    severity_order = {"media": 1, "alta": 2, "critica": 3}
    aggregated = (
        filtered.groupby(["entidad_tipo", "entidad_id"], as_index=False)
        .agg(score_total=("score", "sum"), total_alertas=("codigo_alerta", "count"), max_severidad=("severidad", lambda s: s.iloc[s.map(severity_order).argmax()]))
        .sort_values(["score_total", "total_alertas"], ascending=[False, False])
        .reset_index(drop=True)
    )

    aggregated["clasificacion_riesgo"] = aggregated["score_total"].apply(classify_risk)
    return aggregated
