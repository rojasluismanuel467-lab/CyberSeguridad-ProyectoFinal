"""
Transform a public electoral results CSV into the 05_resultados_mesa.csv
format expected by the Electoral Integrity Analyzer.

Only this dataset is replaced — the other 8 remain synthetic, since they
contain individual or system data that is not publicly available.

Usage
-----
    python scripts/adapt_real_results.py --input <path_to_source.csv>

Supported sources (set via --source flag, default: registraduria):
    registraduria   Colombia — Registraduría Nacional del Estado Civil
                    preconteo / E-14 format
    generic         Any CSV — configure GENERIC_MAP below before running

Output
------
    data/synthetic/05_resultados_mesa.csv  (overwrites existing file)

After running, execute the full analysis from the app or via:
    streamlit run app.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "synthetic" / "05_resultados_mesa.csv"

# ---------------------------------------------------------------------------
# Column mappings — edit here if your source file uses different names
# ---------------------------------------------------------------------------

# Registraduría Nacional (Colombia) — preconteo / E-14 CSV export
REGISTRADURIA_MAP = {
    # source column          -> target column
    "MUNICIPIO":               "municipio",
    "NUMERO_MESA":             "mesa_id",          # or MESA, NUMERO_MESA
    "PUESTO_VOTACION":         "zona_id",           # used as zone proxy
    "DEPARTAMENTO":            "circunscripcion",
    "POTENCIAL_VOTANTES":      "electores_habilitados",
    "TOTAL_SUFRAGIOS":         "sufragantes_registrados",  # or TOTAL_VOTOS
    "CANDIDATO_1":             "votos_candidato_A",  # rename to actual candidate column
    "CANDIDATO_2":             "votos_candidato_B",
    "CANDIDATO_3":             "votos_candidato_C",
    "VOTOS_EN_BLANCO":         "votos_blancos",
    "VOTOS_NULOS":             "votos_nulos",
    "TARJETAS_NO_MARCADAS":    "votos_invalidos",   # or VOTOS_NO_MARCADOS
}

# Generic mapping — configure this when --source generic is used
GENERIC_MAP = {
    # "your_column_name":    "target_column",
    "id_mesa":               "mesa_id",
    "municipio":             "municipio",
    "zona":                  "zona_id",
    "departamento":          "circunscripcion",
    "habilitados":           "electores_habilitados",
    "sufragantes":           "sufragantes_registrados",
    "candidato_a":           "votos_candidato_A",
    "candidato_b":           "votos_candidato_B",
    "candidato_c":           "votos_candidato_C",
    "blancos":               "votos_blancos",
    "nulos":                 "votos_nulos",
    "invalidos":             "votos_invalidos",
}

SOURCES = {
    "registraduria": REGISTRADURIA_MAP,
    "generic": GENERIC_MAP,
}

# Columns that must exist in the output
REQUIRED_COLUMNS = [
    "mesa_id", "municipio", "zona_id", "circunscripcion",
    "electores_habilitados", "sufragantes_registrados",
    "votos_candidato_A", "votos_candidato_B", "votos_candidato_C",
    "votos_blancos", "votos_nulos", "votos_invalidos",
    "total_calculado", "total_reportado", "participacion_pct",
    "ganador", "concentracion_ganador_pct", "margen_victoria_pct",
]

VOTE_COLS = [
    "votos_candidato_A", "votos_candidato_B", "votos_candidato_C",
    "votos_blancos", "votos_nulos", "votos_invalidos",
]

CANDIDATE_COLS = ["votos_candidato_A", "votos_candidato_B", "votos_candidato_C"]


# ---------------------------------------------------------------------------
# Transformation helpers
# ---------------------------------------------------------------------------

def _apply_map(df: pd.DataFrame, col_map: dict[str, str]) -> pd.DataFrame:
    present = {src: tgt for src, tgt in col_map.items() if src in df.columns}
    missing = [src for src in col_map if src not in df.columns]
    if missing:
        print(f"  Advertencia: columnas no encontradas en la fuente: {missing}")
    return df.rename(columns=present)


def _fill_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Fill columns absent from the source with neutral defaults."""
    if "zona_id" not in df.columns:
        df["zona_id"] = "ZONA_UNICA"
    if "circunscripcion" not in df.columns:
        df["circunscripcion"] = df.get("municipio", "SIN_CIRCUNSCRIPCION")
    for col in VOTE_COLS:
        if col not in df.columns:
            df[col] = 0
    return df


def _compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    df[VOTE_COLS] = df[VOTE_COLS].apply(pd.to_numeric, errors="coerce").fillna(0)
    df["electores_habilitados"] = pd.to_numeric(df["electores_habilitados"], errors="coerce").fillna(0)
    df["sufragantes_registrados"] = pd.to_numeric(df["sufragantes_registrados"], errors="coerce").fillna(0)

    df["total_calculado"] = df[VOTE_COLS].sum(axis=1)
    df["total_reportado"] = df["sufragantes_registrados"]

    df["participacion_pct"] = (
        df["sufragantes_registrados"] / df["electores_habilitados"].replace(0, pd.NA)
    ).round(4)

    sorted_candidates = df[CANDIDATE_COLS].apply(lambda row: row.sort_values(ascending=False), axis=1)
    df["ganador"] = df[CANDIDATE_COLS].idxmax(axis=1).str.replace("votos_", "")
    df["concentracion_ganador_pct"] = (
        sorted_candidates.iloc[:, 0] / df["total_calculado"].replace(0, pd.NA)
    ).round(4)
    df["margen_victoria_pct"] = (
        (sorted_candidates.iloc[:, 0] - sorted_candidates.iloc[:, 1])
        / df["total_calculado"].replace(0, pd.NA)
    ).round(4)

    return df


def _normalize_mesa_id(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Ensure mesa_id is a unique string identifier."""
    if "mesa_id" not in df.columns:
        df = df.reset_index()
        df["mesa_id"] = df.index.astype(str).str.zfill(6)
        return df

    if source == "registraduria" and "municipio" in df.columns:
        # Build composite key: MUNICIPIO + MESA to guarantee uniqueness across municipalities
        df["mesa_id"] = (
            df["municipio"].astype(str).str.upper().str.replace(" ", "_")
            + "_M"
            + df["mesa_id"].astype(str).str.zfill(4)
        )
    else:
        df["mesa_id"] = df["mesa_id"].astype(str)

    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def adapt(input_path: Path, source: str) -> None:
    col_map = SOURCES[source]

    print(f"Leyendo: {input_path}")
    try:
        df = pd.read_csv(input_path, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(input_path, encoding="latin-1", low_memory=False)

    print(f"  Filas en fuente: {len(df):,}")
    print(f"  Columnas en fuente: {list(df.columns)}")

    df = _apply_map(df, col_map)
    df = _fill_missing_columns(df)
    df = _normalize_mesa_id(df, source)
    df = _compute_derived(df)

    # Keep only required columns in the correct order
    available = [c for c in REQUIRED_COLUMNS if c in df.columns]
    df = df[available].copy()

    missing_required = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_required:
        print(f"\nColumnas requeridas faltantes tras la adaptación: {missing_required}")
        print("Revise el mapeo de columnas en REGISTRADURIA_MAP o GENERIC_MAP.")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nGuardado en: {OUTPUT_PATH}")
    print(f"  Mesas adaptadas: {len(df):,}")
    print(f"  Participación promedio: {df['participacion_pct'].mean():.1%}")
    print(f"  Mesas con participación > 95%: {(df['participacion_pct'] > 0.95).sum()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Adapt real electoral results to analyzer format.")
    parser.add_argument("--input", required=True, help="Path to source CSV file")
    parser.add_argument(
        "--source",
        choices=list(SOURCES.keys()),
        default="registraduria",
        help="Source format (default: registraduria)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Archivo no encontrado: {input_path}")
        sys.exit(1)

    adapt(input_path, args.source)
    print("\nListo. Ejecute el análisis completo desde la app para ver los resultados.")


if __name__ == "__main__":
    main()
