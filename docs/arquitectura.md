# Arquitectura

## Tipo
Monolito modular por capas orientado a demo académica.

## Capas y responsabilidades
- **Presentación**: `app.py` (Streamlit, navegación, interacción).
- **Carga y validación**: `src/data_loader`.
- **Dominio**: `src/domain` (esquemas, catálogo de alertas).
- **Detectores**: `src/detectors` por etapa electoral.
- **Analítica**: `src/analytics` (Z-score, score de riesgo, resumen).
- **Pipeline**: `src/pipeline/analysis_pipeline.py`.
- **Visualización**: `src/visualizations/charts.py`.
- **Reportes**: `src/reports/report_generator.py`.
- **Datos sintéticos**: `scripts/generate_synthetic_data.py`.

## SOLID aplicado
- SRP: un módulo, una responsabilidad principal.
- OCP: nuevos detectores se agregan sin modificar los existentes.
- LSP: todos los detectores cumplen `detect(datasets) -> DataFrame`.
- ISP: contrato mínimo (`detect`).
- DIP: UI depende del pipeline, no de lógica interna de cada detector.

## Diagrama Mermaid
```mermaid
flowchart LR

    A["Usuarios: administrador, analista, auditor, observador"] --> UI["Streamlit UI"]

    UI --> P["Analysis Pipeline"]

    P --> L["Data Loader"]
    L --> V["Validators"]
    V --> D["Datasets sintéticos"]

    P --> ED["Eligibility Detector"]
    P --> CD["Circumscription Detector"]
    P --> SD["Suffrage Detector"]
    P --> MD["Manual Count Detector"]
    P --> RD["Results Detector"]
    P --> LD["Log Integrity Detector"]

    ED --> A1["Alertas normalizadas"]
    CD --> A1
    SD --> A1
    MD --> A1
    RD --> A1
    LD --> A1

    A1 --> ST["Statistics Engine: Z-score"]
    A1 --> RS["Risk Score Engine"]
    RS --> O["Outputs: alertas, ranking, resumen"]

    O --> C["Charts"]
    O --> R["Report Generator"]
    C --> UI
    R --> UI
```
