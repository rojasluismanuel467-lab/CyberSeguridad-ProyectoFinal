"""Streamlit UI for Electoral Integrity Analyzer."""
from __future__ import annotations
from typing import Any

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
    "Preparar análisis",
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


def all_datasets_exist(base_path: str = "data/synthetic") -> bool:
    path = Path(base_path)
    return all((path / name).exists() for name in _EXPECTED_DATASETS)


def init_state() -> None:
    defaults = {
        "datasets": None,
        "validation": None,
        "analysis": None,
        "export_paths": None,
        "is_busy": False,
        "gen_action": None,
        "load_trigger": False,
        "gen_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def run_generation_script() -> Any:
    """Runs the generation script and yields progress (0-100) and extra data (label or final result)."""
    try:
        proc = subprocess.Popen(
            ["python", "-u", "scripts/generate_synthetic_data.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        current_progress = 0
        if proc.stdout:
            for line in proc.stdout:
                if line.startswith("[PROGRESS]"):
                    try:
                        current_progress = int(line.split("]")[1].strip())
                        yield current_progress, None
                    except ValueError:
                        pass
                elif line.startswith("[LABEL]"):
                    label = line.split("]")[1].strip()
                    yield current_progress, label
        proc.wait()
        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ""
            yield 100, (False, stderr.strip() or "Falló la generación de datasets")
        else:
            yield 100, (True, "Datasets generados correctamente.")
    except Exception as e:
        yield 100, (False, f"Error al ejecutar script: {str(e)}")


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
            st.session_state.gen_message = ("warning", "Errores de validación encontrados. Revise el detalle.")
        else:
            st.session_state.gen_message = ("success", "Datasets cargados y validados correctamente.")

    except DatasetLoadError as exc:
        st.session_state.gen_message = ("warning", str(exc))
    except Exception:
        st.session_state.gen_message = ("error", "Ocurrió un problema al cargar o validar datasets.")


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
            st.dataframe(severity_counts, width="stretch")
            st.info("Las alertas son señales para revisión; no constituyen prueba de fraude.")

    with tabs[1]:
        if stage_alerts.empty:
            st.success("No hay registros de alerta para esta etapa.")
        else:
            st.dataframe(stage_alerts, width="stretch")

    with tabs[2]:
        if stage_alerts.empty:
            st.success("Sin evidencia que mostrar para esta etapa.")
        else:
            evidence_cols = ["codigo_alerta", "entidad_id", "descripcion", "evidencia", "accion_recomendada"]
            present = [c for c in evidence_cols if c in stage_alerts.columns]
            st.dataframe(stage_alerts[present], width="stretch")


def render_home() -> None:
    st.title("Electoral Integrity Analyzer")
    st.subheader("Plataforma de Auditoría Forense Electoral")
    render_ethical_warning()

    st.markdown("""
    ### ¿Cómo funciona el análisis?
    Esta plataforma utiliza una combinación de técnicas avanzadas para detectar posibles irregularidades en procesos electorales a partir de datasets sintéticos:

    1. **Reglas Determinísticas**: Verificación estricta de reglas de negocio (ej. votantes no inscritos, múltiples votos por persona, o inconsistencias en la geografía electoral).
    2. **Análisis Estadístico (Z-Score)**: Identificamos anomalías matemáticas en la participación y comportamiento de votos nulos/inválidos que se alejan significativamente del promedio nacional.
    3. **Auditoría de Integridad**: Comprobamos mediante firmas digitales (hashes) que los archivos de resultados no han sido manipulados después de su generación.
    4. **Trazabilidad de Logs**: Análisis de eventos de sistema para detectar accesos no autorizados o acciones sospechosas durante el proceso.

    ### ¿Qué puede encontrar con esta herramienta?
    - **Fraude en el Padrón**: Registros duplicados o votantes inhabilitados.
    - **Inconsistencias de Mesa**: Resultados que no coinciden con el conteo manual o participación superior al 100%.
    - **Anomalías Estadísticas**: Mesas con comportamientos atípicos que sugieren intervención externa.
    - **Brechas de Integridad**: Archivos de datos alterados o logs de sistema borrados.
    """)

    st.divider()
    
    if st.session_state.is_busy:
        st.info("⏳ El sistema está procesando datos en este momento...")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🚀 Comenzar análisis", type="primary", use_container_width=True):
                st.session_state.current_page = "Preparar análisis"
                st.rerun()


def render_data_management() -> None:
    st.title("Preparar análisis")

    datasets_exist = all_datasets_exist()

    # AUTO-GENERATE if missing
    if not datasets_exist and not st.session_state.is_busy:
        st.session_state.is_busy = True
        st.session_state.gen_action = "generar"
        st.rerun()

    if datasets_exist:
        col1, col2 = st.columns(2)
        with col1:
            # Unified action: Load (if needed) and Analyze
            btn_label = "Ejecutar análisis completo"
            if st.button(btn_label, type="primary", disabled=st.session_state.is_busy):
                try:
                    st.session_state.is_busy = True
                    with st.spinner("Procesando datos y ejecutando análisis..."):
                        # 1. Load and validate if not in session
                        if st.session_state.datasets is None:
                            safe_load_and_validate()
                        
                        # 2. Check for errors before analysis
                        validation = st.session_state.validation or {"errors": []}
                        if validation["errors"]:
                            st.warning("No se puede analizar: existen errores de validación en los archivos.")
                        else:
                            # 3. Run Analysis
                            analysis = run_analysis(st.session_state.datasets)
                            st.session_state.analysis = analysis
                            export_paths = export_reports(
                                analysis["alerts"], analysis["ranking"], analysis["summary"]
                            )
                            st.session_state.export_paths = export_paths
                            st.session_state.gen_message = ("success", "Análisis completado y reportes generados.")
                except Exception as e:
                    st.session_state.gen_message = ("error", f"Error durante el proceso: {str(e)}")
                finally:
                    st.session_state.is_busy = False
                    st.rerun()
        with col2:
            if st.button("Regenerar datasets", disabled=st.session_state.is_busy):
                st.session_state.is_busy = True
                st.session_state.gen_action = "regenerar"
                st.session_state.gen_message = None
                st.rerun()
    else:
        st.warning("No se detectaron datasets. Iniciando generación automática...")

    # Display persistent messages below buttons
    if st.session_state.gen_message:
        msg_type, msg_text = st.session_state.gen_message
        if msg_type == "success": st.success(msg_text)
        elif msg_type == "warning": st.warning(msg_text)
        elif msg_type == "error": st.error(msg_text)

    # Placeholders for full-width progress reporting - moved BELOW buttons
    label_placeholder = st.empty()
    progress_placeholder = st.empty()

    # Handle the generation process if triggered
    if st.session_state.is_busy and st.session_state.gen_action:
        action_name = "generación" if st.session_state.gen_action == "generar" else "regeneración"
        progress_bar = progress_placeholder.progress(0)
        
        success = False
        message = ""
        current_label = f"Preparando {action_name}"
        
        for progress, data in run_generation_script():
            if isinstance(data, str):
                current_label = data
            
            label_placeholder.markdown(f"""
                <div style="height: 30px; display: flex; align-items: flex-end; margin-bottom: 5px;">
                    <span style="font-weight: 500; color: #1E88E5; animation: fadeIn 0.8s ease-in-out;">
                        {current_label}<span class="dots"></span>
                    </span>
                </div>
                <style>
                    @keyframes fadeIn {{
                        from {{ opacity: 0.3; transform: translateY(2px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    .dots::after {{
                        content: '.';
                        animation: loading-dots 1.5s steps(4, end) infinite;
                    }}
                    @keyframes loading-dots {{
                        0% {{ content: ''; }}
                        25% {{ content: '.'; }}
                        50% {{ content: '..'; }}
                        75% {{ content: '...'; }}
                        100% {{ content: ''; }}
                    }}
                </style>
            """, unsafe_allow_html=True)
            
            progress_bar.progress(progress / 100.0)
            if not isinstance(data, str) and data is not None:
                success, message = data
        
        st.session_state.is_busy = False
        st.session_state.gen_action = None
        
        if success:
            st.session_state.gen_message = ("success", "Datasets generados correctamente.")
            safe_load_and_validate()
            st.rerun()
        else:
            st.session_state.gen_message = ("error", f"Error: {message}")
            st.rerun()

    # Handle the load process if triggered (not needed now but kept for safety if used elsewhere)
    if st.session_state.load_trigger:
        with st.spinner("Cargando y validando datasets..."):
            safe_load_and_validate()
        st.session_state.is_busy = False
        st.session_state.load_trigger = False
        st.rerun()

    st.markdown("### Estado de datasets")
    if datasets_exist:
        st.caption("💡 Haz clic en una fila para ver una vista previa del dataset.")
    
    df_status = dataset_status_table()
    selection = st.dataframe(
        df_status,
        use_container_width=True,
        hide_index=True,
        on_select="rerun" if datasets_exist else "ignore",
        selection_mode="single-row" if datasets_exist else None,
    )

    # Show preview based on selection (Disk or Session)
    if selection.selection.rows:
        selected_idx = selection.selection.rows[0]
        preview_name = df_status.iloc[selected_idx]["dataset"]
        
        # Priority 1: Session Data
        if st.session_state.datasets and preview_name in st.session_state.datasets:
            st.markdown(f"#### Vista previa: `{preview_name}` (en sesión)")
            st.dataframe(st.session_state.datasets[preview_name].head(20), use_container_width=True)
        else:
            # Priority 2: Disk Data
            file_path = Path("data/synthetic") / preview_name
            if file_path.exists():
                st.markdown(f"#### Vista previa: `{preview_name}` (vista previa desde archivo)")
                try:
                    df_disk = pd.read_csv(file_path, nrows=20)
                    st.dataframe(df_disk, use_container_width=True)
                except Exception as e:
                    st.error(f"No se pudo leer el archivo: {e}")
            else:
                st.info(f"El dataset `{preview_name}` no existe todavía.")

    if st.session_state.datasets:
        validation = st.session_state.validation or {"errors": []}
        if validation["errors"]:
            st.warning("Errores de validación:")
            for err in validation["errors"]:
                st.write(f"- {err}")



def render_results_stage() -> None:
    render_stage_alerts("Resultados por mesa")

    analysis = st.session_state.analysis
    if not analysis:
        return

    datasets = st.session_state.datasets
    results = datasets.get("05_resultados_mesa.csv", pd.DataFrame()) if datasets else pd.DataFrame()
    charts = build_required_charts(analysis["alerts"], results, analysis["ranking"])

    with st.expander("Visualizaciones de esta etapa", expanded=True):
        st.plotly_chart(charts["histograma_participacion"], width="stretch")
        st.caption("Permite identificar mesas con participación inusualmente alta o baja.")
        st.plotly_chart(charts["boxplot_nulos_invalidos"], width="stretch")
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
        st.dataframe(summary, width="stretch")
        render_metrics()

    with tab_table:
        filtered = _filter_alerts(alerts)
        st.dataframe(filtered, width="stretch")

        st.markdown("### Ranking de riesgo")
        st.dataframe(ranking, width="stretch")

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

        st.plotly_chart(charts["alertas_por_etapa"], width="stretch")
        st.caption("Muestra en qué etapas se concentra el riesgo detectado.")

        st.plotly_chart(charts["alertas_por_severidad"], width="stretch")
        st.caption("Permite priorizar revisión por criticidad.")

        st.plotly_chart(charts["histograma_participacion"], width="stretch")
        st.caption("Identifica mesas con participación atípica.")

        st.plotly_chart(charts["boxplot_nulos_invalidos"], width="stretch")
        st.caption("Señala dispersión de nulos e inválidos entre mesas.")

        st.plotly_chart(charts["ranking_riesgo_mesas"], width="stretch")
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

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Inicio"

    pages = {
        "Inicio": render_home,
        "Preparar análisis": render_data_management,
        "Padrón y elegibilidad": lambda: render_stage_alerts("Padrón y elegibilidad"),
        "Circunscripción y mesa": lambda: render_stage_alerts("Circunscripción y mesa"),
        "Registro de sufragio": lambda: render_stage_alerts("Registro de sufragio"),
        "Escrutinio manual": lambda: render_stage_alerts("Escrutinio manual"),
        "Resultados por mesa": render_results_stage,
        "Logs e integridad": lambda: render_stage_alerts("Logs e integridad"),
        "Reporte consolidado": render_consolidated_report,
    }

    st.sidebar.title("Navegación")
    
    # Simple navigation with session state
    selected = st.sidebar.radio(
        "Seleccione una etapa", 
        MENU_OPTIONS, 
        index=MENU_OPTIONS.index(st.session_state.current_page),
        format_func=_nav_label
    )
    
    if selected != st.session_state.current_page:
        st.session_state.current_page = selected
        st.rerun()
    
    pages[selected]()


if __name__ == "__main__":
    main()
