"""Suffrage process anomaly detector (SUF codes)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.analytics.statistics import detect_outliers
from src.config.rules_config import ELECTION_CLOSE_TIME, ELECTION_OPEN_TIME, MIN_VOTING_AGE
from src.detectors.base import build_alert_row, to_alert_dataframe


class SuffrageDetector:
    """Detect anomalies focused on voting registry operations."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        padron = datasets["01_padron_votantes.csv"].copy()
        suffrage = datasets["03_registro_sufragio.csv"].copy()

        rows: list[dict[str, str | int]] = []
        idx = 1

        # SUF-01: potential double suffrage
        dup_counts = (
            suffrage[suffrage["voto_registrado"] == 1]
            .groupby("voter_id", as_index=False)
            .size()
            .rename(columns={"size": "conteo"})
        )
        duplicated = dup_counts[dup_counts["conteo"] > 1]
        for _, record in duplicated.iterrows():
            rows.append(
                build_alert_row(
                    "SUF-01",
                    "voter_id",
                    record["voter_id"],
                    "03_registro_sufragio.csv",
                    f"registros_sufragio={record['conteo']}",
                    alert_index=idx,
                )
            )
            idx += 1

        # SUF-02: check-in by unauthorized person
        merged = suffrage.merge(padron, on="voter_id", how="left", suffixes=("", "_padron"))
        unauthorized_mask = (
            (merged["edad"] < MIN_VOTING_AGE)
            | (merged["estado_documento"] == "cancelado")
            | (merged["condicion_legal"].isin(["fallecido", "inhabilitado", "privado_libertad"]))
            | (merged["habilitado_legalmente"] == 0)
        ) & (merged["voto_registrado"] == 1)
        unauthorized = merged[unauthorized_mask]

        for _, record in unauthorized.iterrows():
            rows.append(
                build_alert_row(
                    "SUF-02",
                    "voter_id",
                    record["voter_id"],
                    "03_registro_sufragio.csv",
                    (
                        "edad={} estado_documento={} condicion_legal={} habilitado={}"
                    ).format(
                        record.get("edad", "NA"),
                        record.get("estado_documento", "NA"),
                        record.get("condicion_legal", "NA"),
                        record.get("habilitado_legalmente", "NA"),
                    ),
                    alert_index=idx,
                )
            )
            idx += 1

        # SUF-03: check-in out of schedule
        open_time = datetime.strptime(ELECTION_OPEN_TIME, "%H:%M:%S").time()
        close_time = datetime.strptime(ELECTION_CLOSE_TIME, "%H:%M:%S").time()

        parsed_time = pd.to_datetime(suffrage["hora_checkin"], format="%H:%M:%S", errors="coerce").dt.time
        off_schedule_mask = parsed_time.notna() & ((parsed_time < open_time) | (parsed_time > close_time))
        off_schedule = suffrage[off_schedule_mask]

        for _, record in off_schedule.iterrows():
            rows.append(
                build_alert_row(
                    "SUF-03",
                    "suffrage_id",
                    record["suffrage_id"],
                    "03_registro_sufragio.csv",
                    f"hora_checkin={record['hora_checkin']} fuera de [{ELECTION_OPEN_TIME}, {ELECTION_CLOSE_TIME}]",
                    alert_index=idx,
                )
            )
            idx += 1

        # SUF-04: anomalous operator concentration
        operator_counts = suffrage.groupby("operador_checkin", as_index=False).size().rename(columns={"size": "conteo"})
        if not operator_counts.empty:
            outliers = detect_outliers(operator_counts["conteo"])
            for _, record in operator_counts[outliers].iterrows():
                rows.append(
                    build_alert_row(
                        "SUF-04",
                        "usuario_id",
                        record["operador_checkin"],
                        "03_registro_sufragio.csv",
                        f"checkins_operador={record['conteo']}",
                        alert_index=idx,
                    )
                )
                idx += 1

        return to_alert_dataframe(rows)
