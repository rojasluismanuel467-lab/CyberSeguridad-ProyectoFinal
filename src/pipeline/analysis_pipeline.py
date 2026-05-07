"""End-to-end analysis orchestration pipeline."""

from __future__ import annotations

import pandas as pd

from src.analytics.risk_score import generate_risk_ranking, normalize_scores
from src.analytics.summary import build_summary
from src.domain.alert_types import ALERT_COLUMNS


class AnalysisPipeline:
    """Orchestrates all detectors and post-processing steps."""

    def __init__(self, detectors: list):
        self.detectors = detectors

    def run(self, datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        all_alerts: list[pd.DataFrame] = []

        for detector in self.detectors:
            detected = detector.detect(datasets)
            if detected is None or detected.empty:
                continue
            all_alerts.append(detected[ALERT_COLUMNS])

        consolidated_alerts = (
            pd.concat(all_alerts, ignore_index=True)
            if all_alerts
            else pd.DataFrame(columns=ALERT_COLUMNS)
        )

        consolidated_alerts = normalize_scores(consolidated_alerts)
        ranking = generate_risk_ranking(consolidated_alerts)
        expected = datasets.get("08_alertas_esperadas.csv", pd.DataFrame())
        summary = build_summary(consolidated_alerts, ranking, expected)

        return {
            "alerts": consolidated_alerts,
            "ranking": ranking,
            "summary": summary,
        }
