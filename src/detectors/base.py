"""Common detector contract and alert-row helpers."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from src.config.rules_config import CRITICAL_SCORE, HIGH_SCORE, MEDIUM_SCORE
from src.domain.alert_types import ALERT_CATALOG, ALERT_COLUMNS


class AlertDetector(Protocol):
    """Detector contract enforced across all detection modules."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        ...


def severity_to_score(severity: str) -> int:
    mapping = {
        "critica": CRITICAL_SCORE,
        "alta": HIGH_SCORE,
        "media": MEDIUM_SCORE,
    }
    return mapping.get(severity, MEDIUM_SCORE)


def build_alert_row(
    codigo_alerta: str,
    entidad_tipo: str,
    entidad_id: str,
    dataset_origen: str,
    evidencia: str,
    *,
    descripcion: str | None = None,
    etapa: str | None = None,
    severidad: str | None = None,
    accion_recomendada: str | None = None,
    alert_index: int = 0,
) -> dict[str, str | int]:
    metadata = ALERT_CATALOG.get(codigo_alerta, {})
    resolved_severity = severidad or metadata.get("severidad", "media")

    return {
        "alerta_id": f"DET-{codigo_alerta}-{alert_index:06d}",
        "codigo_alerta": codigo_alerta,
        "severidad": resolved_severity,
        "etapa": etapa or metadata.get("etapa", "General"),
        "entidad_tipo": entidad_tipo,
        "entidad_id": str(entidad_id),
        "dataset_origen": dataset_origen,
        "descripcion": descripcion or metadata.get("descripcion", "Alerta detectada"),
        "evidencia": evidencia,
        "accion_recomendada": accion_recomendada or metadata.get("accion", "Revisar evidencia técnica."),
        "score": severity_to_score(resolved_severity),
    }


def to_alert_dataframe(rows: list[dict[str, str | int]]) -> pd.DataFrame:
    """Build normalized alert DataFrame with mandatory columns."""
    if not rows:
        return pd.DataFrame(columns=ALERT_COLUMNS)
    return pd.DataFrame(rows)[ALERT_COLUMNS]
