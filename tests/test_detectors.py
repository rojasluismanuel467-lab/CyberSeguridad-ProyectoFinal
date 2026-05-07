"""Tests for detector contract and pipeline execution."""

from __future__ import annotations

import pandas as pd

from scripts.generate_synthetic_data import main as generate_data_main
from src.data_loader.csv_loader import load_datasets
from src.detectors.circumscription_detector import CircumscriptionDetector
from src.detectors.eligibility_detector import EligibilityDetector
from src.detectors.log_integrity_detector import LogIntegrityDetector
from src.detectors.manual_count_detector import ManualCountDetector
from src.detectors.results_detector import ResultsDetector
from src.detectors.suffrage_detector import SuffrageDetector
from src.domain.alert_types import ALERT_COLUMNS
from src.pipeline.analysis_pipeline import AnalysisPipeline


def _prepared_datasets() -> dict[str, pd.DataFrame]:
    generate_data_main()
    return load_datasets()


def test_each_detector_returns_dataframe_with_standard_columns() -> None:
    datasets = _prepared_datasets()
    detectors = [
        EligibilityDetector(),
        CircumscriptionDetector(),
        SuffrageDetector(),
        ManualCountDetector(),
        ResultsDetector(),
        LogIntegrityDetector(),
    ]

    for detector in detectors:
        df = detector.detect(datasets)
        assert isinstance(df, pd.DataFrame)
        for col in ALERT_COLUMNS:
            assert col in df.columns


def test_pipeline_runs_without_exception_and_detects_anomalies() -> None:
    datasets = _prepared_datasets()
    pipeline = AnalysisPipeline(
        [
            EligibilityDetector(),
            CircumscriptionDetector(),
            SuffrageDetector(),
            ManualCountDetector(),
            ResultsDetector(),
            LogIntegrityDetector(),
        ]
    )

    result = pipeline.run(datasets)
    alerts = result["alerts"]

    assert isinstance(alerts, pd.DataFrame)
    assert len(alerts) > 0
    assert alerts["codigo_alerta"].nunique() >= 5
    assert isinstance(result["ranking"], pd.DataFrame)
    assert isinstance(result["summary"], pd.DataFrame)
