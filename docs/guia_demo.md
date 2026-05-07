# Guía de Demo

## Objetivo de la demo
Mostrar en menos de 8 minutos el flujo completo del sistema de análisis electoral sintético por etapas.

## Paso 1: Preparación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Paso 2: Generar datos
```bash
python scripts/generate_synthetic_data.py
```
Verificar mensaje final con totales de votantes, mesas, usuarios y alertas esperadas.

## Paso 3: Ejecutar app
```bash
streamlit run app.py
```

## Paso 4: Flujo recomendado en UI
1. **Inicio**: explicar propósito y advertencia ética.
2. **Cargar / generar datasets**: cargar datos, validar y ejecutar análisis.
3. **Padrón y elegibilidad**: mostrar alertas PAD.
4. **Circunscripción y mesa**: mostrar alertas CIR.
5. **Registro de sufragio**: mostrar alertas SUF.
6. **Escrutinio manual**: mostrar alertas MAN.
7. **Resultados por mesa**: mostrar alertas RES + histogram/boxplot.
8. **Logs e integridad**: mostrar alertas LOG/INT.
9. **Reporte consolidado**: filtros, ranking, 5 visualizaciones y descargas CSV.

## Paso 5: Cierre
- Recordar que las alertas son señales de revisión.
- Repetir limitación ética: no prueba fraude real.
- Mostrar exportación de `alertas_detectadas.csv`, `ranking_riesgo.csv`, `resumen_hallazgos.csv`.
