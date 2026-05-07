"""Streamlit UI for Electoral Integrity Analyzer."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config.rules_config import ETHICAL_WARNING
from src.data_loader.csv_loader import DatasetLoadError, load_datasets
from src.data_loader.validators import validate_datasets
from src.detectors.circumscription_detector import CircumscriptionDetector
from src.detectors.eligibility_detector import EligibilityDetector
from src.detectors.log_integrity_detector import LogIntegrityDetector
from src.detectors.manual_count_detector import ManualCountDetector
from src.detectors.results_detector import ResultsDetector
from src.detectors.suffrage_detector import SuffrageDetector
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

STAGE_CODE_PREFIX = {
    "Padrón y elegibilidad": "PAD",
    "Circunscripción y mesa": "CIR",
    "Registro de sufragio": "SUF",
    "Escrutinio manual": "MAN",
    "Resultados por mesa": "RES",
    "Logs e integridad": "LOG/INT",
}

STAGE_DATASETS = {
    "Padrón y elegibilidad": ["01_padron_votantes.csv", "03_registro_sufragio.csv"],
    "Circunscripción y mesa": ["02_asignacion_mesas.csv", "03_registro_sufragio.csv"],
    "Registro de sufragio": [
        "01_padron_votantes.csv",
        "02_asignacion_mesas.csv",
        "03_registro_sufragio.csv",
        "usuarios_sistema.csv",
    ],
    "Escrutinio manual": ["04_clasificacion_votos_manual.csv", "usuarios_sistema.csv"],
    "Resultados por mesa": ["05_resultados_mesa.csv"],
    "Logs e integridad": ["06_logs_eventos.csv", "07_integridad_archivos.csv", "usuarios_sistema.csv"],
}


@st.cache_data(show_spinner=False)
def dataset_status_table(base_path: str = "data/synthetic") -> pd.DataFrame:
    expected = [
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
    path = Path(base_path)
    rows = []
    for name in expected:
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
    detectors = [
        EligibilityDetector(),
        CircumscriptionDetector(),
        SuffrageDetector(),
        ManualCountDetector(),
        ResultsDetector(),
        LogIntegrityDetector(),
    ]
    pipeline = AnalysisPipeline(detectors)
    return pipeline.run(datasets)


def safe_load_and_validate() -> None:
    try:
        datasets = load_datasets()
        validation = validate_datasets(datasets)
        st.session_state.datasets = datasets
        st.session_state.validation = validation

        if validation["errors"]:
            st.error("Errores de validación encontrados. Revise el detalle en esta sección.")
        else:
            st.success("Datasets cargados y validados correctamente.")

    except DatasetLoadError as exc:
        st.error(str(exc))
    except Exception:
        st.error("Ocurrió un problema al cargar o validar datasets.")


def render_ethical_warning() -> None:
    st.warning(ETHICAL_WARNING)
    st.info(
        "No se usan datos personales reales. No se analizan procesos electorales reales. "
        "No se atribuyen irregularidades a personas, partidos, países o instituciones reales."
    )


def render_metrics() -> None:
    datasets = st.session_state.datasets
    analysis = st.session_state.analysis
    validation = st.session_state.validation

    datasets_loaded = len(datasets) if datasets else 0
    records_analyzed = 0
    if datasets:
        records_analyzed = sum(len(df) for name, df in datasets.items() if name != "08_alertas_esperadas.csv")

    alerts_detected = len(analysis["alerts"]) if analysis else 0
    critical_alerts = int((analysis["alerts"]["severidad"] == "critica").sum()) if analysis and not analysis["alerts"].empty else 0
    overall_score = int(analysis["ranking"]["score_total"].sum()) if analysis and not analysis["ranking"].empty else 0
    validation_state = "Validación exitosa" if validation and not validation["errors"] else "Pendiente/Error"

    cols = st.columns(6)
    cols[0].metric("Datasets cargados", datasets_loaded)
    cols[1].metric("Registros analizados", records_analyzed)
    cols[2].metric("Alertas detectadas", alerts_detected)
    cols[3].metric("Alertas críticas", critical_alerts)
    cols[4].metric("Score general", overall_score)
    cols[5].metric("Estado validación", validation_state)


def render_stage_alerts(stage_name: str) -> None:
    analysis = st.session_state.analysis
    if not analysis or analysis["alerts"].empty:
        st.warning("Análisis no ejecutado o sin alertas detectadas.")
        return

    alerts = analysis["alerts"]
    stage_alerts = alerts[alerts["etapa"] == stage_name].copy()

    st.subheader(stage_name)
    st.write("Descripción: análisis de anomalías de la etapa seleccionada.")
    st.write(f"Datasets usados: {', '.join(STAGE_DATASETS.get(stage_name, []))}")
    st.write(f"Reglas aplicadas: códigos {STAGE_CODE_PREFIX.get(stage_name, 'N/A')}.")

    cols = st.columns(3)
    cols[0].metric("Alertas etapa", len(stage_alerts))
    cols[1].metric("Críticas", int((stage_alerts["severidad"] == "critica").sum()))
    cols[2].metric("Entidades afectadas", stage_alerts["entidad_id"].nunique())

    tabs = st.tabs(["Resumen", "Tabla de alertas", "Reglas y evidencia"])

    with tabs[0]:
        if stage_alerts.empty:
            st.info("Sin alertas para esta etapa.")
        else:
            severity_counts = stage_alerts["severidad"].value_counts().reset_index()
            severity_counts.columns = ["severidad", "total"]
            st.dataframe(severity_counts, use_container_width=True)
            st.info(
                "Las alertas son señales para revisión. No constituyen prueba de fraude por sí solas."
            )

    with tabs[1]:
        if stage_alerts.empty:
            st.info("No hay registros para mostrar.")
        else:
            st.dataframe(stage_alerts, use_container_width=True)

    with tabs[2]:
        st.expander("Evidencia y acciones recomendadas", expanded=True).write(
            "Cada alerta incluye evidencia puntual y acción recomendada para revisión documental/técnica."
        )
        st.expander("Limitación ética", expanded=True).write(
            "Este módulo no afirma fraude real; prioriza casos para auditoría posterior."
        )


def render_home() -> None:
    st.title("Electoral Integrity Analyzer")
    st.subheader("Analizador de Integridad Electoral por Etapas")
    render_ethical_warning()

    st.write(
        "Objetivo: analizar datasets electorales sintéticos para detectar anomalías por etapa "
        "mediante reglas simples y Z-score."
    )

    status = dataset_status_table()
    render_metrics()

    st.markdown("### Estado de datasets")
    st.dataframe(status, use_container_width=True)

    st.info("Ejecute la sección 'Cargar / generar datasets' para preparar y analizar datos.")


def render_data_management() -> None:
    st.title("Cargar / generar datasets")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generar datasets sintéticos", type="primary"):
            ok, message = run_generation_script()
            if ok:
                st.success("Datasets generados correctamente.")
                st.code(message)
                safe_load_and_validate()
            else:
                st.error("No se pudieron generar datasets con el script.")
                st.code(message)

    with col2:
        if st.button("Cargar datasets existentes"):
            safe_load_and_validate()

    status = dataset_status_table()
    st.dataframe(status, use_container_width=True)

    if st.session_state.datasets:
        st.success("Datasets disponibles en sesión.")
        preview_name = st.selectbox("Vista previa de dataset", list(st.session_state.datasets.keys()))
        preview_df = st.session_state.datasets[preview_name].head(20)
        st.dataframe(preview_df, use_container_width=True)

        validation = st.session_state.validation or {"errors": []}
        if validation["errors"]:
            st.error("Errores de validación:")
            for err in validation["errors"]:
                st.write(f"- {err}")
        else:
            st.success("Validación exitosa")

        if st.button("Ejecutar análisis completo"):
            if validation["errors"]:
                st.error("Corrija primero los errores de validación.")
            else:
                try:
                    analysis = run_analysis(st.session_state.datasets)
                    st.session_state.analysis = analysis
                    export_paths = export_reports(
                        analysis["alerts"], analysis["ranking"], analysis["summary"]
                    )
                    st.session_state.export_paths = export_paths
                    st.success("Análisis ejecutado y reportes exportados correctamente.")
                except Exception:
                    st.error("No fue posible ejecutar el análisis completo.")


def render_results_stage() -> None:
    render_stage_alerts("Resultados por mesa")
    datasets = st.session_state.datasets
    analysis = st.session_state.analysis

    if not datasets or not analysis:
        return

    results = datasets.get("05_resultados_mesa.csv", pd.DataFrame())
    charts = build_required_charts(analysis["alerts"], results, analysis["ranking"])

    with st.expander("Visualizaciones de esta etapa", expanded=True):
        st.plotly_chart(charts["histograma_participacion"], use_container_width=True)
        st.caption("Interpretación: permite identificar mesas con participación inusualmente alta o baja.")
        st.plotly_chart(charts["boxplot_nulos_invalidos"], use_container_width=True)
        st.caption("Interpretación: resalta mesas con tasas atípicas de nulos/inválidos.")


def render_consolidated_report() -> None:
    st.title("Reporte consolidado")
    render_ethical_warning()

    analysis = st.session_state.analysis
    datasets = st.session_state.datasets

    if not analysis:
        st.warning("Ejecute análisis completo desde la sección de carga/generación.")
        return

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
        stage_filter = st.selectbox("Filtrar por etapa", ["Todos"] + sorted(alerts["etapa"].dropna().unique().tolist()))
        severity_filter = st.selectbox(
            "Filtrar por severidad", ["Todos"] + sorted(alerts["severidad"].dropna().unique().tolist())
        )
        code_filter = st.selectbox(
            "Filtrar por código", ["Todos"] + sorted(alerts["codigo_alerta"].dropna().unique().tolist())
        )
        entity_type_filter = st.selectbox(
            "Filtrar por entidad_tipo", ["Todos"] + sorted(alerts["entidad_tipo"].dropna().unique().tolist())
        )

        entity_id_text = st.text_input("Filtrar por entidad_id (contiene)")
        mesa_id_text = st.text_input("Filtrar por mesa_id (cuando aplique)")
        usuario_id_text = st.text_input("Filtrar por usuario_id (cuando aplique)")

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
            filtered = filtered[filtered["entidad_id"].astype(str).str.contains(entity_id_text, case=False, na=False)]
        if mesa_id_text:
            filtered = filtered[
                (filtered["entidad_tipo"] == "mesa_id")
                & (filtered["entidad_id"].astype(str).str.contains(mesa_id_text, case=False, na=False))
            ]
        if usuario_id_text:
            filtered = filtered[
                (filtered["entidad_tipo"] == "usuario_id")
                & (filtered["entidad_id"].astype(str).str.contains(usuario_id_text, case=False, na=False))
            ]

        st.dataframe(filtered, use_container_width=True)
        st.markdown("### Ranking de riesgo")
        st.dataframe(ranking, use_container_width=True)

        export_paths = st.session_state.export_paths
        if export_paths:
            st.success("Archivos exportados correctamente.")
            st.write("Descargas disponibles:")
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
        st.caption("Interpretación: muestra en qué etapas se concentra el riesgo detectado.")

        st.plotly_chart(charts["alertas_por_severidad"], use_container_width=True)
        st.caption("Interpretación: permite priorizar revisión por criticidad.")

        st.plotly_chart(charts["histograma_participacion"], use_container_width=True)
        st.caption("Interpretación: identifica mesas con participación atípica.")

        st.plotly_chart(charts["boxplot_nulos_invalidos"], use_container_width=True)
        st.caption("Interpretación: señala dispersión de nulos e inválidos entre mesas.")

        st.plotly_chart(charts["ranking_riesgo_mesas"], use_container_width=True)
        st.caption("Interpretación: prioriza las 10 mesas con mayor score de riesgo.")

    with tab_method:
        st.info(
            "Z-score: medida estadística que indica qué tan lejos está un valor del promedio. "
            "Se marca como atípico cuando |Z-score| >= 3."
        )
        st.info(
            "Hash: resumen digital para verificar integridad. Si hash original y actual no coinciden, "
            "se genera alerta de integridad."
        )
        st.write(
            "Conclusión: este sistema genera señales de revisión y no demuestra fraude electoral por sí solo."
        )


def main() -> None:
    init_state()

    st.sidebar.title("Navegación")
    selected = st.sidebar.radio("Seleccione una etapa", MENU_OPTIONS)

    if selected == "Inicio":
        render_home()
    elif selected == "Cargar / generar datasets":
        render_data_management()
    elif selected == "Padrón y elegibilidad":
        render_stage_alerts("Padrón y elegibilidad")
    elif selected == "Circunscripción y mesa":
        render_stage_alerts("Circunscripción y mesa")
    elif selected == "Registro de sufragio":
        render_stage_alerts("Registro de sufragio")
    elif selected == "Escrutinio manual":
        render_stage_alerts("Escrutinio manual")
    elif selected == "Resultados por mesa":
        render_results_stage()
    elif selected == "Logs e integridad":
        render_stage_alerts("Logs e integridad")
    elif selected == "Reporte consolidado":
        render_consolidated_report()


if __name__ == "__main__":
    main()
