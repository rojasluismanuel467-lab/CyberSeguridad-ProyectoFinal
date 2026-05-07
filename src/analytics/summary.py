"""Summary and evaluation utilities."""

from __future__ import annotations

import pandas as pd


def evaluate_against_ground_truth(alerts: pd.DataFrame, expected_alerts: pd.DataFrame) -> dict[str, float | int]:
    """Compare detected alerts against synthetic expected anomalies."""
    if expected_alerts is None or expected_alerts.empty:
        return {
            "alertas_esperadas": 0,
            "alertas_detectadas": int(len(alerts)),
            "coincidencias": 0,
            "precision_aproximada": 0.0,
            "cobertura_aproximada": 0.0,
        }

    detected_keys = set(
        alerts[["codigo_alerta", "entidad_tipo", "entidad_id"]]
        .fillna("")
        .astype(str)
        .itertuples(index=False, name=None)
    )
    expected_keys = set(
        expected_alerts[["codigo_alerta", "entidad_tipo", "entidad_id"]]
        .fillna("")
        .astype(str)
        .itertuples(index=False, name=None)
    )

    coincidencias = len(detected_keys & expected_keys)
    detected_count = len(detected_keys)
    expected_count = len(expected_keys)

    precision = (coincidencias / detected_count) if detected_count else 0.0
    coverage = (coincidencias / expected_count) if expected_count else 0.0

    return {
        "alertas_esperadas": expected_count,
        "alertas_detectadas": detected_count,
        "coincidencias": coincidencias,
        "precision_aproximada": round(precision, 4),
        "cobertura_aproximada": round(coverage, 4),
    }


def build_summary(
    alerts: pd.DataFrame,
    ranking: pd.DataFrame,
    expected_alerts: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build one-table summary used by dashboard and CSV export."""
    total_alerts = len(alerts)
    critical_alerts = int((alerts["severidad"] == "critica").sum()) if not alerts.empty else 0
    total_entities = int(ranking[["entidad_tipo", "entidad_id"]].drop_duplicates().shape[0]) if not ranking.empty else 0

    evaluation = evaluate_against_ground_truth(alerts, expected_alerts if expected_alerts is not None else pd.DataFrame())

    rows = [
        {"metrica": "alertas_totales", "valor": total_alerts},
        {"metrica": "alertas_criticas", "valor": critical_alerts},
        {"metrica": "entidades_en_ranking", "valor": total_entities},
        {"metrica": "alertas_esperadas", "valor": evaluation["alertas_esperadas"]},
        {"metrica": "alertas_detectadas", "valor": evaluation["alertas_detectadas"]},
        {"metrica": "coincidencias", "valor": evaluation["coincidencias"]},
        {"metrica": "precision_aproximada", "valor": evaluation["precision_aproximada"]},
        {"metrica": "cobertura_aproximada", "valor": evaluation["cobertura_aproximada"]},
    ]

    return pd.DataFrame(rows)
