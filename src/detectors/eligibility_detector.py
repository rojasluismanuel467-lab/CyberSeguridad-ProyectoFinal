"""Eligibility anomaly detector (PAD codes)."""

from __future__ import annotations

import pandas as pd

from src.config.rules_config import MAX_REASONABLE_AGE, MIN_VOTING_AGE
from src.detectors.base import build_alert_row, to_alert_dataframe


class EligibilityDetector:
    """Detect anomalies tied to voter eligibility and registry quality."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        padron = datasets["01_padron_votantes.csv"].copy()
        suffrage = datasets["03_registro_sufragio.csv"].copy()

        voted_ids = set(suffrage.loc[suffrage["voto_registrado"] == 1, "voter_id"].astype(str))
        rows: list[dict[str, str | int]] = []
        idx = 1

        mask_pad01 = (padron["condicion_legal"] == "fallecido") & (padron["voter_id"].astype(str).isin(voted_ids))
        for _, record in padron[mask_pad01].iterrows():
            rows.append(
                build_alert_row(
                    "PAD-01",
                    "voter_id",
                    record["voter_id"],
                    "01_padron_votantes.csv",
                    f"condicion_legal={record['condicion_legal']}; voto_registrado=1",
                    alert_index=idx,
                )
            )
            idx += 1

        mask_pad02 = (padron["edad"] < MIN_VOTING_AGE) & (padron["voter_id"].astype(str).isin(voted_ids))
        for _, record in padron[mask_pad02].iterrows():
            rows.append(
                build_alert_row(
                    "PAD-02",
                    "voter_id",
                    record["voter_id"],
                    "01_padron_votantes.csv",
                    f"edad={record['edad']}; voto_registrado=1",
                    alert_index=idx,
                )
            )
            idx += 1

        mask_pad03 = padron["edad"] > MAX_REASONABLE_AGE
        for _, record in padron[mask_pad03].iterrows():
            rows.append(
                build_alert_row(
                    "PAD-03",
                    "voter_id",
                    record["voter_id"],
                    "01_padron_votantes.csv",
                    f"edad={record['edad']} > {MAX_REASONABLE_AGE}",
                    alert_index=idx,
                )
            )
            idx += 1

        mask_pad04 = (padron["estado_documento"] == "cancelado") & (padron["voter_id"].astype(str).isin(voted_ids))
        for _, record in padron[mask_pad04].iterrows():
            rows.append(
                build_alert_row(
                    "PAD-04",
                    "voter_id",
                    record["voter_id"],
                    "01_padron_votantes.csv",
                    f"estado_documento={record['estado_documento']}; voto_registrado=1",
                    alert_index=idx,
                )
            )
            idx += 1

        mask_pad05 = (
            padron["condicion_legal"].isin(["inhabilitado", "privado_libertad"])
            & (padron["voter_id"].astype(str).isin(voted_ids))
        )
        for _, record in padron[mask_pad05].iterrows():
            rows.append(
                build_alert_row(
                    "PAD-05",
                    "voter_id",
                    record["voter_id"],
                    "01_padron_votantes.csv",
                    f"condicion_legal={record['condicion_legal']}; voto_registrado=1",
                    alert_index=idx,
                )
            )
            idx += 1

        duplicated_mask = padron["documento_hash"].duplicated(keep=False)
        for _, record in padron[duplicated_mask].iterrows():
            rows.append(
                build_alert_row(
                    "PAD-06",
                    "voter_id",
                    record["voter_id"],
                    "01_padron_votantes.csv",
                    f"documento_hash_duplicado={record['documento_hash']}",
                    alert_index=idx,
                )
            )
            idx += 1

        return to_alert_dataframe(rows)
