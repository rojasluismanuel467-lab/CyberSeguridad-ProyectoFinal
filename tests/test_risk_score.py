"""Tests for risk scoring logic."""

from __future__ import annotations

import pandas as pd

from src.analytics.risk_score import classify_risk, generate_risk_ranking, normalize_scores


def test_severity_score_mapping() -> None:
    alerts = pd.DataFrame(
        [
            {"severidad": "critica", "codigo_alerta": "A", "entidad_tipo": "mesa_id", "entidad_id": "M1"},
            {"severidad": "alta", "codigo_alerta": "B", "entidad_tipo": "mesa_id", "entidad_id": "M1"},
            {"severidad": "media", "codigo_alerta": "C", "entidad_tipo": "mesa_id", "entidad_id": "M2"},
        ]
    )

    normalized = normalize_scores(alerts)
    scores = normalized["score"].tolist()

    assert scores == [3, 2, 1]


def test_risk_classification_thresholds() -> None:
    assert classify_risk(0) == "Sin alerta"
    assert classify_risk(2) == "Riesgo bajo"
    assert classify_risk(5) == "Riesgo medio"
    assert classify_risk(10) == "Riesgo alto"
    assert classify_risk(20) == "Revisión prioritaria"


def test_generate_risk_ranking_aggregates_scores() -> None:
    alerts = pd.DataFrame(
        [
            {"codigo_alerta": "PAD-01", "severidad": "critica", "entidad_tipo": "mesa_id", "entidad_id": "MESA-001", "score": 3},
            {"codigo_alerta": "RES-03", "severidad": "alta", "entidad_tipo": "mesa_id", "entidad_id": "MESA-001", "score": 2},
            {"codigo_alerta": "LOG-04", "severidad": "media", "entidad_tipo": "usuario_id", "entidad_id": "USR-0001", "score": 1},
        ]
    )

    ranking = generate_risk_ranking(alerts)

    mesa_row = ranking[(ranking["entidad_tipo"] == "mesa_id") & (ranking["entidad_id"] == "MESA-001")].iloc[0]
    assert int(mesa_row["score_total"]) == 5
    assert mesa_row["clasificacion_riesgo"] == "Riesgo medio"
