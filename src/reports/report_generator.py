"""CSV report export utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_reports(
    alerts: pd.DataFrame,
    ranking: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: str | Path = "data/outputs",
) -> dict[str, Path]:
    """Export mandatory CSV outputs to data/outputs."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    files = {
        "alerts": out_path / "alertas_detectadas.csv",
        "ranking": out_path / "ranking_riesgo.csv",
        "summary": out_path / "resumen_hallazgos.csv",
    }

    alerts.to_csv(files["alerts"], index=False)
    ranking.to_csv(files["ranking"], index=False)
    summary.to_csv(files["summary"], index=False)

    return files
