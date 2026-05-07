"""Streamlit UI for Electoral Integrity Analyzer."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config.rules_config import ETHICAL_WARNING
from src.data_loader.csv_loader import DatasetLoadError, load_datasets
from src.data_loader.validators import validate_datasets
from src.detectors.factory import build_default_detectors
from src.pipeline.analysis_pipeline import AnalysisPipeline
from src.reports.report_generator import export_reports
from src.visualizations.charts import build_required_charts

st.set_page_config(page_title="Electoral Integrity Analyzer", layout="wide")

MENU_OPTIONS = [
    "Inicio",
    "Cargar / generar datasets",
    "Padrón y elegibilidad",
    "Circunscripción y mesa",
    "Registro de sufragio",
    "Escrutinio manual",
    "Resultados por mesa",
    "Logs e integridad",
    "Reporte consolidado",
]

STAGE_CONFIG: dict[str, dict] = {
    "Padrón y elegibilidad": {
        "prefix": "PAD",
        "datasets": ["01_padron_votantes.csv", "03_registro_sufragio.csv"],
    },
    "Circunscripción y mesa": {
        "prefix": "CIR",
        "datasets": ["02_asignacion_mesas.csv", "03_registro_sufragio.csv"],
    },
    "Registro de sufragio": {
        "prefix": "SUF",
        "datasets": [
            "01_padron_votantes.csv",
            "02_asignacion_mesas.csv",
            "03_registro_sufragio.csv",
            "usuarios_sistema.csv",
        ],
    },
    "Escrutinio manual": {
        "prefix": "MAN",
        "datasets": ["04_clasificacion_votos_manual.csv", "usuarios_sistema.csv"],
    },
    "Resultados por mesa": {
        "prefix": "RES",
        "datasets": ["05_resultados_mesa.csv"],
    },
    "Logs e integridad": {
        "prefix": "LOG/INT",
        "datasets": ["06_logs_eventos.csv", "07_integridad_archivos.csv", "usuarios_sistema.csv"],
    },
}

_EXPECTED_DATASETS = [
    "01_padron_votantes.csv",
    "02_asignacion_mesas.csv",
    "03_registro_sufragio.csv",
    "04_clasificacion_votos_manual.csv",
    "05_resultados_mesa.csv",
    "06_logs_eventos.csv",
    "07_integridad_archivos.csv",
    "08_alertas_esperadas.csv",
    "usuarios_sistema.csv",
]


@st.cache_data(show_spinner=False)
def dataset_status_table(base_path: str = "data/synthetic") -> pd.DataFrame:
    path = Path(base_path)
    rows = []
    for name in _EXPECTED_DATASETS:
        exists = (path / name).exists()
        rows.append(
            {
                "dataset": name,
                "estado": "Generado" if exists else "Pendiente",
                "ruta": str(path / name),
            }
        )
    return pd.DataFrame(rows)


def init_state() -> None:
    defaults = {
        "datasets": None,
        "validation": None,
        "analysis": None,
        "export_paths": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def run_generation_script() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["python", "scripts/generate_synthetic_data.py"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return False, proc.stderr.strip() or "Falló la generación de datasets"
        return True, proc.stdout.strip()
    except Exception:
        return False, "No fue posible ejecutar el script de generación en este entorno."


def run_analysis(datasets: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    detectors = build_default_detectors()
    pipeline = AnalysisPipeline(detectors)
    return pipeline.run(datasets)


def safe_load_and_validate() -> None:
    try:
        datasets = load_datasets()
        validation = validate_datasets(datasets)
        st.session_state.datasets = datasets
        st.session_state.validation = validation

        if validation["errors"]:
            st.warning("Errores de validación encontrados. Revise el detalle en esta sección.")
        else:
            st.success("Datasets cargados y validados correctamente.")

    except DatasetLoadError as exc:
        st.warning(str(exc))
    except Exception:
        st.warning("Ocurrió un problema al cargar o validar datasets.")


def render_ethical_warning() -> None:
    st.warning(ETHICAL_WARNING)


def _require_analysis() -> bool:
    """Returns True when analysis results are available; otherwise shows guidance and returns False."""
    if st.session_state.analysis:
        return True
    st.info(
        "Para ver esta sección primero genere o cargue los datasets y ejecute el análisis "
        "completo desde **Cargar / generar datasets**."
    )
    return False


def _filter_alerts(alerts: pd.DataFrame) -> pd.DataFrame:
    col1, col2 = st.columns(2)
    with col1:
        stage_filter = st.selectbox(
            "Etapa", ["Todos"] + sorted(alerts["etapa"].dropna().unique().tolist())
        )
        severity_filter = st.selectbox(
            "Severidad", ["Todos"] + sorted(alerts["severidad"].dropna().unique().tolist())
        )
    with col2:
        code_filter = st.selectbox(
            "Código", ["Todos"] + sorted(alerts["codigo_alerta"].dropna().unique().tolist())
        )
        entity_type_filter = st.selectbox(
            "Tipo de entidad", ["Todos"] + sorted(alerts["entidad_tipo"].dropna().unique().tolist())
        )

    entity_id_text = st.text_input("Buscar por entidad_id (contiene)")

    filtered = alerts.copy()
    if stage_filter != "Todos":
        filtered = filtered[filtered["etapa"] == stage_filter]
    if severity_filter != "Todos":
        filtered = filtered[filtered["severidad"] == severity_filter]
    if code_filter != "Todos":
        filtered = filtered[filtered["codigo_alerta"] == code_filter]
    if entity_type_filter != "Todos":
        filtered = filtered[filtered["entidad_tipo"] == entity_type_filter]
    if entity_id_text:
        filtered = filtered[
            filtered["entidad_id"].astype(str).str.contains(entity_id_text, case=False, na=False)
        ]
    return filtered


def render_metrics() -> None:
    datasets = st.session_state.datasets
    analysis = st.session_state.analysis
    validation = st.session_state.validation

    datasets_loaded = len(datasets) if datasets else 0
    records_analyzed = (
        sum(len(df) for name, df in datasets.items() if name != "08_alertas_esperadas.csv")
        if datasets
        else 0
    )
    alerts_detected = len(analysis["alerts"]) if analysis else 0
    critical_alerts = (
        int((analysis["alerts"]["severidad"] == "critica").sum())
        if analysis and not analysis["alerts"].empty
        else 0
    )
    overall_score = (
        int(analysis["ranking"]["score_total"].sum())
        if analysis and not analysis["ranking"].empty
        else 0
    )
    validation_state = "Exitosa" if validation and not validation["errors"] else "Pendiente"

    cols = st.columns(6)
    cols[0].metric("Datasets cargados", datasets_loaded)
    cols[1].metric("Registros analizados", records_analyzed)
    cols[2].metric("Alertas detectadas", alerts_detected)
    cols[3].metric("Alertas críticas", critical_alerts)
    cols[4].metric("Score general", overall_score)
    cols[5].metric("Validación", validation_state)


def render_stage_alerts(stage_name: str) -> None:
    if not _require_analysis():
        return

    analysis = st.session_state.analysis
    alerts = analysis["alerts"]
    stage_alerts = alerts[alerts["etapa"] == stage_name].copy()
    cfg = STAGE_CONFIG.get(stage_name, {})

    st.subheader(stage_name)
    st.caption(
        f"Datasets: {', '.join(cfg.get('datasets', []))}  |  Códigos: {cfg.get('prefix', 'N/A')}"
    )

    cols = st.columns(3)
    cols[0].metric("Alertas en etapa", len(stage_alerts))
    cols[1].metric("Críticas", int((stage_alerts["severidad"] == "critica").sum()))
    cols[2].metric("Entidades afectadas", stage_alerts["entidad_id"].nunique())

    tabs = st.tabs(["Resumen", "Tabla de alertas", "Evidencia y acciones"])

    with tabs[0]:
        if stage_alerts.empty:
            st.success("Sin alertas detectadas en esta etapa.")
        else:
            severity_counts = stage_alerts["severidad"].value_counts().reset_index()
            severity_counts.columns = ["severidad", "total"]
            st.dataframe(severity_counts, use_container_width=True)
            st.info("Las alertas son señales para revisión; no constituyen prueba de fraude.")

    with tabs[1]:
        if stage_alerts.empty:
            st.success("No hay registros de alerta para esta etapa.")
        else:
            st.dataframe(stage_alerts, use_container_width=True)

    with tabs[2]:
        if stage_alerts.empty:
            st.success("Sin evidencia que mostrar para esta etapa.")
        else:
            evidence_cols = ["codigo_alerta", "entidad_id", "descripcion", "evidencia", "accion_recomendada"]
            present = [c for c in evidence_cols if c in stage_alerts.columns]
            st.dataframe(stage_alerts[present], use_container_width=True)


def render_home() -> None:
    st.title("Electoral Integrity Analyzer")
    st.subheader("Analizador de Integridad Electoral por Etapas")
    render_ethical_warning()
    st.write(
        "Detecta anomalías en datasets electorales sintéticos por etapa "
        "mediante reglas determinísticas y Z-score."
    )

    render_metrics()

    st.markdown("### Estado de datasets")
    st.dataframe(dataset_status_table(), use_container_width=True)

    if not st.session_state.datasets:
        st.info("Vaya a **Cargar / generar datasets** para preparar y analizar los datos.")


def render_data_management() -> None:
    st.title("Cargar / generar datasets")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generar datasets sintéticos", type="primary"):
            ok, message = run_generation_script()
            dataset_status_table.clear()
            if ok:
                st.success("Datasets generados correctamente.")
                if message:
                    st.code(message)
                safe_load_and_validate()
            else:
                st.warning("No se pudieron generar datasets con el script.")
                st.code(message)

    with col2:
        if st.button("Cargar datasets existentes"):
            safe_load_and_validate()

    st.dataframe(dataset_status_table(), use_container_width=True)

    if st.session_state.datasets:
        st.success("Datasets disponibles en sesión.")

        preview_name = st.selectbox("Vista previa de dataset", list(st.session_state.datasets.keys()))
        st.dataframe(st.session_state.datasets[preview_name].head(20), use_container_width=True)

        validation = st.session_state.validation or {"errors": []}
        if validation["errors"]:
            st.warning("Errores de validación:")
            for err in validation["errors"]:
                st.write(f"- {err}")
        else:
            st.success("Validación exitosa.")

        if st.button("Ejecutar análisis completo", type="primary"):
            if validation["errors"]:
                st.warning("Corrija primero los errores de validación.")
            else:
                try:
                    with st.spinner("Ejecutando análisis..."):
                        analysis = run_analysis(st.session_state.datasets)
                        st.session_state.analysis = analysis
                        export_paths = export_reports(
                            analysis["alerts"], analysis["ranking"], analysis["summary"]
                        )
                        st.session_state.export_paths = export_paths
                    st.success("Análisis ejecutado y reportes exportados correctamente.")
                except Exception:
                    st.warning("No fue posible ejecutar el análisis completo.")


def render_results_stage() -> None:
    render_stage_alerts("Resultados por mesa")

    analysis = st.session_state.analysis
    if not analysis:
        return

    datasets = st.session_state.datasets
    results = datasets.get("05_resultados_mesa.csv", pd.DataFrame()) if datasets else pd.DataFrame()
    charts = build_required_charts(analysis["alerts"], results, analysis["ranking"])

    with st.expander("Visualizaciones de esta etapa", expanded=True):
        st.plotly_chart(charts["histograma_participacion"], use_container_width=True)
        st.caption("Permite identificar mesas con participación inusualmente alta o baja.")
        st.plotly_chart(charts["boxplot_nulos_invalidos"], use_container_width=True)
        st.caption("Resalta mesas con tasas atípicas de nulos/inválidos.")


def render_consolidated_report() -> None:
    st.title("Reporte consolidado")
    render_ethical_warning()

    if not _require_analysis():
        return

    analysis = st.session_state.analysis
    datasets = st.session_state.datasets
    alerts = analysis["alerts"].copy()
    ranking = analysis["ranking"].copy()
    summary = analysis["summary"].copy()

    tab_summary, tab_table, tab_charts, tab_method = st.tabs(
        ["Resumen", "Tabla y filtros", "Visualizaciones", "Metodología"]
    )

    with tab_summary:
        st.dataframe(summary, use_container_width=True)
        render_metrics()

    with tab_table:
        filtered = _filter_alerts(alerts)
        st.dataframe(filtered, use_container_width=True)

        st.markdown("### Ranking de riesgo")
        st.dataframe(ranking, use_container_width=True)

        export_paths = st.session_state.export_paths
        if export_paths:
            st.success("Archivos exportados.")
            for key, path in export_paths.items():
                with open(path, "rb") as f:
                    st.download_button(
                        label=f"Descargar {path.name}",
                        data=f.read(),
                        file_name=path.name,
                        mime="text/csv",
                        key=f"download_{key}",
                    )

    with tab_charts:
        results = datasets.get("05_resultados_mesa.csv", pd.DataFrame()) if datasets else pd.DataFrame()
        charts = build_required_charts(alerts, results, ranking)

        st.plotly_chart(charts["alertas_por_etapa"], use_container_width=True)
        st.caption("Muestra en qué etapas se concentra el riesgo detectado.")

        st.plotly_chart(charts["alertas_por_severidad"], use_container_width=True)
        st.caption("Permite priorizar revisión por criticidad.")

        st.plotly_chart(charts["histograma_participacion"], use_container_width=True)
        st.caption("Identifica mesas con participación atípica.")

        st.plotly_chart(charts["boxplot_nulos_invalidos"], use_container_width=True)
        st.caption("Señala dispersión de nulos e inválidos entre mesas.")

        st.plotly_chart(charts["ranking_riesgo_mesas"], use_container_width=True)
        st.caption("Prioriza las 10 mesas con mayor score de riesgo.")

    with tab_method:
        st.info(
            "**Z-score**: indica qué tan lejos está un valor del promedio. "
            "Se marca como atípico cuando |Z-score| ≥ 3."
        )
        st.info(
            "**Hash**: resumen digital para verificar integridad de archivos. "
            "Una discrepancia entre hash original y actual genera alerta."
        )
        st.write("Este sistema genera señales de revisión; no demuestra fraude electoral por sí solo.")


def _nav_label(name: str) -> str:
    """Decorates sidebar labels with a checkmark once analysis results are available."""
    if name in ("Inicio", "Cargar / generar datasets"):
        return name
    if st.session_state.get("analysis"):
        return f"✓ {name}"
    return name


def main() -> None:
    init_state()

    pages = {
        "Inicio": render_home,
        "Cargar / generar datasets": render_data_management,
        "Padrón y elegibilidad": lambda: render_stage_alerts("Padrón y elegibilidad"),
        "Circunscripción y mesa": lambda: render_stage_alerts("Circunscripción y mesa"),
        "Registro de sufragio": lambda: render_stage_alerts("Registro de sufragio"),
        "Escrutinio manual": lambda: render_stage_alerts("Escrutinio manual"),
        "Resultados por mesa": render_results_stage,
        "Logs e integridad": lambda: render_stage_alerts("Logs e integridad"),
        "Reporte consolidado": render_consolidated_report,
    }

    st.sidebar.title("Navegación")
    selected = st.sidebar.radio("Seleccione una etapa", MENU_OPTIONS, format_func=_nav_label)
    pages[selected]()


if __name__ == "__main__":
    main()
