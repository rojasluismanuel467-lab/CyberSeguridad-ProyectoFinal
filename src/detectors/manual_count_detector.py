"""Manual count anomaly detector (MAN codes)."""

from __future__ import annotations

import pandas as pd

from src.analytics.statistics import detect_outliers
from src.detectors.base import build_alert_row, to_alert_dataframe


class ManualCountDetector:
    """Detect anomalies in manual vote classification."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        manual = datasets["04_clasificacion_votos_manual.csv"].copy()

        rows: list[dict[str, str | int]] = []
        idx = 1

        man01 = manual[
            (manual["clasificacion_objetiva"] == "valido")
            & (manual["clasificacion_jurado"].isin(["invalido", "nulo"]))
        ]
        for _, record in man01.iterrows():
            rows.append(
                build_alert_row(
                    "MAN-01",
                    "ballot_id",
                    record["ballot_id"],
                    "04_clasificacion_votos_manual.csv",
                    f"objetiva={record['clasificacion_objetiva']}; jurado={record['clasificacion_jurado']}",
                    alert_index=idx,
                )
            )
            idx += 1

        man02 = manual[
            (manual["clasificacion_objetiva"].isin(["invalido", "nulo"]))
            & (manual["clasificacion_jurado"] == "valido")
        ]
        for _, record in man02.iterrows():
            rows.append(
                build_alert_row(
                    "MAN-02",
                    "ballot_id",
                    record["ballot_id"],
                    "04_clasificacion_votos_manual.csv",
                    f"objetiva={record['clasificacion_objetiva']}; jurado={record['clasificacion_jurado']}",
                    alert_index=idx,
                )
            )
            idx += 1

        mesa_stats = manual.groupby("mesa_id", as_index=False).agg(
            total=("ballot_id", "count"),
            invalidos=("clasificacion_jurado", lambda s: int((s == "invalido").sum())),
        )
        mesa_stats["invalid_rate"] = mesa_stats["invalidos"] / mesa_stats["total"].replace(0, pd.NA)
        mesa_outliers = detect_outliers(mesa_stats["invalid_rate"].fillna(0))
        for _, record in mesa_stats[mesa_outliers].iterrows():
            rows.append(
                build_alert_row(
                    "MAN-03",
                    "mesa_id",
                    record["mesa_id"],
                    "04_clasificacion_votos_manual.csv",
                    f"invalid_rate={record['invalid_rate']:.4f}",
                    alert_index=idx,
                )
            )
            idx += 1

        classifier_stats = manual.groupby("usuario_clasificador", as_index=False).agg(
            total=("ballot_id", "count"),
            invalidos=("clasificacion_jurado", lambda s: int((s == "invalido").sum())),
        )
        classifier_stats["invalid_rate"] = classifier_stats["invalidos"] / classifier_stats["total"].replace(0, pd.NA)
        classifier_outliers = detect_outliers(classifier_stats["invalid_rate"].fillna(0))
        for _, record in classifier_stats[classifier_outliers].iterrows():
            rows.append(
                build_alert_row(
                    "MAN-04",
                    "usuario_id",
                    record["usuario_clasificador"],
                    "04_clasificacion_votos_manual.csv",
                    f"invalid_rate={record['invalid_rate']:.4f}",
                    alert_index=idx,
                )
            )
            idx += 1

        return to_alert_dataframe(rows)
