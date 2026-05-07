# Metodología

## Contexto
El proyecto implementa un analizador de anomalías para un proceso electoral simulado, en alcance académico de ciberseguridad.

## Datos sintéticos
Todos los datasets son generados localmente con semilla fija (`RANDOM_SEED = 42`) para reproducibilidad.

## Técnicas
1. **Reglas simples**: inconsistencias determinísticas en padrón, mesa, sufragio, resultados, logs e integridad.
2. **Z-score**: detección de valores atípicos con umbral `|z| >= 3`.

## Score de riesgo
- crítica = 3
- alta = 2
- media = 1

Clasificación:
- 0: Sin alerta
- 1 a 3: Riesgo bajo
- 4 a 7: Riesgo medio
- 8 a 12: Riesgo alto
- > 12: Revisión prioritaria

## Evaluación
Se compara contra `08_alertas_esperadas.csv` por:
- `codigo_alerta`
- `entidad_tipo`
- `entidad_id`

Métricas:
- alertas_esperadas
- alertas_detectadas
- coincidencias
- precision_aproximada
- cobertura_aproximada

## Limitaciones
- No usa datos reales ni personales.
- No prueba fraude real.
- No es sistema productivo.
- Resultados deben interpretarse como señales de revisión.

## Referencias técnicas
1. NIST CDF: https://nvlpubs.nist.gov/nistpubs/gcr/2024/24-058/NIST.GCR.24-058.html
2. NIST VRI: https://pages.nist.gov/VoterRecordsInterchange/
3. NIST CVR: https://pages.nist.gov/CastVoteRecords/
4. NIST EEL: https://pages.nist.gov/ElectionEventLogging/
5. NIST ERR: https://github.com/usnistgov/ElectionResultsReporting
6. EAC Audit Guide: https://www.eac.gov/sites/default/files/2024-11/Post_Election_Tabulation_Audit_Guide_508.pdf
7. NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
8. Streamlit layout: https://docs.streamlit.io/develop/api-reference/layout
9. Streamlit sidebar: https://docs.streamlit.io/develop/api-reference/layout/st.sidebar
10. Streamlit download: https://docs.streamlit.io/develop/api-reference/widgets/st.download_button
11. NN/g heurísticas: https://www.nngroup.com/articles/ten-usability-heuristics/
12. NN/g progressive disclosure: https://www.nngroup.com/articles/progressive-disclosure/
13. WCAG 2.2: https://www.w3.org/TR/WCAG22/
14. W3C accesibilidad: https://www.w3.org/WAI/fundamentals/accessibility-principles/
15. SciPy zscore: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.zscore.html
16. pandas read_csv: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
