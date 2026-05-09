"""Generate synthetic electoral datasets with reproducible anomalies."""

from __future__ import annotations

import hashlib
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.rules_config import (
    ELECTION_CLOSE_TIME,
    ELECTION_DATE,
    ELECTION_OPEN_TIME,
    MAX_REASONABLE_AGE,
    MIN_VOTING_AGE,
    NUM_MUNICIPALITIES,
    NUM_POLLING_STATIONS,
    NUM_TABLES,
    NUM_USERS,
    NUM_VOTERS,
    NUM_ZONES,
    RANDOM_SEED,
)

OUTPUT_DIR = Path("data/synthetic")

ROLE_DISTRIBUTION = {
    "ADMIN_ELECTORAL": 2,
    "OPERADOR_PADRON": 8,
    "JURADO_MESA": 15,
    "CLASIFICADOR_MANUAL": 10,
    "SUPERVISOR_ESCRUTINIO": 5,
    "OPERADOR_TECNICO": 6,
    "ANALISTA_SEGURIDAD": 4,
    "AUDITOR": 5,
    "SERVICIO_SISTEMA": 5,
}

ALLOWED_ACTIONS = [
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
]

ROLE_ALLOWED_ACTIONS = {
    "ADMIN_ELECTORAL": set(ALLOWED_ACTIONS),
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

ALERT_SEVERITY = {
    "PAD-01": "critica",
    "PAD-02": "critica",
    "PAD-03": "alta",
    "PAD-04": "critica",
    "PAD-05": "critica",
    "PAD-06": "alta",
    "CIR-01": "alta",
    "CIR-02": "critica",
    "CIR-03": "alta",
    "SUF-01": "critica",
    "SUF-02": "critica",
    "SUF-03": "alta",
    "SUF-04": "alta",
    "MAN-01": "alta",
    "MAN-02": "alta",
    "MAN-03": "media",
    "MAN-04": "alta",
    "RES-01": "critica",
    "RES-02": "critica",
    "RES-03": "alta",
    "RES-04": "media",
    "RES-05": "media",
    "RES-06": "media",
    "LOG-01": "critica",
    "LOG-02": "critica",
    "LOG-03": "alta",
    "LOG-04": "media",
    "LOG-05": "critica",
    "LOG-06": "critica",
    "INT-01": "critica",
    "INT-02": "critica",
    "INT-03": "alta",
    "INT-04": "alta",
}


def hash_value(raw: str) -> str:
    """Create deterministic hash for synthetic ids and records."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def make_alert(
    expected_alerts: list[dict[str, Any]],
    codigo_alerta: str,
    entidad_tipo: str,
    entidad_id: str,
    dataset_origen: str,
    descripcion: str,
) -> None:
    expected_alerts.append(
        {
            "alerta_id": f"EXP-{len(expected_alerts) + 1:06d}",
            "codigo_alerta": codigo_alerta,
            "entidad_tipo": entidad_tipo,
            "entidad_id": entidad_id,
            "dataset_origen": dataset_origen,
            "severidad": ALERT_SEVERITY[codigo_alerta],
            "descripcion": descripcion,
        }
    )


def create_geography() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    municipalities = pd.DataFrame(
        {
            "municipio": [f"MUN-{i:02d}" for i in range(1, NUM_MUNICIPALITIES + 1)],
            "circunscripcion": [f"CIRC-{i:02d}" for i in range(1, NUM_MUNICIPALITIES + 1)],
        }
    )

    zones = pd.DataFrame(
        {
            "zona_id": [f"ZONA-{i:02d}" for i in range(1, NUM_ZONES + 1)],
        }
    )
    zones["municipio"] = zones.index.map(lambda idx: municipalities.iloc[idx % NUM_MUNICIPALITIES]["municipio"])

    polling_stations = pd.DataFrame(
        {
            "puesto_id": [f"PUESTO-{i:03d}" for i in range(1, NUM_POLLING_STATIONS + 1)],
        }
    )
    polling_stations["zona_id"] = polling_stations.index.map(lambda idx: zones.iloc[idx % NUM_ZONES]["zona_id"])
    polling_stations = polling_stations.merge(zones, on="zona_id", how="left")

    tables = pd.DataFrame(
        {
            "mesa_id": [f"MESA-{i:03d}" for i in range(1, NUM_TABLES + 1)],
        }
    )
    tables["puesto_id"] = tables.index.map(
        lambda idx: polling_stations.iloc[idx % NUM_POLLING_STATIONS]["puesto_id"]
    )
    tables = tables.merge(polling_stations, on="puesto_id", how="left")
    tables = tables.merge(municipalities, on="municipio", how="left")

    return municipalities, zones, polling_stations, tables


def assign_role_permissions(role: str) -> dict[str, int]:
    return {
        "puede_modificar_padron": int("actualizar_padron" in ROLE_ALLOWED_ACTIONS[role]),
        "puede_registrar_sufragio": int("registrar_checkin" in ROLE_ALLOWED_ACTIONS[role]),
        "puede_clasificar_votos": int("clasificar_voto" in ROLE_ALLOWED_ACTIONS[role]),
        "puede_modificar_resultados": int("modificar_resultado" in ROLE_ALLOWED_ACTIONS[role]),
        "puede_aprobar_cambios": int("aprobar_correccion" in ROLE_ALLOWED_ACTIONS[role]),
        "puede_ver_logs": int("consultar_alertas" in ROLE_ALLOWED_ACTIONS[role]),
    }


def create_users(fake: Faker, tables: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    idx = 1
    for role, count in ROLE_DISTRIBUTION.items():
        for _ in range(count):
            table = tables.sample(1, random_state=RANDOM_SEED + idx).iloc[0]
            permissions = assign_role_permissions(role)
            state = np.random.choice(["activo", "inactivo", "suspendido"], p=[0.85, 0.1, 0.05])
            records.append(
                {
                    "usuario_id": f"USR-{idx:04d}",
                    "nombre_usuario": fake.user_name(),
                    "rol": role,
                    "estado_usuario": state,
                    "zona_asignada": table["zona_id"],
                    "mesa_asignada": table["mesa_id"],
                    "puede_modificar_padron": permissions["puede_modificar_padron"],
                    "puede_registrar_sufragio": permissions["puede_registrar_sufragio"],
                    "puede_clasificar_votos": permissions["puede_clasificar_votos"],
                    "puede_modificar_resultados": permissions["puede_modificar_resultados"],
                    "puede_aprobar_cambios": permissions["puede_aprobar_cambios"],
                    "puede_ver_logs": permissions["puede_ver_logs"],
                    "requiere_mfa": int(np.random.rand() < 0.75),
                }
            )
            idx += 1
    users = pd.DataFrame(records)
    if len(users) != NUM_USERS:
        raise ValueError(f"Expected {NUM_USERS} users but created {len(users)}")
    return users


def create_voters(tables: pd.DataFrame) -> pd.DataFrame:
    voter_ids = [f"V{i:06d}" for i in range(1, NUM_VOTERS + 1)]
    ages = np.random.randint(18, 91, size=NUM_VOTERS)
    election_day = datetime.strptime(ELECTION_DATE, "%Y-%m-%d")

    table_choices = np.random.choice(tables.index, size=NUM_VOTERS, replace=True)
    assigned_tables = tables.iloc[table_choices].reset_index(drop=True)

    voters = pd.DataFrame(
        {
            "voter_id": voter_ids,
            "documento_hash": [hash_value(f"DOC-{voter_id}-{RANDOM_SEED}")[:20] for voter_id in voter_ids],
            "edad": ages,
            "fecha_nacimiento": [
                (election_day - timedelta(days=int(age * 365.25))).strftime("%Y-%m-%d") for age in ages
            ],
            "fecha_defuncion": ["" for _ in voter_ids],
            "estado_documento": "vigente",
            "condicion_legal": "normal",
            "habilitado_legalmente": 1,
            "estado_padron": "activo",
            "municipio": assigned_tables["municipio"].values,
            "zona_id": assigned_tables["zona_id"].values,
            "circunscripcion_autorizada": assigned_tables["circunscripcion"].values,
            "mesa_asignada": assigned_tables["mesa_id"].values,
        }
    )
    print("[PROGRESS] 15", flush=True)
    return voters


def sample_distinct(pool: np.ndarray, n: int, used: set[int]) -> np.ndarray:
    available = np.array([idx for idx in pool if idx not in used])
    chosen = np.random.choice(available, size=n, replace=False)
    used.update(chosen.tolist())
    return chosen


def inject_padron_anomalies(voters: pd.DataFrame, expected_alerts: list[dict[str, Any]]) -> pd.DataFrame:
    election_day = datetime.strptime(ELECTION_DATE, "%Y-%m-%d")
    used_indices: set[int] = set()
    all_indices = voters.index.to_numpy()

    deceased_idx = sample_distinct(all_indices, int(NUM_VOTERS * 0.02), used_indices)
    for idx in deceased_idx:
        death_date = election_day - timedelta(days=int(np.random.randint(30, 900)))
        voters.at[idx, "condicion_legal"] = "fallecido"
        voters.at[idx, "fecha_defuncion"] = death_date.strftime("%Y-%m-%d")
        voters.at[idx, "estado_padron"] = "activo"
        voters.at[idx, "habilitado_legalmente"] = 1
        make_alert(
            expected_alerts,
            "PAD-01",
            "voter_id",
            voters.at[idx, "voter_id"],
            "01_padron_votantes.csv",
            "Persona fallecida marcada como activa en padrón.",
        )
    print("[PROGRESS] 23", flush=True)

    minors_idx = sample_distinct(all_indices, int(NUM_VOTERS * 0.015), used_indices)
    for idx in minors_idx:
        age = int(np.random.randint(15, 18))
        voters.at[idx, "edad"] = age
        voters.at[idx, "fecha_nacimiento"] = (election_day - timedelta(days=int(age * 365.25))).strftime("%Y-%m-%d")
        voters.at[idx, "habilitado_legalmente"] = 1
        make_alert(
            expected_alerts,
            "PAD-02",
            "voter_id",
            voters.at[idx, "voter_id"],
            "01_padron_votantes.csv",
            "Menor de edad habilitado legalmente.",
        )

    impossible_age_idx = sample_distinct(all_indices, int(NUM_VOTERS * 0.01), used_indices)
    for idx in impossible_age_idx:
        age = int(np.random.randint(MAX_REASONABLE_AGE + 1, 131))
        voters.at[idx, "edad"] = age
        voters.at[idx, "fecha_nacimiento"] = (election_day - timedelta(days=int(age * 365.25))).strftime("%Y-%m-%d")
        make_alert(
            expected_alerts,
            "PAD-03",
            "voter_id",
            voters.at[idx, "voter_id"],
            "01_padron_votantes.csv",
            "Edad superior al máximo razonable permitido.",
        )

    canceled_docs_idx = sample_distinct(all_indices, int(NUM_VOTERS * 0.015), used_indices)
    for idx in canceled_docs_idx:
        voters.at[idx, "estado_documento"] = "cancelado"
        voters.at[idx, "habilitado_legalmente"] = 1
        make_alert(
            expected_alerts,
            "PAD-04",
            "voter_id",
            voters.at[idx, "voter_id"],
            "01_padron_votantes.csv",
            "Documento cancelado marcado como habilitado.",
        )
    print("[PROGRESS] 28", flush=True)

    ineligible_idx = sample_distinct(all_indices, int(NUM_VOTERS * 0.01), used_indices)
    for idx in ineligible_idx:
        voters.at[idx, "condicion_legal"] = np.random.choice(["inhabilitado", "privado_libertad"])
        voters.at[idx, "habilitado_legalmente"] = 1
        make_alert(
            expected_alerts,
            "PAD-05",
            "voter_id",
            voters.at[idx, "voter_id"],
            "01_padron_votantes.csv",
            "Persona legalmente inhabilitada marcada como habilitada.",
        )

    duplicate_targets = np.random.choice(all_indices, size=int(NUM_VOTERS * 0.005), replace=False)
    duplicate_sources = np.random.choice(all_indices, size=len(duplicate_targets), replace=False)
    for src, tgt in zip(duplicate_sources, duplicate_targets):
        if src == tgt:
            continue
        voters.at[tgt, "documento_hash"] = voters.at[src, "documento_hash"]
        make_alert(
            expected_alerts,
            "PAD-06",
            "voter_id",
            voters.at[tgt, "voter_id"],
            "01_padron_votantes.csv",
            "Documento hash duplicado en padrón.",
        )

    return voters


def create_assignments(voters: pd.DataFrame, tables: pd.DataFrame, expected_alerts: list[dict[str, Any]]) -> pd.DataFrame:
    base = voters[["voter_id", "mesa_asignada", "zona_id", "municipio", "circunscripcion_autorizada"]].copy()
    table_map = tables.set_index("mesa_id")

    base["puesto_asignado"] = base["mesa_asignada"].map(table_map["puesto_id"])
    base.rename(
        columns={
            "zona_id": "zona_asignada",
            "municipio": "municipio_asignado",
        },
        inplace=True,
    )

    circ_unique = sorted(base["circunscripcion_autorizada"].unique())

    def boleta_for_circ(circ: str) -> str:
        circ_idx = circ_unique.index(circ)
        if circ_idx % 5 == 0:
            return "especial"
        if circ_idx % 2 == 0:
            return "municipal"
        return "nacional"

    base["tipo_boleta_autorizada"] = base["circunscripcion_autorizada"].map(boleta_for_circ)
    base["puede_votar_en_otro_puesto"] = 0
    base["justificacion_excepcion"] = ""

    wrong_table_idx = np.random.choice(base.index, size=int(NUM_VOTERS * 0.02), replace=False)
    for idx in wrong_table_idx:
        new_table = tables.sample(1, random_state=RANDOM_SEED + idx).iloc[0]
        if new_table["mesa_id"] == base.at[idx, "mesa_asignada"]:
            continue
        base.at[idx, "mesa_asignada"] = new_table["mesa_id"]
        base.at[idx, "puesto_asignado"] = new_table["puesto_id"]
        base.at[idx, "zona_asignada"] = new_table["zona_id"]
        base.at[idx, "municipio_asignado"] = new_table["municipio"]
        base.at[idx, "justificacion_excepcion"] = "inconsistencia_simulada_mesa"
        make_alert(
            expected_alerts,
            "CIR-01",
            "voter_id",
            base.at[idx, "voter_id"],
            "02_asignacion_mesas.csv",
            "Mesa asignada incompatible con padrón base.",
        )
    print("[PROGRESS] 38", flush=True)

    wrong_circ_idx = np.random.choice(base.index, size=int(NUM_VOTERS * 0.015), replace=False)
    all_circs = base["circunscripcion_autorizada"].unique().tolist()
    for idx in wrong_circ_idx:
        current = base.at[idx, "circunscripcion_autorizada"]
        alternatives = [c for c in all_circs if c != current]
        base.at[idx, "circunscripcion_autorizada"] = np.random.choice(alternatives)
        make_alert(
            expected_alerts,
            "CIR-02",
            "voter_id",
            base.at[idx, "voter_id"],
            "02_asignacion_mesas.csv",
            "Circunscripción autorizada inconsistente.",
        )
    print("[PROGRESS] 42", flush=True)

    wrong_ballot_idx = np.random.choice(base.index, size=int(NUM_VOTERS * 0.01), replace=False)
    for idx in wrong_ballot_idx:
        current = base.at[idx, "tipo_boleta_autorizada"]
        options = ["nacional", "municipal", "especial"]
        options.remove(current)
        base.at[idx, "tipo_boleta_autorizada"] = np.random.choice(options)
        make_alert(
            expected_alerts,
            "CIR-03",
            "voter_id",
            base.at[idx, "voter_id"],
            "02_asignacion_mesas.csv",
            "Tipo de boleta autorizada no corresponde a circunscripción.",
        )

    return base[
        [
            "voter_id",
            "mesa_asignada",
            "puesto_asignado",
            "zona_asignada",
            "municipio_asignado",
            "circunscripcion_autorizada",
            "tipo_boleta_autorizada",
            "puede_votar_en_otro_puesto",
            "justificacion_excepcion",
        ]
    ]


def random_time_between(start: datetime, end: datetime) -> str:
    delta_seconds = int((end - start).total_seconds())
    random_seconds = int(np.random.randint(0, max(delta_seconds, 1)))
    return (start + timedelta(seconds=random_seconds)).strftime("%H:%M:%S")


def create_suffrage(
    voters: pd.DataFrame,
    assignments: pd.DataFrame,
    users: pd.DataFrame,
    expected_alerts: list[dict[str, Any]],
) -> pd.DataFrame:
    padron = voters.set_index("voter_id")
    assignment_map = assignments.set_index("voter_id")

    unauthorized_mask = (
        (voters["edad"] < MIN_VOTING_AGE)
        | (voters["condicion_legal"].isin(["fallecido", "inhabilitado", "privado_libertad"]))
        | (voters["estado_documento"] == "cancelado")
    )

    authorized_voters = voters.loc[~unauthorized_mask, "voter_id"].values
    base_voters = np.random.choice(
        authorized_voters,
        size=int(round(len(authorized_voters) * 0.70)),
        replace=False,
    )

    checkin_operators = users.loc[
        users["rol"].isin(["JURADO_MESA", "OPERADOR_PADRON"]) & (users["estado_usuario"] == "activo"), "usuario_id"
    ].tolist()
    if not checkin_operators:
        raise ValueError("No active check-in operators available")

    open_dt = datetime.strptime(f"{ELECTION_DATE} {ELECTION_OPEN_TIME}", "%Y-%m-%d %H:%M:%S")
    close_dt = datetime.strptime(f"{ELECTION_DATE} {ELECTION_CLOSE_TIME}", "%Y-%m-%d %H:%M:%S")

    records: list[dict[str, Any]] = []
    sid = 1
    total_base = len(base_voters)
    for i, voter_id in enumerate(base_voters):
        assign = assignment_map.loc[voter_id]
        records.append(
            {
                "suffrage_id": f"SUF-{sid:07d}",
                "voter_id": voter_id,
                "fecha_eleccion": ELECTION_DATE,
                "voto_registrado": 1,
                "mesa_voto": assign["mesa_asignada"],
                "puesto_voto": assign["puesto_asignado"],
                "zona_voto": assign["zona_asignada"],
                "municipio_voto": assign["municipio_asignado"],
                "circunscripcion_voto": assign["circunscripcion_autorizada"],
                "hora_checkin": random_time_between(open_dt, close_dt),
                "metodo_checkin": np.random.choice(["manual", "electronico"], p=[0.35, 0.65]),
                "operador_checkin": np.random.choice(checkin_operators),
            }
        )
        sid += 1
        if i % max(1, total_base // 4) == 0 and i > 0:
            p = 45 + (i / total_base) * 10
            print(f"[PROGRESS] {int(p)}", flush=True)

    suffrage = pd.DataFrame(records)

    # SUF-01: double suffrage
    dup_count = max(1, int(len(suffrage) * 0.01))
    double_voters = np.random.choice(suffrage["voter_id"].unique(), size=dup_count, replace=False)
    duplicate_rows = suffrage[suffrage["voter_id"].isin(double_voters)].copy()
    duplicate_rows["suffrage_id"] = [f"SUF-{i:07d}" for i in range(sid, sid + len(duplicate_rows))]
    duplicate_rows["hora_checkin"] = [random_time_between(open_dt, close_dt) for _ in range(len(duplicate_rows))]
    sid += len(duplicate_rows)
    suffrage = pd.concat([suffrage, duplicate_rows], ignore_index=True)
    for voter_id in double_voters:
        make_alert(
            expected_alerts,
            "SUF-01",
            "voter_id",
            voter_id,
            "03_registro_sufragio.csv",
            "Votante con más de un registro de sufragio.",
        )

    # SUF-02: unauthorized check-ins
    unauthorized_voters = voters.loc[unauthorized_mask, "voter_id"].values
    unauthorized_count = max(1, int(NUM_VOTERS * 0.02))
    unauthorized_selected = np.random.choice(unauthorized_voters, size=min(unauthorized_count, len(unauthorized_voters)), replace=False)
    unauthorized_rows: list[dict[str, Any]] = []
    for voter_id in unauthorized_selected:
        assign = assignment_map.loc[voter_id]
        unauthorized_rows.append(
            {
                "suffrage_id": f"SUF-{sid:07d}",
                "voter_id": voter_id,
                "fecha_eleccion": ELECTION_DATE,
                "voto_registrado": 1,
                "mesa_voto": assign["mesa_asignada"],
                "puesto_voto": assign["puesto_asignado"],
                "zona_voto": assign["zona_asignada"],
                "municipio_voto": assign["municipio_asignado"],
                "circunscripcion_voto": assign["circunscripcion_autorizada"],
                "hora_checkin": random_time_between(open_dt, close_dt),
                "metodo_checkin": np.random.choice(["manual", "electronico"]),
                "operador_checkin": np.random.choice(checkin_operators),
            }
        )
        sid += 1
        make_alert(
            expected_alerts,
            "SUF-02",
            "voter_id",
            voter_id,
            "03_registro_sufragio.csv",
            "Check-in registrado para persona no habilitada.",
        )
    if unauthorized_rows:
        suffrage = pd.concat([suffrage, pd.DataFrame(unauthorized_rows)], ignore_index=True)

    # CIR and SUF anomalies on voting place and circumscription
    wrong_vote_count = max(1, int(len(suffrage) * 0.03))
    wrong_vote_idx = np.random.choice(suffrage.index, size=wrong_vote_count, replace=False)
    table_map = assignments.set_index("voter_id")
    for idx in wrong_vote_idx:
        voter_id = suffrage.at[idx, "voter_id"]
        current_mesa = suffrage.at[idx, "mesa_voto"]
        candidate_rows = assignments[assignments["mesa_asignada"] != current_mesa]
        replacement = candidate_rows.sample(1, random_state=RANDOM_SEED + idx).iloc[0]

        suffrage.at[idx, "mesa_voto"] = replacement["mesa_asignada"]
        suffrage.at[idx, "puesto_voto"] = replacement["puesto_asignado"]
        suffrage.at[idx, "zona_voto"] = replacement["zona_asignada"]
        suffrage.at[idx, "municipio_voto"] = replacement["municipio_asignado"]

        if idx % 2 == 0:
            suffrage.at[idx, "circunscripcion_voto"] = replacement["circunscripcion_autorizada"]
            make_alert(
                expected_alerts,
                "CIR-01",
                "voter_id",
                voter_id,
                "03_registro_sufragio.csv",
                "Voto registrado en mesa distinta de la asignada.",
            )
        else:
            current_circ = table_map.loc[voter_id, "circunscripcion_autorizada"]
            circ_options = [c for c in assignments["circunscripcion_autorizada"].unique() if c != current_circ]
            suffrage.at[idx, "circunscripcion_voto"] = np.random.choice(circ_options)
            make_alert(
                expected_alerts,
                "CIR-02",
                "voter_id",
                voter_id,
                "03_registro_sufragio.csv",
                "Voto registrado en circunscripción no autorizada.",
            )

    # SUF-03: out-of-schedule check-in
    off_hours_count = max(1, int(len(suffrage) * 0.02))
    off_hours_idx = np.random.choice(suffrage.index, size=off_hours_count, replace=False)
    for idx in off_hours_idx:
        if idx % 2 == 0:
            out_dt = open_dt - timedelta(minutes=int(np.random.randint(1, 120)))
        else:
            out_dt = close_dt + timedelta(minutes=int(np.random.randint(1, 180)))
        suffrage.at[idx, "hora_checkin"] = out_dt.strftime("%H:%M:%S")
        make_alert(
            expected_alerts,
            "SUF-03",
            "suffrage_id",
            suffrage.at[idx, "suffrage_id"],
            "03_registro_sufragio.csv",
            "Check-in fuera de horario electoral.",
        )

    # SUF-04: operator concentration anomaly
    anomalous_operator = np.random.choice(checkin_operators)
    forced_idx = np.random.choice(suffrage.index, size=max(1, int(len(suffrage) * 0.1)), replace=False)
    suffrage.loc[forced_idx, "operador_checkin"] = anomalous_operator
    make_alert(
        expected_alerts,
        "SUF-04",
        "usuario_id",
        anomalous_operator,
        "03_registro_sufragio.csv",
        "Operador con concentración atípica de check-ins.",
    )

    return suffrage.sort_values("suffrage_id").reset_index(drop=True)


def classify_objective(mark: str) -> str:
    if mark in {"candidato_A", "candidato_B", "candidato_C"}:
        return "valido"
    if mark == "blanco":
        return "blanco"
    if mark == "marca_ambigua":
        return np.random.choice(["nulo", "invalido"])
    if mark == "multiple_marca":
        return "nulo"
    return "invalido"


def create_manual_count(
    suffrage: pd.DataFrame,
    users: pd.DataFrame,
    expected_alerts: list[dict[str, Any]],
) -> pd.DataFrame:
    marks = [
        "candidato_A",
        "candidato_B",
        "candidato_C",
        "blanco",
        "marca_ambigua",
        "multiple_marca",
        "sin_marca",
    ]
    probs = [0.4, 0.35, 0.15, 0.05, 0.025, 0.015, 0.01]

    classifiers = users.loc[
        (users["rol"] == "CLASIFICADOR_MANUAL") & (users["estado_usuario"] == "activo"), "usuario_id"
    ].tolist()
    if not classifiers:
        raise ValueError("No active manual classifiers available")

    valid_votes = suffrage[suffrage["voto_registrado"] == 1].copy()
    records: list[dict[str, Any]] = []
    total_valid = len(valid_votes)

    for i, (idx, row) in enumerate(valid_votes.iterrows()):
        mark = np.random.choice(marks, p=probs)
        objective = classify_objective(mark)
        records.append(
            {
                "ballot_id": f"BAL-{idx + 1:07d}",
                "mesa_id": row["mesa_voto"],
                "voter_id": row["voter_id"],
                "marca_simulada": mark,
                "clasificacion_objetiva": objective,
                "clasificacion_jurado": objective,
                "clasificacion_auditoria": objective,
                "usuario_clasificador": np.random.choice(classifiers),
            }
        )
        if i % max(1, total_valid // 4) == 0 and i > 0:
            p = 60 + (i / total_valid) * 10
            print(f"[PROGRESS] {int(p)}", flush=True)

    manual = pd.DataFrame(records)

    # MAN-01
    man01_idx = manual[(manual["clasificacion_objetiva"] == "valido")].sample(
        n=max(1, int(len(manual) * 0.015)), random_state=RANDOM_SEED
    ).index
    manual.loc[man01_idx, "clasificacion_jurado"] = "invalido"
    for idx in man01_idx:
        make_alert(
            expected_alerts,
            "MAN-01",
            "ballot_id",
            manual.at[idx, "ballot_id"],
            "04_clasificacion_votos_manual.csv",
            "Voto objetivamente válido declarado inválido.",
        )

    # MAN-02
    man02_candidates = manual[manual["clasificacion_objetiva"].isin(["nulo", "invalido"])].index
    if len(man02_candidates) > 0:
        man02_idx = np.random.choice(man02_candidates, size=max(1, int(len(manual) * 0.01)), replace=False)
        manual.loc[man02_idx, "clasificacion_jurado"] = "valido"
        for idx in man02_idx:
            make_alert(
                expected_alerts,
                "MAN-02",
                "ballot_id",
                manual.at[idx, "ballot_id"],
                "04_clasificacion_votos_manual.csv",
                "Voto objetivamente inválido declarado válido.",
            )

    # MAN-03
    man03_candidates = manual[manual["clasificacion_objetiva"] == "blanco"].index
    if len(man03_candidates) > 0:
        man03_idx = np.random.choice(man03_candidates, size=max(1, int(len(manual) * 0.008)), replace=False)
        manual.loc[man03_idx, "clasificacion_jurado"] = "nulo"
        for idx in man03_idx:
            make_alert(
                expected_alerts,
                "MAN-03",
                "ballot_id",
                manual.at[idx, "ballot_id"],
                "04_clasificacion_votos_manual.csv",
                "Voto blanco reclasificado indebidamente.",
            )

    # MAN-04 classifier anomaly
    anomalous_classifier = np.random.choice(classifiers)
    classifier_idx = manual[manual["usuario_clasificador"] == anomalous_classifier].sample(
        n=max(5, int(len(manual) * 0.05)),
        random_state=RANDOM_SEED,
        replace=True,
    ).index
    manual.loc[classifier_idx, "clasificacion_jurado"] = "invalido"
    make_alert(
        expected_alerts,
        "MAN-04",
        "usuario_id",
        anomalous_classifier,
        "04_clasificacion_votos_manual.csv",
        "Clasificador manual con tasa anómala de invalidación.",
    )

    return manual


def create_results(
    manual: pd.DataFrame,
    assignments: pd.DataFrame,
    voters: pd.DataFrame,
    expected_alerts: list[dict[str, Any]],
) -> pd.DataFrame:
    assign_map = assignments.set_index("voter_id")
    voters_map = voters.set_index("voter_id")

    manual = manual.copy()
    manual["municipio"] = manual["voter_id"].map(voters_map["municipio"])
    manual["zona_id"] = manual["voter_id"].map(voters_map["zona_id"])
    manual["circunscripcion"] = manual["voter_id"].map(assign_map["circunscripcion_autorizada"])

    grouped = manual.groupby("mesa_id", dropna=False)
    rows: list[dict[str, Any]] = []
    total_mesas = len(grouped)
    
    for i, (mesa_id, grp) in enumerate(grouped):
        if i % max(1, total_mesas // 5) == 0 and i > 0:
            p = 75 + (i / total_mesas) * 10
            print(f"[PROGRESS] {int(p)}", flush=True)
        
        municipio = grp["municipio"].iloc[0]
        zona_id = grp["zona_id"].iloc[0]
        circ = grp["circunscripcion"].iloc[0]

        electores_habilitados = int(
            voters[
                (voters["mesa_asignada"] == mesa_id)
                & (voters["habilitado_legalmente"] == 1)
                & (voters["edad"] >= MIN_VOTING_AGE)
            ].shape[0]
        )
        sufragantes = int(grp.shape[0])

        votos_a = int((grp["marca_simulada"] == "candidato_A").sum())
        votos_b = int((grp["marca_simulada"] == "candidato_B").sum())
        votos_c = int((grp["marca_simulada"] == "candidato_C").sum())
        votos_blancos = int((grp["clasificacion_jurado"] == "blanco").sum())
        votos_nulos = int((grp["clasificacion_jurado"] == "nulo").sum())
        votos_invalidos = int((grp["clasificacion_jurado"] == "invalido").sum())

        total_calculado = votos_a + votos_b + votos_c + votos_blancos + votos_nulos + votos_invalidos
        total_reportado = total_calculado
        participacion_pct = (sufragantes / electores_habilitados) if electores_habilitados else 0.0

        candidate_votes = {"A": votos_a, "B": votos_b, "C": votos_c}
        sorted_votes = sorted(candidate_votes.items(), key=lambda x: x[1], reverse=True)
        ganador = f"candidato_{sorted_votes[0][0]}"
        ganador_votos = sorted_votes[0][1]
        segundo_votos = sorted_votes[1][1]
        concentration = (ganador_votos / total_reportado) if total_reportado else 0.0
        margin = ((ganador_votos - segundo_votos) / total_reportado) if total_reportado else 0.0

        rows.append(
            {
                "mesa_id": mesa_id,
                "municipio": municipio,
                "zona_id": zona_id,
                "circunscripcion": circ,
                "electores_habilitados": electores_habilitados,
                "sufragantes_registrados": sufragantes,
                "votos_candidato_A": votos_a,
                "votos_candidato_B": votos_b,
                "votos_candidato_C": votos_c,
                "votos_blancos": votos_blancos,
                "votos_nulos": votos_nulos,
                "votos_invalidos": votos_invalidos,
                "total_calculado": total_calculado,
                "total_reportado": total_reportado,
                "participacion_pct": round(participacion_pct, 4),
                "ganador": ganador,
                "concentracion_ganador_pct": round(concentration, 4),
                "margen_victoria_pct": round(margin, 4),
            }
        )

    results = pd.DataFrame(rows)

    # RES-01 and RES-02
    res01_idx = results.sample(n=max(1, int(len(results) * 0.08)), random_state=RANDOM_SEED).index
    for idx in res01_idx:
        extra = int(np.random.randint(3, 20))
        results.at[idx, "sufragantes_registrados"] = int(results.at[idx, "electores_habilitados"]) + extra
        if results.at[idx, "electores_habilitados"] == 0:
            results.at[idx, "electores_habilitados"] = 1
        results.at[idx, "participacion_pct"] = round(
            results.at[idx, "sufragantes_registrados"] / results.at[idx, "electores_habilitados"], 4
        )
        make_alert(
            expected_alerts,
            "RES-01",
            "mesa_id",
            results.at[idx, "mesa_id"],
            "05_resultados_mesa.csv",
            "Sufragantes registrados mayores que electores habilitados.",
        )
        if results.at[idx, "participacion_pct"] > 1.0:
            make_alert(
                expected_alerts,
                "RES-02",
                "mesa_id",
                results.at[idx, "mesa_id"],
                "05_resultados_mesa.csv",
                "Participación superior al 100%.",
            )

    # RES-03
    res03_idx = results.sample(n=max(1, int(len(results) * 0.06)), random_state=RANDOM_SEED + 3).index
    for idx in res03_idx:
        results.at[idx, "total_reportado"] = int(results.at[idx, "total_calculado"]) + int(np.random.randint(1, 7))
        make_alert(
            expected_alerts,
            "RES-03",
            "mesa_id",
            results.at[idx, "mesa_id"],
            "05_resultados_mesa.csv",
            "Total reportado no coincide con total calculado.",
        )

    # RES-06 extreme concentration (also affects z-score)
    res06_idx = results.sample(n=max(1, int(len(results) * 0.05)), random_state=RANDOM_SEED + 7).index
    for idx in res06_idx:
        total = max(int(results.at[idx, "total_reportado"]), 20)
        votos_a = int(total * 0.92)
        votos_b = int(total * 0.05)
        votos_c = max(total - votos_a - votos_b, 0)
        results.at[idx, "votos_candidato_A"] = votos_a
        results.at[idx, "votos_candidato_B"] = votos_b
        results.at[idx, "votos_candidato_C"] = votos_c
        results.at[idx, "concentracion_ganador_pct"] = round(votos_a / total, 4)
        results.at[idx, "margen_victoria_pct"] = round((votos_a - votos_b) / total, 4)
        results.at[idx, "ganador"] = "candidato_A"
        make_alert(
            expected_alerts,
            "RES-06",
            "mesa_id",
            results.at[idx, "mesa_id"],
            "05_resultados_mesa.csv",
            "Concentración extrema del ganador.",
        )

    # RES-05: unusual null/invalid percentages
    res05_idx = results.sample(n=max(1, int(len(results) * 0.05)), random_state=RANDOM_SEED + 11).index
    for idx in res05_idx:
        total = max(int(results.at[idx, "total_reportado"]), 30)
        results.at[idx, "votos_nulos"] = int(total * 0.25)
        results.at[idx, "votos_invalidos"] = int(total * 0.2)
        make_alert(
            expected_alerts,
            "RES-05",
            "mesa_id",
            results.at[idx, "mesa_id"],
            "05_resultados_mesa.csv",
            "Porcentaje atípico de votos nulos o inválidos.",
        )

    return results


def random_ip() -> str:
    return f"10.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}"


def build_timestamp(base_dt: datetime, min_offset: int, max_offset: int) -> str:
    dt = base_dt + timedelta(minutes=int(np.random.randint(min_offset, max_offset)))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_logs(
    users: pd.DataFrame,
    tables: pd.DataFrame,
    expected_alerts: list[dict[str, Any]],
) -> pd.DataFrame:
    base_dt = datetime.strptime(f"{ELECTION_DATE} 06:00:00", "%Y-%m-%d %H:%M:%S")
    close_dt = datetime.strptime(f"{ELECTION_DATE} {ELECTION_CLOSE_TIME}", "%Y-%m-%d %H:%M:%S")

    active_users = users[users["estado_usuario"] == "activo"]
    records: list[dict[str, Any]] = []
    event_idx = 1
    total_logs = 1800

    for i in range(total_logs):
        if i % 400 == 0 and i > 0:
            p = 85 + (i / total_logs) * 5
            print(f"[PROGRESS] {int(p)}", flush=True)

        user = active_users.sample(1, random_state=RANDOM_SEED + event_idx).iloc[0]
        role = user["rol"]
        allowed = list(ROLE_ALLOWED_ACTIONS[role])
        action = np.random.choice(allowed)
        table = tables.sample(1, random_state=RANDOM_SEED + (event_idx * 3)).iloc[0]
        requires_approval = int(action in {"modificar_resultado", "aprobar_correccion"})
        before_hash = hash_value(f"before-{event_idx}-{user['usuario_id']}")[:16]
        after_hash = before_hash if action != "modificar_resultado" else hash_value(f"after-{event_idx}-{user['usuario_id']}")[:16]

        records.append(
            {
                "evento_id": f"EVT-{event_idx:07d}",
                "timestamp": build_timestamp(base_dt, 0, 800),
                "usuario_id": user["usuario_id"],
                "rol_usuario": role,
                "accion": action,
                "recurso": "sistema_electoral",
                "mesa_id": table["mesa_id"],
                "zona_id": table["zona_id"],
                "resultado_accion": np.random.choice(["exito", "fallido"], p=[0.92, 0.08]),
                "ip_origen": random_ip(),
                "requiere_aprobacion": requires_approval,
                "aprobado_por": "" if requires_approval == 0 else np.random.choice(users["usuario_id"]),
                "hash_antes": before_hash,
                "hash_despues": after_hash,
            }
        )
        event_idx += 1

    logs = pd.DataFrame(records)

    # LOG-01: modification after close without approval
    idxs = np.random.choice(logs.index, size=20, replace=False)
    for idx in idxs:
        logs.at[idx, "accion"] = "modificar_resultado"
        logs.at[idx, "timestamp"] = (close_dt + timedelta(minutes=int(np.random.randint(1, 300)))).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        logs.at[idx, "requiere_aprobacion"] = 1
        logs.at[idx, "aprobado_por"] = ""
        make_alert(
            expected_alerts,
            "LOG-01",
            "evento_id",
            logs.at[idx, "evento_id"],
            "06_logs_eventos.csv",
            "Modificación posterior al cierre sin aprobación.",
        )

    # LOG-02: disallowed action by role
    disallowed_idxs = np.random.choice(logs.index, size=35, replace=False)
    for idx in disallowed_idxs:
        role = logs.at[idx, "rol_usuario"]
        disallowed = [a for a in ALLOWED_ACTIONS if a not in ROLE_ALLOWED_ACTIONS[role]]
        if not disallowed:
            continue
        logs.at[idx, "accion"] = np.random.choice(disallowed)
        make_alert(
            expected_alerts,
            "LOG-02",
            "evento_id",
            logs.at[idx, "evento_id"],
            "06_logs_eventos.csv",
            "Acción ejecutada no permitida por el rol.",
        )

    # LOG-03: inactive/suspended user activity
    inactive_users = users[users["estado_usuario"].isin(["inactivo", "suspendido"])]
    for _, user in inactive_users.sample(n=min(25, len(inactive_users)), random_state=RANDOM_SEED).iterrows():
        table = tables.sample(1, random_state=RANDOM_SEED + event_idx).iloc[0]
        records = {
            "evento_id": f"EVT-{event_idx:07d}",
            "timestamp": build_timestamp(base_dt, 100, 900),
            "usuario_id": user["usuario_id"],
            "rol_usuario": user["rol"],
            "accion": "consultar_alertas",
            "recurso": "sistema_electoral",
            "mesa_id": table["mesa_id"],
            "zona_id": table["zona_id"],
            "resultado_accion": "exito",
            "ip_origen": random_ip(),
            "requiere_aprobacion": 0,
            "aprobado_por": "",
            "hash_antes": hash_value(f"inactive-before-{event_idx}")[:16],
            "hash_despues": hash_value(f"inactive-after-{event_idx}")[:16],
        }
        logs = pd.concat([logs, pd.DataFrame([records])], ignore_index=True)
        make_alert(
            expected_alerts,
            "LOG-03",
            "usuario_id",
            user["usuario_id"],
            "06_logs_eventos.csv",
            "Usuario no activo ejecuta acción en el sistema.",
        )
        event_idx += 1

    # LOG-04: repeated failed login attempts
    target_user = users.sample(1, random_state=RANDOM_SEED + 999).iloc[0]
    failed_rows = []
    for i in range(8):
        failed_rows.append(
            {
                "evento_id": f"EVT-{event_idx:07d}",
                "timestamp": build_timestamp(base_dt, 20 + i, 40 + i),
                "usuario_id": target_user["usuario_id"],
                "rol_usuario": target_user["rol"],
                "accion": "login",
                "recurso": "auth",
                "mesa_id": "",
                "zona_id": "",
                "resultado_accion": "fallido",
                "ip_origen": random_ip(),
                "requiere_aprobacion": 0,
                "aprobado_por": "",
                "hash_antes": hash_value(f"failed-{event_idx}")[:16],
                "hash_despues": hash_value(f"failed-{event_idx}")[:16],
            }
        )
        event_idx += 1
    logs = pd.concat([logs, pd.DataFrame(failed_rows)], ignore_index=True)
    make_alert(
        expected_alerts,
        "LOG-04",
        "usuario_id",
        target_user["usuario_id"],
        "06_logs_eventos.csv",
        "Múltiples intentos fallidos de acceso.",
    )

    # LOG-05: hash modified without authorization
    hash_idxs = np.random.choice(logs.index, size=20, replace=False)
    for idx in hash_idxs:
        logs.at[idx, "accion"] = "modificar_resultado"
        logs.at[idx, "requiere_aprobacion"] = 0
        logs.at[idx, "hash_despues"] = hash_value(f"tampered-{idx}")[:16]
        if logs.at[idx, "hash_antes"] == logs.at[idx, "hash_despues"]:
            logs.at[idx, "hash_despues"] = hash_value(f"tampered-2-{idx}")[:16]
        make_alert(
            expected_alerts,
            "LOG-05",
            "evento_id",
            logs.at[idx, "evento_id"],
            "06_logs_eventos.csv",
            "Hash modificado en evento no autorizado.",
        )

    # LOG-06: self-approval
    self_approve_idxs = np.random.choice(logs.index, size=15, replace=False)
    for idx in self_approve_idxs:
        logs.at[idx, "accion"] = "aprobar_correccion"
        logs.at[idx, "requiere_aprobacion"] = 1
        logs.at[idx, "aprobado_por"] = logs.at[idx, "usuario_id"]
        make_alert(
            expected_alerts,
            "LOG-06",
            "evento_id",
            logs.at[idx, "evento_id"],
            "06_logs_eventos.csv",
            "Usuario aprueba su propio cambio.",
        )

    return logs.sort_values("evento_id").reset_index(drop=True)


def create_file_integrity(
    tables: pd.DataFrame,
    users: pd.DataFrame,
    expected_alerts: list[dict[str, Any]],
) -> pd.DataFrame:
    close_dt = datetime.strptime(f"{ELECTION_DATE} {ELECTION_CLOSE_TIME}", "%Y-%m-%d %H:%M:%S")

    publishers = users.loc[
        users["rol"].isin(["ADMIN_ELECTORAL", "SUPERVISOR_ESCRUTINIO", "AUDITOR"]) & (users["estado_usuario"] == "activo"),
        "usuario_id",
    ].tolist()
    if not publishers:
        publishers = users["usuario_id"].tolist()

    records: list[dict[str, Any]] = []
    for idx in range(1, NUM_TABLES * 2 + 1):
        table = tables.sample(1, random_state=RANDOM_SEED + idx).iloc[0]
        file_type = np.random.choice(["acta", "resultado_mesa", "snapshot_publicacion", "log_exportado"])
        original = hash_value(f"file-orig-{idx}")[:20]
        current = original
        sign_dt = close_dt + timedelta(minutes=int(np.random.randint(10, 180)))
        pub_dt = sign_dt + timedelta(minutes=int(np.random.randint(5, 120)))
        signed_total = int(np.random.randint(50, 450))
        pub_total = signed_total
        records.append(
            {
                "archivo_id": f"ARC-{idx:06d}",
                "tipo_archivo": file_type,
                "mesa_id": table["mesa_id"],
                "version": int(np.random.randint(1, 5)),
                "hash_original": original,
                "hash_actual": current,
                "timestamp_firma": sign_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_publicacion": pub_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "usuario_publicador": np.random.choice(publishers),
                "estado_integridad": "integro",
                "reporte_firmado_total": signed_total,
                "reporte_publicado_total": pub_total,
            }
        )

    integrity = pd.DataFrame(records)

    # INT-01
    int01_idx = np.random.choice(integrity.index, size=max(1, int(len(integrity) * 0.08)), replace=False)
    for idx in int01_idx:
        integrity.at[idx, "hash_actual"] = hash_value(f"mutated-hash-{idx}")[:20]
        integrity.at[idx, "estado_integridad"] = "alterado"
        make_alert(
            expected_alerts,
            "INT-01",
            "archivo_id",
            integrity.at[idx, "archivo_id"],
            "07_integridad_archivos.csv",
            "Hash actual distinto al hash original.",
        )

    # INT-02
    int02_idx = np.random.choice(integrity.index, size=max(1, int(len(integrity) * 0.06)), replace=False)
    for idx in int02_idx:
        integrity.at[idx, "reporte_publicado_total"] = int(integrity.at[idx, "reporte_firmado_total"]) + int(
            np.random.randint(1, 9)
        )
        make_alert(
            expected_alerts,
            "INT-02",
            "archivo_id",
            integrity.at[idx, "archivo_id"],
            "07_integridad_archivos.csv",
            "Total publicado diferente al total firmado.",
        )

    # INT-03
    int03_idx = np.random.choice(integrity.index, size=max(1, int(len(integrity) * 0.05)), replace=False)
    for idx in int03_idx:
        sign_dt = datetime.strptime(integrity.at[idx, "timestamp_firma"], "%Y-%m-%d %H:%M:%S")
        pub_dt = sign_dt - timedelta(minutes=int(np.random.randint(1, 60)))
        integrity.at[idx, "timestamp_publicacion"] = pub_dt.strftime("%Y-%m-%d %H:%M:%S")
        make_alert(
            expected_alerts,
            "INT-03",
            "archivo_id",
            integrity.at[idx, "archivo_id"],
            "07_integridad_archivos.csv",
            "Archivo publicado antes de la firma.",
        )

    # INT-04
    int04_idx = np.random.choice(integrity.index, size=max(1, int(len(integrity) * 0.05)), replace=False)
    for idx in int04_idx:
        integrity.at[idx, "estado_integridad"] = "alterado"
        integrity.at[idx, "timestamp_publicacion"] = (
            close_dt + timedelta(minutes=int(np.random.randint(180, 520)))
        ).strftime("%Y-%m-%d %H:%M:%S")
        integrity.at[idx, "hash_actual"] = hash_value(f"late-alter-{idx}")[:20]
        make_alert(
            expected_alerts,
            "INT-04",
            "archivo_id",
            integrity.at[idx, "archivo_id"],
            "07_integridad_archivos.csv",
            "Archivo alterado después del cierre electoral.",
        )

    return integrity


def save_datasets(datasets: dict[str, pd.DataFrame]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, dataset in datasets.items():
        dataset.to_csv(OUTPUT_DIR / name, index=False)


def main() -> None:
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    Faker.seed(RANDOM_SEED)
    fake = Faker("es_ES")

    expected_alerts: list[dict[str, Any]] = []

    print("[PROGRESS] 0", flush=True)
    print("[LABEL] Generando geografía electoral", flush=True)
    _, _, _, tables = create_geography()
    
    print("[PROGRESS] 10", flush=True)
    print("[LABEL] Creando usuarios del sistema", flush=True)
    users = create_users(fake, tables)
    
    print("[PROGRESS] 20", flush=True)
    print("[LABEL] Generando padrón de votantes", flush=True)
    voters = inject_padron_anomalies(create_voters(tables), expected_alerts)
    
    print("[PROGRESS] 35", flush=True)
    print("[LABEL] Asignando mesas y puestos", flush=True)
    assignments = create_assignments(voters, tables, expected_alerts)
    
    print("[PROGRESS] 45", flush=True)
    print("[LABEL] Registrando votos (sufragio)", flush=True)
    suffrage = create_suffrage(voters, assignments, users, expected_alerts)
    
    print("[PROGRESS] 60", flush=True)
    print("[LABEL] Realizando escrutinio manual", flush=True)
    manual = create_manual_count(suffrage, users, expected_alerts)
    
    print("[PROGRESS] 75", flush=True)
    print("[LABEL] Consolidando resultados por mesa", flush=True)
    results = create_results(manual, assignments, voters, expected_alerts)
    
    print("[PROGRESS] 85", flush=True)
    print("[LABEL] Generando logs de auditoría", flush=True)
    logs = create_logs(users, tables, expected_alerts)
    
    print("[PROGRESS] 92", flush=True)
    print("[LABEL] Verificando integridad de archivos", flush=True)
    integrity = create_file_integrity(tables, users, expected_alerts)
    
    print("[PROGRESS] 95", flush=True)
    print("[LABEL] Guardando datasets finales", flush=True)

    expected_alerts_df = pd.DataFrame(expected_alerts)

    datasets = {
        "01_padron_votantes.csv": voters,
        "02_asignacion_mesas.csv": assignments,
        "03_registro_sufragio.csv": suffrage,
        "04_clasificacion_votos_manual.csv": manual,
        "05_resultados_mesa.csv": results,
        "06_logs_eventos.csv": logs,
        "07_integridad_archivos.csv": integrity,
        "08_alertas_esperadas.csv": expected_alerts_df,
        "usuarios_sistema.csv": users,
    }

    save_datasets(datasets)
    print("[PROGRESS] 100", flush=True)
    print("[LABEL] ¡Generación completada!", flush=True)

    print("Datasets generados correctamente.")
    print(f"Total votantes: {len(voters)}")
    print(f"Total mesas: {NUM_TABLES}")
    print(f"Total usuarios: {len(users)}")
    print(f"Total alertas esperadas: {len(expected_alerts_df)}")
    print(f"Ubicación: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
