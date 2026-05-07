"""Global configuration constants for Electoral Integrity Analyzer."""

RANDOM_SEED = 42

NUM_VOTERS = 5000
NUM_MUNICIPALITIES = 5
NUM_ZONES = 10
NUM_POLLING_STATIONS = 25
NUM_TABLES = 80
NUM_USERS = 60

ELECTION_DATE = "2026-06-03"
ELECTION_OPEN_TIME = "08:00:00"
ELECTION_CLOSE_TIME = "16:00:00"

MIN_VOTING_AGE = 18
MAX_REASONABLE_AGE = 115

HIGH_TURNOUT_THRESHOLD = 0.95
Z_SCORE_THRESHOLD = 3.0

CRITICAL_SCORE = 3
HIGH_SCORE = 2
MEDIUM_SCORE = 1

ETHICAL_WARNING = (
    "Este sistema utiliza datos sintéticos generados con fines académicos. "
    "Las alertas no constituyen prueba de fraude electoral. "
    "Los resultados deben interpretarse como señales de revisión que requieren "
    "validación documental, técnica y contextual."
)
