"""Validation layer for synthetic electoral datasets."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from src.domain.schemas import ALLOWED_VALUES, DATASET_ORDER, DATASET_SCHEMAS, ID_COLUMNS, NUMERIC_COLUMNS

DATE_COLUMNS: dict[str, list[str]] = {
    "01_padron_votantes.csv": ["fecha_nacimiento", "fecha_defuncion"],
    "03_registro_sufragio.csv": ["fecha_eleccion", "hora_checkin"],
    "06_logs_eventos.csv": ["timestamp"],
    "07_integridad_archivos.csv": ["timestamp_firma", "timestamp_publicacion"],
}

REFERENTIAL_RULES = [
    ("03_registro_sufragio.csv", "voter_id", "01_padron_votantes.csv", "voter_id"),
    ("02_asignacion_mesas.csv", "voter_id", "01_padron_votantes.csv", "voter_id"),
    ("04_clasificacion_votos_manual.csv", "voter_id", "01_padron_votantes.csv", "voter_id"),
    ("05_resultados_mesa.csv", "mesa_id", "02_asignacion_mesas.csv", "mesa_asignada"),
    ("06_logs_eventos.csv", "usuario_id", "usuarios_sistema.csv", "usuario_id"),
    ("07_integridad_archivos.csv", "usuario_publicador", "usuarios_sistema.csv", "usuario_id"),
]


def _validate_existence(base_path: Path) -> list[str]:
    errors: list[str] = []
    for name in DATASET_ORDER:
        if not (base_path / name).exists():
            errors.append(f"Falta el archivo {name}.")
    return errors


def _validate_columns(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    for name, expected_columns in DATASET_SCHEMAS.items():
        if name not in datasets:
            continue
        df = datasets[name]
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"{name}: columnas faltantes {missing_columns}")
    return errors


def _validate_non_null_ids(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    for name, id_col in ID_COLUMNS.items():
        if name not in datasets or id_col not in datasets[name].columns:
            continue
        df = datasets[name]
        null_count = int(df[id_col].isna().sum())
        empty_count = int((df[id_col].astype(str).str.strip() == "").sum())
        if null_count > 0 or empty_count > 0:
            errors.append(f"{name}: {id_col} tiene valores nulos o vacíos")
    return errors


def _is_valid_date(value: str, fmt: str) -> bool:
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def _validate_dates(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    for name, columns in DATE_COLUMNS.items():
        if name not in datasets:
            continue
        df = datasets[name]
        for col in columns:
            if col not in df.columns:
                continue

            series = df[col].fillna("").astype(str).str.strip()
            if col == "fecha_defuncion":
                series = series[series != ""]

            if col in {"fecha_nacimiento", "fecha_eleccion", "fecha_defuncion"}:
                mask = series.apply(lambda x: _is_valid_date(x, "%Y-%m-%d"))
            elif col == "hora_checkin":
                mask = series.apply(lambda x: _is_valid_date(x, "%H:%M:%S"))
            else:
                mask = series.apply(lambda x: _is_valid_date(x, "%Y-%m-%d %H:%M:%S"))

            if not mask.all():
                errors.append(f"{name}: columna {col} tiene fechas/horas inválidas")
    return errors


def _validate_categories(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    for column, allowed in ALLOWED_VALUES.items():
        for name, df in datasets.items():
            if column not in df.columns:
                continue
            values = set(df[column].dropna().astype(str).str.strip().unique().tolist())
            invalid = sorted(values - allowed)
            if invalid:
                errors.append(f"{name}: columna {column} contiene valores no permitidos {invalid[:5]}")
    return errors


def _validate_referential(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    for src_file, src_col, ref_file, ref_col in REFERENTIAL_RULES:
        if src_file not in datasets or ref_file not in datasets:
            continue
        src_df = datasets[src_file]
        ref_df = datasets[ref_file]
        if src_col not in src_df.columns or ref_col not in ref_df.columns:
            continue

        src_vals = set(src_df[src_col].dropna().astype(str))
        ref_vals = set(ref_df[ref_col].dropna().astype(str))
        missing = src_vals - ref_vals
        if missing:
            errors.append(
                f"Llave referencial inválida: {src_file}.{src_col} tiene {len(missing)} valores sin match en {ref_file}.{ref_col}"
            )
    return errors


def _validate_numeric_types(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    for name, numeric_cols in NUMERIC_COLUMNS.items():
        if name not in datasets:
            continue
        df = datasets[name]
        for col in numeric_cols:
            if col not in df.columns:
                continue
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.isna().any():
                errors.append(f"{name}: columna {col} contiene valores no numéricos")
    return errors


def _validate_percentages(datasets: dict[str, pd.DataFrame]) -> list[str]:
    errors: list[str] = []
    results_name = "05_resultados_mesa.csv"
    if results_name not in datasets:
        return errors

    df = datasets[results_name]
    required = {"total_reportado", "votos_nulos", "votos_invalidos", "participacion_pct", "electores_habilitados", "sufragantes_registrados"}
    if not required.issubset(df.columns):
        return errors

    if (df["electores_habilitados"] < 0).any() or (df["sufragantes_registrados"] < 0).any():
        errors.append(f"{results_name}: hay conteos negativos en electores o sufragantes")

    nonzero = df["total_reportado"].replace(0, pd.NA)
    nulos_pct = (df["votos_nulos"] / nonzero).fillna(0)
    invalidos_pct = (df["votos_invalidos"] / nonzero).fillna(0)

    if ((nulos_pct < 0) | (nulos_pct > 1.2)).any():
        errors.append(f"{results_name}: porcentaje de votos nulos fuera de rango razonable")
    if ((invalidos_pct < 0) | (invalidos_pct > 1.2)).any():
        errors.append(f"{results_name}: porcentaje de votos inválidos fuera de rango razonable")

    if (df["participacion_pct"] < 0).any():
        errors.append(f"{results_name}: participación negativa no permitida")

    return errors


def validate_datasets(datasets: dict[str, pd.DataFrame], base_path: str | Path = "data/synthetic") -> dict[str, list[str]]:
    """Run full validation suite and return structured errors/warnings."""
    path = Path(base_path)
    errors: list[str] = []

    errors.extend(_validate_existence(path))
    errors.extend(_validate_columns(datasets))
    errors.extend(_validate_non_null_ids(datasets))
    errors.extend(_validate_dates(datasets))
    errors.extend(_validate_categories(datasets))
    errors.extend(_validate_referential(datasets))
    errors.extend(_validate_numeric_types(datasets))
    errors.extend(_validate_percentages(datasets))

    return {
        "errors": errors,
        "warnings": [],
    }
