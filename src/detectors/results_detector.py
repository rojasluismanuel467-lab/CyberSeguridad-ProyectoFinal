"""Results anomaly detector (RES codes)."""

from __future__ import annotations

import pandas as pd

from src.analytics.statistics import detect_outliers
from src.detectors.base import build_alert_row, to_alert_dataframe


class ResultsDetector:
    """Detect inconsistencies and statistical outliers in mesa results."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        results = datasets["05_resultados_mesa.csv"].copy()

        rows: list[dict[str, str | int]] = []
        idx = 1

        res01 = results[results["sufragantes_registrados"] > results["electores_habilitados"]]
        for _, record in res01.iterrows():
            rows.append(
                build_alert_row(
                    "RES-01",
                    "mesa_id",
                    record["mesa_id"],
                    "05_resultados_mesa.csv",
                    f"sufragantes={record['sufragantes_registrados']}; electores={record['electores_habilitados']}",
                    alert_index=idx,
                )
            )
            idx += 1

        res02 = results[results["participacion_pct"] > 1.0]
        for _, record in res02.iterrows():
            rows.append(
                build_alert_row(
                    "RES-02",
                    "mesa_id",
                    record["mesa_id"],
                    "05_resultados_mesa.csv",
                    f"participacion_pct={record['participacion_pct']}",
                    alert_index=idx,
                )
            )
            idx += 1

        res03 = results[results["total_reportado"] != results["total_calculado"]]
        for _, record in res03.iterrows():
            rows.append(
                build_alert_row(
                    "RES-03",
                    "mesa_id",
                    record["mesa_id"],
                    "05_resultados_mesa.csv",
                    f"total_reportado={record['total_reportado']}; total_calculado={record['total_calculado']}",
                    alert_index=idx,
                )
            )
            idx += 1

        participation_outliers = detect_outliers(results["participacion_pct"].fillna(0))
        for _, record in results[participation_outliers].iterrows():
            rows.append(
                build_alert_row(
                    "RES-04",
                    "mesa_id",
                    record["mesa_id"],
                    "05_resultados_mesa.csv",
                    f"participacion_pct={record['participacion_pct']}",
                    alert_index=idx,
                )
            )
            idx += 1

        total_reportado_nonzero = results["total_reportado"].replace(0, pd.NA)
        results["votos_nulos_pct"] = (results["votos_nulos"] / total_reportado_nonzero).fillna(0)
        results["votos_invalidos_pct"] = (results["votos_invalidos"] / total_reportado_nonzero).fillna(0)

        nulos_outliers = detect_outliers(results["votos_nulos_pct"])
        invalidos_outliers = detect_outliers(results["votos_invalidos_pct"])
        res05_mask = nulos_outliers | invalidos_outliers
        for _, record in results[res05_mask].iterrows():
            rows.append(
                build_alert_row(
                    "RES-05",
                    "mesa_id",
                    record["mesa_id"],
                    "05_resultados_mesa.csv",
                    f"votos_nulos_pct={record['votos_nulos_pct']:.4f}; votos_invalidos_pct={record['votos_invalidos_pct']:.4f}",
                    alert_index=idx,
                )
            )
            idx += 1

        concentration_outliers = detect_outliers(results["concentracion_ganador_pct"].fillna(0))
        margin_outliers = detect_outliers(results["margen_victoria_pct"].fillna(0))
        extreme_mask = concentration_outliers | margin_outliers | (results["concentracion_ganador_pct"] >= 0.9)
        for _, record in results[extreme_mask].iterrows():
            rows.append(
                build_alert_row(
                    "RES-06",
                    "mesa_id",
                    record["mesa_id"],
                    "05_resultados_mesa.csv",
                    (
                        "concentracion_ganador_pct={} ; margen_victoria_pct={}"
                    ).format(record["concentracion_ganador_pct"], record["margen_victoria_pct"]),
                    alert_index=idx,
                )
            )
            idx += 1

        return to_alert_dataframe(rows)
