# Guión de Video: Electoral Integrity Analyzer

Este documento contiene la estructura y el guión sugerido para la presentación en video del proyecto. Está diseñado para 3 integrantes, equilibrando los tiempos de habla y combinando la explicación técnica con la demostración en vivo.

## 📋 Información General
- **Duración Estimada**: 5 a 7 minutos.
- **Herramientas**: Grabación de pantalla compartida (Zoom, Teams, OBS, etc.).
- **Roles sugeridos**:
  - **Integrante 1 (I1)**: Introducción, Contexto Ético y Conclusión.
  - **Integrante 2 (I2)**: Flujo de Trabajo, Preparación de Datos y Ejecución del Análisis.
  - **Integrante 3 (I3)**: Explicación de Hallazgos, Visualizaciones y Metodología Forense.

---

## 🎬 Acto 1: Introducción y Contexto Ético (Integrante 1)
**Duración**: ~1.5 minutos

| 🎥 ¿Qué mostrar en pantalla? | 🗣️ ¿Qué decir? (Guión base) |
| :--- | :--- |
| **Cámara**: Los tres integrantes saludan o diapositiva de título. | **I1**: "Hola a todos. Somos [Nombres del equipo] y hoy les presentamos el **Electoral Integrity Analyzer**, una plataforma de auditoría forense diseñada para analizar la transparencia en procesos electorales." |
| **Pantalla**: Aplicación abierta en la pestaña **Inicio**, enfocando la "Advertencia Ética" y la descripción metodológica. | **I1**: "Antes de comenzar la demostración, queremos hacer una **declaración ética fundamental**: Todos los datos que verán en esta herramienta son **100% sintéticos y generados de forma aleatoria** mediante scripts de Python para fines puramente académicos y de demostración de ciberseguridad. No utilizamos datos de votantes reales, ni representamos ningún proceso electoral gubernamental en particular." |
| **Pantalla**: Hacer scroll suave por la página de inicio mostrando las técnicas (Reglas, Z-Score, Hashes). | **I1**: "Nuestro objetivo es demostrar cómo, mediante técnicas forenses como reglas determinísticas, análisis estadístico y auditoría de integridad, es posible detectar anomalías y posibles fraudes. A continuación, mi compañero(a) [Nombre de I2] les mostrará cómo la herramienta prepara y procesa estos datos." |

---

## 🎬 Acto 2: Preparación de Datos y Análisis Automático (Integrante 2)
**Duración**: ~1.5 a 2 minutos

| 🎥 ¿Qué mostrar en pantalla? | 🗣️ ¿Qué decir? (Guión base) |
| :--- | :--- |
| **Pantalla**: Hacer clic en el botón `🚀 Comenzar análisis` de la página de inicio. El sistema redirige a **Preparar análisis**. | **I2**: "Gracias, [Nombre I1]. Cuando iniciamos la plataforma, lo primero que necesitamos es un conjunto de datos. Hemos diseñado un sistema que automatiza esta preparación." |
| **Pantalla**: Mostrar la barra de carga automática y los mensajes ("Generando datos de votantes...", "Uniendo datos..."). | **I2**: "Si el sistema detecta que no hay datos previos, **inicia una generación sintética en tiempo real**. Aquí se crean simulaciones de padrones, asignación de mesas, escrutinios y logs de sistema, imitando las etapas de una elección real." |
| **Pantalla**: Una vez terminada la carga, hacer clic en una fila de la tabla inferior para mostrar la vista previa del archivo. | **I2**: "Una vez generados, el sistema nos permite inspeccionar rápidamente la estructura de los archivos directamente desde la interfaz. Con los datos listos, procedemos a iniciar la auditoría." |
| **Pantalla**: Hacer clic en el botón `Ejecutar análisis completo` y esperar a que aparezca el Dashboard de éxito con las 7 tarjetas. | **I2**: "Al ejecutar el análisis, la plataforma lanza un *pipeline* que aplica todas nuestras reglas de negocio y algoritmos. Como vemos, el proceso ha finalizado con éxito, generando reportes para las diferentes etapas. Ahora, [Nombre de I3] les guiará por los resultados y hallazgos." |

---

## 🎬 Acto 3: Exploración de Hallazgos y Visualizaciones (Integrante 3)
**Duración**: ~2.5 minutos

| 🎥 ¿Qué mostrar en pantalla? | 🗣️ ¿Qué decir? (Guión base) |
| :--- | :--- |
| **Pantalla**: Dashboard de éxito en la vista de Preparar Análisis. Hacer clic en el botón `Ver detalle` de la tarjeta **Resultados por mesa**. | **I3**: "Gracias, [Nombre I2]. Nuestro hub de resultados centraliza las anomalías detectadas. Empecemos revisando la etapa de Escrutinio y Resultados por Mesa." |
| **Pantalla**: Dentro de la pestaña, ir a la sub-pestaña **Hallazgos**. Mostrar cómo se ordenan desde los rojos (Críticos) hasta los azules. | **I3**: "Una de las características clave de nuestra herramienta es la **traducción de anomalías a lenguaje natural**. En lugar de ver solo tablas de datos crudos, el sistema clasifica y describe el problema. Por ejemplo, prioriza en rojo las alertas **críticas**, como mesas donde la participación supera matemáticamente el 100%, indicándonos exactamente a cuántas entidades afecta para una mitigación inmediata." |
| **Pantalla**: Hacer scroll hacia abajo para abrir el expander "Visualizaciones de esta etapa" (Histograma y Boxplot). | **I3**: "Adicionalmente, aplicamos modelos estadísticos como el cálculo del **Z-Score**. Esto nos genera histogramas y gráficos de caja (*boxplots*) que resaltan visualmente mesas con tasas de participación o votos nulos atípicamente altas en comparación con la media, lo cual es un indicador clásico de manipulación local." |
| **Pantalla**: Navegar a la pestaña **Logs e integridad** en el Hub de Resultados. | **I3**: "Finalmente, desde el punto de vista de la ciberseguridad pura, la etapa de Integridad verifica si los archivos originales han sido modificados después de su creación, comprobando **firmas digitales (hashes)**, y revisa accesos no autorizados en los registros del sistema." |

---

## 🎬 Acto 4: Conclusión (Integrante 1 o 3)
**Duración**: ~1 minuto

| 🎥 ¿Qué mostrar en pantalla? | 🗣️ ¿Qué decir? (Guión base) |
| :--- | :--- |
| **Pantalla**: Cambiar a la pestaña **Reporte Consolidado**. Mostrar el score general y las métricas. | **I1 o I3**: "Para cerrar, la plataforma compila todas estas alertas en un **Reporte Consolidado** que califica el nivel de riesgo global de la elección mediante un sistema de puntuación (*scoring*)." |
| **Pantalla**: Volver a la página de **Inicio** o mostrar el repositorio de GitHub (Opcional). | **I1 o I3**: "En conclusión, el Electoral Integrity Analyzer demuestra que al combinar reglas lógicas de negocio, estadística predictiva y auditoría criptográfica en un diseño centrado en la usabilidad, podemos proveer a los analistas de una herramienta poderosa para proteger la integridad de la información crítica. Muchas gracias por su atención." |

---

## 💡 Consejos de Grabación
1. **Practiquen la navegación**: Quien comparta pantalla debe saber exactamente dónde hacer clic antes de que el compañero empiece a hablar.
2. **Usen el botón de "Regenerar datasets"**: Si graban el video varias veces y ya tienen los datos generados, recuerden usar el botón "Regenerar datasets" antes de empezar a grabar para poder mostrar el proceso de carga automático.
3. **Hagan pausas**: Si algo carga, usen ese tiempo para explicar qué está haciendo el sistema "por debajo" (ej. "En este momento el algoritmo está calculando las desviaciones estándar...").
