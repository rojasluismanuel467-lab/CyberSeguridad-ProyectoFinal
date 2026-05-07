# Electoral Integrity Analyzer

## 1. Objetivo
Electoral Integrity Analyzer (Analizador de Integridad Electoral por Etapas) es una aplicación académica en Python + Streamlit para detectar anomalías en un proceso electoral simulado por etapas.

## 2. Advertencia ética
Este sistema utiliza datos sintéticos generados con fines académicos. Las alertas no constituyen prueba de fraude electoral. Los resultados deben interpretarse como señales de revisión que requieren validación documental, técnica y contextual.

No se usan datos personales reales. No se analizan procesos electorales reales. No se atribuyen irregularidades a personas, partidos, países o instituciones reales.

## 3. Tecnologías
- Python 3.11+
- Streamlit
- pandas
- numpy
- scipy (Z-score)
- plotly
- faker
- pytest

## 4. Arquitectura
Monolito modular por capas con separación SOLID:
- Presentación (`app.py`)
- Carga/validación de datos (`src/data_loader`)
- Detectores por etapa (`src/detectors`)
- Analítica (estadística, score, resumen) (`src/analytics`)
- Orquestación (`src/pipeline`)
- Visualizaciones (`src/visualizations`)
- Exportación (`src/reports`)
- Generación de datos (`scripts/generate_synthetic_data.py`)

## 5. Estructura del repositorio
```text
electoral-integrity-analyzer/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── synthetic/
│   └── outputs/
├── scripts/
│   └── generate_synthetic_data.py
├── src/
│   ├── config/
│   ├── data_loader/
│   ├── domain/
│   ├── detectors/
│   ├── analytics/
│   ├── pipeline/
│   ├── visualizations/
│   └── reports/
├── tests/
└── docs/
```

## 6. Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows:
```bash
.venv\Scripts\activate
```

## 7. Generación de datasets
```bash
python scripts/generate_synthetic_data.py
```

## 8. Ejecución de la app
```bash
streamlit run app.py
```

## 9. Técnicas de detección
Se usan exactamente dos técnicas:
1. Reglas simples determinísticas.
2. Z-score para detección de outliers.

No se usa deep learning ni técnicas adicionales.

## 10. Datasets generados
- `01_padron_votantes.csv`
- `02_asignacion_mesas.csv`
- `03_registro_sufragio.csv`
- `04_clasificacion_votos_manual.csv`
- `05_resultados_mesa.csv`
- `06_logs_eventos.csv`
- `07_integridad_archivos.csv`
- `08_alertas_esperadas.csv`
- `usuarios_sistema.csv`

## 11. Visualizaciones
Se implementan 5 visualizaciones obligatorias:
1. Alertas por etapa.
2. Alertas por severidad.
3. Histograma de participación.
4. Boxplot de votos nulos e inválidos.
5. Top 10 mesas por score de riesgo.

## 12. Limitaciones
- Dataset completamente sintético.
- No es sistema productivo.
- No prueba fraude real.
- No reemplaza auditoría electoral formal.

## 13. Pruebas
```bash
pytest -q
```

## 14. Referencias técnicas
1. NIST CDF: https://nvlpubs.nist.gov/nistpubs/gcr/2024/24-058/NIST.GCR.24-058.html
2. NIST VRI: https://pages.nist.gov/VoterRecordsInterchange/
3. NIST CVR: https://pages.nist.gov/CastVoteRecords/
4. NIST EEL: https://pages.nist.gov/ElectionEventLogging/
5. NIST ERR: https://github.com/usnistgov/ElectionResultsReporting
6. EAC Audit Guide: https://www.eac.gov/sites/default/files/2024-11/Post_Election_Tabulation_Audit_Guide_508.pdf
7. NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
8. Streamlit Docs: https://docs.streamlit.io/
9. SciPy zscore: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.zscore.html
10. pandas read_csv: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
