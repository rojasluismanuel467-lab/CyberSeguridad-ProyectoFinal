"""Detector factory utilities."""

from __future__ import annotations

from src.detectors.circumscription_detector import CircumscriptionDetector
from src.detectors.eligibility_detector import EligibilityDetector
from src.detectors.log_integrity_detector import LogIntegrityDetector
from src.detectors.manual_count_detector import ManualCountDetector
from src.detectors.results_detector import ResultsDetector
from src.detectors.suffrage_detector import SuffrageDetector


def build_default_detectors() -> list:
    """Build default detector strategy list for the analysis pipeline."""
    return [
        EligibilityDetector(),
        CircumscriptionDetector(),
        SuffrageDetector(),
        ManualCountDetector(),
        ResultsDetector(),
        LogIntegrityDetector(),
    ]
