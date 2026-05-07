"""Log and file-integrity anomaly detector (LOG and INT codes)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.config.rules_config import ELECTION_CLOSE_TIME, ELECTION_DATE
from src.detectors.base import build_alert_row, to_alert_dataframe

ALLOWED_ACTIONS_BY_ROLE = {
    "ADMIN_ELECTORAL": {
        "login",
        "logout",
        "crear_registro",
        "actualizar_padron",
        "registrar_checkin",
        "clasificar_voto",
        "cargar_resultado",
        "modificar_resultado",
        "aprobar_correccion",
        "generar_hash",
        "publicar_reporte",
        "consultar_alertas",
        "exportar_reporte",
    },
    "OPERADOR_PADRON": {"login", "logout", "actualizar_padron", "consultar_alertas"},
    "JURADO_MESA": {"login", "logout", "registrar_checkin", "consultar_alertas"},
    "CLASIFICADOR_MANUAL": {"login", "logout", "clasificar_voto", "consultar_alertas"},
    "SUPERVISOR_ESCRUTINIO": {
        "login",
        "logout",
        "cargar_resultado",
        "modificar_resultado",
        "aprobar_correccion",
        "consultar_alertas",
    },
    "OPERADOR_TECNICO": {"login", "logout", "generar_hash", "exportar_reporte", "consultar_alertas"},
    "ANALISTA_SEGURIDAD": {"login", "logout", "consultar_alertas", "exportar_reporte"},
    "AUDITOR": {"login", "logout", "consultar_alertas", "exportar_reporte"},
    "SERVICIO_SISTEMA": {"generar_hash", "publicar_reporte"},
}


class LogIntegrityDetector:
    """Detect unauthorized behavior and integrity violations."""

    def detect(self, datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
        logs = datasets["06_logs_eventos.csv"].copy()
        integrity = datasets["07_integridad_archivos.csv"].copy()
        users = datasets["usuarios_sistema.csv"].copy()

        rows: list[dict[str, str | int]] = []
        idx = 1

        close_dt = datetime.strptime(f"{ELECTION_DATE} {ELECTION_CLOSE_TIME}", "%Y-%m-%d %H:%M:%S")
        logs["timestamp_dt"] = pd.to_datetime(logs["timestamp"], errors="coerce")

        log01_mask = (
            (logs["accion"] == "modificar_resultado")
            & (logs["timestamp_dt"] > close_dt)
            & (logs["requiere_aprobacion"] == 1)
            & (logs["aprobado_por"].fillna("").astype(str).str.strip() == "")
        )
        for _, record in logs[log01_mask].iterrows():
            rows.append(
                build_alert_row(
                    "LOG-01",
                    "evento_id",
                    record["evento_id"],
                    "06_logs_eventos.csv",
                    f"accion={record['accion']}; timestamp={record['timestamp']}; aprobado_por_vacio",
                    alert_index=idx,
                )
            )
            idx += 1

        allowed = logs.apply(
            lambda r: r["accion"] in ALLOWED_ACTIONS_BY_ROLE.get(r["rol_usuario"], set()), axis=1
        )
        for _, record in logs[~allowed].iterrows():
            rows.append(
                build_alert_row(
                    "LOG-02",
                    "evento_id",
                    record["evento_id"],
                    "06_logs_eventos.csv",
                    f"rol={record['rol_usuario']}; accion={record['accion']}",
                    alert_index=idx,
                )
            )
            idx += 1

        user_state = users.set_index("usuario_id")["estado_usuario"].to_dict()
        logs["estado_usuario"] = logs["usuario_id"].map(user_state).fillna("desconocido")
        log03 = logs[logs["estado_usuario"].isin(["inactivo", "suspendido", "desconocido"])]
        for _, record in log03.iterrows():
            rows.append(
                build_alert_row(
                    "LOG-03",
                    "usuario_id",
                    record["usuario_id"],
                    "06_logs_eventos.csv",
                    f"estado_usuario={record['estado_usuario']}; accion={record['accion']}",
                    alert_index=idx,
                )
            )
            idx += 1

        failed_login = logs[(logs["accion"] == "login") & (logs["resultado_accion"] == "fallido")]
        failed_counts = failed_login.groupby("usuario_id", as_index=False).size().rename(columns={"size": "fallos"})
        repeated = failed_counts[failed_counts["fallos"] >= 5]
        for _, record in repeated.iterrows():
            rows.append(
                build_alert_row(
                    "LOG-04",
                    "usuario_id",
                    record["usuario_id"],
                    "06_logs_eventos.csv",
                    f"fallos_login={record['fallos']}",
                    alert_index=idx,
                )
            )
            idx += 1

        log05 = logs[
            (logs["hash_antes"].astype(str) != logs["hash_despues"].astype(str))
            & (logs["requiere_aprobacion"] == 0)
        ]
        for _, record in log05.iterrows():
            rows.append(
                build_alert_row(
                    "LOG-05",
                    "evento_id",
                    record["evento_id"],
                    "06_logs_eventos.csv",
                    f"hash_antes={record['hash_antes']}; hash_despues={record['hash_despues']}",
                    alert_index=idx,
                )
            )
            idx += 1

        log06 = logs[
            (logs["accion"] == "aprobar_correccion")
            & (logs["aprobado_por"].fillna("").astype(str).str.strip() == logs["usuario_id"].astype(str))
        ]
        for _, record in log06.iterrows():
            rows.append(
                build_alert_row(
                    "LOG-06",
                    "evento_id",
                    record["evento_id"],
                    "06_logs_eventos.csv",
                    f"usuario_id={record['usuario_id']} aprueba su propio cambio",
                    alert_index=idx,
                )
            )
            idx += 1

        int01 = integrity[integrity["hash_original"].astype(str) != integrity["hash_actual"].astype(str)]
        for _, record in int01.iterrows():
            rows.append(
                build_alert_row(
                    "INT-01",
                    "archivo_id",
                    record["archivo_id"],
                    "07_integridad_archivos.csv",
                    f"hash_original={record['hash_original']}; hash_actual={record['hash_actual']}",
                    alert_index=idx,
                )
            )
            idx += 1

        int02 = integrity[integrity["reporte_publicado_total"] != integrity["reporte_firmado_total"]]
        for _, record in int02.iterrows():
            rows.append(
                build_alert_row(
                    "INT-02",
                    "archivo_id",
                    record["archivo_id"],
                    "07_integridad_archivos.csv",
                    "reporte_publicado_total={} ; reporte_firmado_total={}".format(
                        record["reporte_publicado_total"], record["reporte_firmado_total"]
                    ),
                    alert_index=idx,
                )
            )
            idx += 1

        integrity["timestamp_firma_dt"] = pd.to_datetime(integrity["timestamp_firma"], errors="coerce")
        integrity["timestamp_publicacion_dt"] = pd.to_datetime(integrity["timestamp_publicacion"], errors="coerce")

        int03 = integrity[integrity["timestamp_publicacion_dt"] < integrity["timestamp_firma_dt"]]
        for _, record in int03.iterrows():
            rows.append(
                build_alert_row(
                    "INT-03",
                    "archivo_id",
                    record["archivo_id"],
                    "07_integridad_archivos.csv",
                    f"publicacion={record['timestamp_publicacion']}; firma={record['timestamp_firma']}",
                    alert_index=idx,
                )
            )
            idx += 1

        int04 = integrity[
            (integrity["estado_integridad"] == "alterado")
            & (integrity["timestamp_publicacion_dt"] > close_dt)
        ]
        for _, record in int04.iterrows():
            rows.append(
                build_alert_row(
                    "INT-04",
                    "archivo_id",
                    record["archivo_id"],
                    "07_integridad_archivos.csv",
                    f"estado_integridad={record['estado_integridad']}; timestamp_publicacion={record['timestamp_publicacion']}",
                    alert_index=idx,
                )
            )
            idx += 1

        return to_alert_dataframe(rows)
