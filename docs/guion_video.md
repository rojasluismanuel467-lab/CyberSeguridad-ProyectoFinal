# Guion de Video: Electoral Integrity Analyzer (Enfoque Ciberseguridad + Estandares NIST/EAC)

Este documento contiene la estructura y el guion sugerido para la presentacion en video del proyecto. Esta pensado para 3 integrantes, equilibrando tiempos y combinando demostracion en vivo con explicacion tecnica.

Objetivo del guion: que quede claro que decisiones se tomaron en ciberseguridad (auditoria, integridad, trazabilidad, RBAC/SoD) y como se ven reflejadas en el codigo y en la UI.

## Informacion General
- Duracion estimada: 5 a 7 minutos.
- Modalidad: grabacion de pantalla (Streamlit) + camara opcional al inicio/cierre.

Roles sugeridos:
- Integrante 1 (I1): contexto, estandares NIST/EAC, arquitectura, SSDF y UX/accesibilidad.
- Integrante 2 (I2): datasets sinteticos, validacion y ejecucion del pipeline.
- Integrante 3 (I3): hallazgos y foco fuerte en Logs e integridad (controles cyber).

## Mensajes Clave
1. Esto no es un sistema de votacion: es una herramienta de auditoria forense sobre datos electorales sinteticos.
2. Lo "cyber" del proyecto se evidencia en controles: auditoria (logs), integridad (hashes y control de publicacion) y control de acceso (RBAC + segregacion de funciones).
3. Los datos/etapas se alinean conceptualmente con NIST Common Data Formats (CDF) y la guia EAC de auditoria post-electoral (sin afirmar certificacion ni conformidad oficial de esquema).

## Mapeo Rapido: NIST/EAC -> Artefactos del Proyecto
Sugerencia: mostrar esta tabla 10-15 segundos.

| Estandar / Artefacto | En el proyecto | Archivo(s) | Que cubre en ciberseguridad |
|---|---|---|---|
| NIST CDF (interoperabilidad) | diccionario + esquemas + validacion | `docs/diccionario_datos.md`, `src/domain/schemas.py`, `src/data_loader/validators.py` | consistencia de evidencia, reduccion de errores, trazabilidad |
| NIST VRI | padron/eligibilidad | `01_padron_votantes.csv` | calidad de datos, minimizacion de PII (hash), deteccion de registros invalidos |
| NIST CVR | papeleta/voto (simulado) | `04_clasificacion_votos_manual.csv` | inconsistencias y manipulacion humana (forense) |
| NIST ERR | resultados agregados | `05_resultados_mesa.csv` | validaciones aritmeticas + outliers para priorizar auditoria |
| NIST EEL | logs de eventos | `06_logs_eventos.csv` | violaciones RBAC, brute force, post-cierre, SoD |
| EAC Post-Election Audit Guide | evidencia exportable + priorizacion | `data/outputs/*.csv` | evidencia portable (CSV) y ranking de riesgo |

---

## Acto 1: Contexto, Estandares, Arquitectura y UX (I1)
Duracion: ~1.5 a 2 minutos.

| Que mostrar en pantalla | Que decir (guion tecnico) |
|---|---|
| Inicio (titulo + advertencia etica) | **I1**: "Somos [Nombres]. Presentamos Electoral Integrity Analyzer: una herramienta de auditoria forense para detectar anomalias en procesos electorales simulados, con foco en ciberseguridad y trazabilidad." |
| Advertencia etica | **I1**: "Todos los datos son sinteticos. No buscamos probar fraude real: buscamos generar senales de auditoria y evidencia reproducible sin exponer datos personales reales." |
| Referencias (opcional `docs/metodologia.md`) | **I1**: "Nos alineamos conceptualmente con NIST CDF: VRI, CVR, ERR y EEL, y con el enfoque del EAC para auditorias post-electorales. En desarrollo seguro usamos el marco NIST SSDF (SP 800-218): separacion por capas, validacion de entradas, pruebas y reproducibilidad." |
| Arquitectura (README o `docs/arquitectura.md`) | **I1**: "Arquitectura por capas: UI en `app.py`, pipeline en `src/pipeline/analysis_pipeline.py`, validacion en `src/data_loader/validators.py`, detectores por etapa en `src/detectors/`, y exportacion de evidencia en `src/reports/`." |
| UI (sidebar + tabs + expanders) | **I1**: "UX: aplicamos progressive disclosure (tabs/expanders) para no saturar al analista. Heuristicas NN/g: visibilidad de estado (metricas y mensajes), consistencia por etapa y prevencion de errores (no ejecuta analisis si falla validacion). Accesibilidad: guia WCAG 2.2 y principios WAI/POUR (texto claro, navegacion consistente y no depender solo de color)." |

---

## Acto 2: Datos Sinteticos, Validacion y Ejecucion (I2)
Duracion: ~1.5 a 2 minutos.

| Que mostrar en pantalla | Que decir (guion tecnico) |
|---|---|
| Menu: "Cargar / generar datasets" | **I2**: "Generamos datasets con `scripts/generate_synthetic_data.py` usando `RANDOM_SEED = 42` para reproducibilidad. Esto es clave para auditoria: misma entrada, mismo resultado." |
| Boton: "Generar datasets sinteticos" + tabla de estado | **I2**: "Privacidad: evitamos PII real; por ejemplo `documento_hash` se calcula con SHA-256. Tambien simulamos cadena de custodia con hashes en logs (`hash_antes/hash_despues`) y en integridad (`hash_original/hash_actual`)." |
| Boton: "Cargar datasets existentes" + validacion | **I2**: "La carga usa `pandas.read_csv` y la validacion asegura: columnas obligatorias, IDs no nulos, fechas/horas validas, categorias permitidas y llaves referenciales entre datasets. Si hay errores, el sistema bloquea la ejecucion del analisis." |
| Boton: "Ejecutar analisis completo" | **I2**: "Al ejecutar, la UI orquesta el pipeline: corre detectores, consolida alertas con un esquema estandar y produce ranking/summary, ademas de exportar CSVs para evidencia." |

---

## Acto 3: Hallazgos y Controles Cyber (I3)
Duracion: ~2.5 a 3 minutos.

### 3A. Deteccion estadistica (priorizacion)
| Que mostrar en pantalla | Que decir (guion tecnico) |
|---|---|
| Resultados por mesa + visualizaciones | **I3**: "Para priorizar auditoria, usamos Z-score con `scipy.stats.zscore` (explicable y trazable). Histogramas y boxplots resaltan mesas outlier en participacion o nulos/invalidos." |

### 3B. Logs e integridad (nucleo cyber)
| Que mostrar en pantalla | Que decir (guion tecnico) |
|---|---|
| Logs e integridad -> "Tabla de alertas" | **I3**: "Esta etapa implementa controles de seguridad operacional en `src/detectors/log_integrity_detector.py`: auditoria, RBAC, segregacion de funciones e integridad." |
| Mostrar LOG-02 | **I3**: "LOG-02: accion no permitida por rol. Hallazgo directo de control de acceso (RBAC)." |
| Mostrar LOG-06 | **I3**: "LOG-06: auto-aprobacion. Segregacion de funciones (SoD): quien cambia no aprueba." |
| Mostrar LOG-01 | **I3**: "LOG-01: modificacion post-cierre sin aprobacion. Control de cambios y proteccion contra tampering tardio." |
| Mostrar LOG-04 | **I3**: "LOG-04: multiples fallos de login. Senal tipica de brute force o credenciales comprometidas." |
| Mostrar INT-01..INT-04 | **I3**: "INT-01..INT-04 validan integridad de artefactos: hash original vs actual, publicacion vs firma, y cambios despues del cierre. Esto simula evidencia criptografica y control de release." |

### 3C. Reporte consolidado (evidencia + ranking)
| Que mostrar en pantalla | Que decir (guion tecnico) |
|---|---|
| Reporte consolidado + descargas CSV | **I3**: "El consolidado traduce severidad a score y rankea entidades (mesa/usuario/archivo/evento). Exportamos evidencia en CSV para auditoria fuera de la UI." |

---

## Acto 4: Cierre (I1 o I3)
Duracion: ~40 a 60 segundos.

| Que mostrar en pantalla | Que decir (guion tecnico) |
|---|---|
| Resumen o consolidado | **I1/I3**: "Conclusion: el proyecto es auditable y defensivo: datos validados, pipeline modular, reglas explicables, estadistica transparente y controles cyber sobre logs e integridad. Permite priorizar revision y exportar evidencia." |

## Consejos de Grabacion
1. Ensayen la navegacion por las secciones reales del menu: "Cargar / generar datasets", "Resultados por mesa", "Logs e integridad", "Reporte consolidado".
2. En Logs e integridad, muestren solo 3-4 alertas (LOG-02, LOG-06, INT-01, INT-03) y expliquen el control detras.
3. Si preguntan "donde esta lo cyber", respondan con el triangulo: RBAC/SoD + auditoria (logs) + integridad (hash/firma/publicacion) y apunten al detector de esa etapa.
