"""Plotly chart builders for mandatory project visualizations."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def chart_alerts_by_stage(alerts: pd.DataFrame):
    stage_counts = alerts.groupby("etapa", as_index=False).size().rename(columns={"size": "total_alertas"})
    return px.bar(
        stage_counts,
        x="etapa",
        y="total_alertas",
        title="Alertas por etapa",
        labels={"etapa": "Etapa", "total_alertas": "Total de alertas"},
    )


def chart_alerts_by_severity(alerts: pd.DataFrame):
    severity_counts = alerts.groupby("severidad", as_index=False).size().rename(columns={"size": "total_alertas"})
    return px.bar(
        severity_counts,
        x="severidad",
        y="total_alertas",
        title="Alertas por severidad",
        labels={"severidad": "Severidad", "total_alertas": "Total de alertas"},
        color="severidad",
    )


def chart_participation_histogram(results: pd.DataFrame):
    return px.histogram(
        results,
        x="participacion_pct",
        nbins=20,
        title="Histograma de participación por mesa",
        labels={"participacion_pct": "Participación (%)"},
    )


def chart_null_invalid_boxplot(results: pd.DataFrame):
    work = results.copy()
    total = work["total_reportado"].replace(0, pd.NA)
    work["votos_nulos_pct"] = (work["votos_nulos"] / total).fillna(0)
    work["votos_invalidos_pct"] = (work["votos_invalidos"] / total).fillna(0)

    melted = work[["votos_nulos_pct", "votos_invalidos_pct"]].melt(
        var_name="tipo", value_name="porcentaje"
    )
    return px.box(
        melted,
        x="tipo",
        y="porcentaje",
        title="Boxplot de votos nulos e inválidos",
        labels={"tipo": "Tipo", "porcentaje": "Porcentaje"},
    )


def chart_top_risk_tables(ranking: pd.DataFrame):
    mesas = ranking[ranking["entidad_tipo"] == "mesa_id"].copy().head(10)
    return px.bar(
        mesas,
        x="score_total",
        y="entidad_id",
        orientation="h",
        title="Top 10 mesas por score de riesgo",
        labels={"score_total": "Score total", "entidad_id": "Mesa"},
    )


def build_required_charts(alerts: pd.DataFrame, results: pd.DataFrame, ranking: pd.DataFrame) -> dict[str, object]:
    """Build the five mandatory visualizations."""
    return {
        "alertas_por_etapa": chart_alerts_by_stage(alerts),
        "alertas_por_severidad": chart_alerts_by_severity(alerts),
        "histograma_participacion": chart_participation_histogram(results),
        "boxplot_nulos_invalidos": chart_null_invalid_boxplot(results),
        "ranking_riesgo_mesas": chart_top_risk_tables(ranking),
    }
