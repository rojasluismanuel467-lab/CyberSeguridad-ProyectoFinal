"""Circumscription anomaly detector (CIR codes)."""

from __future__ import annotations

import pandas as pd

from src.detectors.base import build_alert_row, to_alert_dataframe


class CircumscriptionDetector:
    """Detect anomalies related to mesa/circunscription and ballot type."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        assignments = datasets["02_asignacion_mesas.csv"].copy()
        suffrage = datasets["03_registro_sufragio.csv"].copy()

        merged = suffrage.merge(assignments, on="voter_id", how="left", suffixes=("_voto", "_asignada"))
        rows: list[dict[str, str | int]] = []
        idx = 1

        cir01 = merged[merged["mesa_voto"].astype(str) != merged["mesa_asignada"].astype(str)]
        for _, record in cir01.iterrows():
            rows.append(
                build_alert_row(
                    "CIR-01",
                    "voter_id",
                    record["voter_id"],
                    "03_registro_sufragio.csv",
                    f"mesa_voto={record['mesa_voto']}; mesa_asignada={record['mesa_asignada']}",
                    alert_index=idx,
                )
            )
            idx += 1

        cir02 = merged[
            merged["circunscripcion_voto"].astype(str) != merged["circunscripcion_autorizada"].astype(str)
        ]
        for _, record in cir02.iterrows():
            rows.append(
                build_alert_row(
                    "CIR-02",
                    "voter_id",
                    record["voter_id"],
                    "03_registro_sufragio.csv",
                    "circ_voto={} ; circ_autorizada={}".format(
                        record["circunscripcion_voto"], record["circunscripcion_autorizada"]
                    ),
                    alert_index=idx,
                )
            )
            idx += 1

        # For each circunscription, use majority ballot type as expected baseline.
        circ_mode = (
            assignments.groupby("circunscripcion_autorizada")["tipo_boleta_autorizada"]
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
            .to_dict()
        )
        expected_boleta = assignments["circunscripcion_autorizada"].map(circ_mode)
        cir03 = assignments[assignments["tipo_boleta_autorizada"].astype(str) != expected_boleta.astype(str)]

        for _, record in cir03.iterrows():
            expected = circ_mode.get(record["circunscripcion_autorizada"], "desconocido")
            rows.append(
                build_alert_row(
                    "CIR-03",
                    "voter_id",
                    record["voter_id"],
                    "02_asignacion_mesas.csv",
                    f"tipo_boleta={record['tipo_boleta_autorizada']}; esperado={expected}",
                    alert_index=idx,
                )
            )
            idx += 1

        return to_alert_dataframe(rows)
