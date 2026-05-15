# Guion de Video: Electoral Integrity Analyzer

**Duración objetivo:** 6–7 minutos | **Máximo:** 8 minutos  
**Ritmo de habla:** 130–150 palabras por minuto — ensáyenlo con cronómetro antes de grabar

| Integrante | Parte |
|---|---|
| I1 | Apertura, threat model, datos y arquitectura, cierre |
| I2 | Técnicas de detección |
| I3 | Controles de ciberseguridad, resultados y métricas |

---

## Acto 1 — Apertura y threat model (~1 min 15 seg)

*Pantalla: título del sistema + advertencia ética*

**I1:** "¿Cómo sabe un auditor que los resultados de una elección no fueron alterados? No cuando ya están publicados — sino en cada paso: desde que un ciudadano aparece en el padrón, hasta que el acta queda firmada y archivada.

Somos [Nombres]. Presentamos Electoral Integrity Analyzer: una herramienta de auditoría forense sobre datos electorales sintéticos, diseñada para detectar anomalías usando principios de ciberseguridad. El enfoque no es construir un sistema de votación — es modelar los controles que permiten auditar uno.

*Pantalla: diagrama de las seis etapas*

El punto de partida de cualquier sistema de seguridad es el modelo de amenazas: el ejercicio de identificar qué puede salir mal, quién podría provocarlo, y en qué punto del proceso. En un proceso electoral, identificamos seis etapas con sus propios vectores de ataque: el padrón de votantes, la asignación de mesas, el registro del sufragio, el escrutinio manual, los resultados por mesa, y los logs del sistema.

¿Por qué seis etapas y no solo los resultados finales? Porque el fraude rara vez ocurre solo en los números del final. Ocurre antes: en un padrón con registros de personas fallecidas que aparecen votando, en un doble voto que no se detecta en el check-in, en un operador que clasifica boletas con sesgo sistemático. Si solo auditamos resultados, llegamos tarde.

Los controles tienen que estar en cada capa del proceso — lo que en ciberseguridad llamamos defensa en profundidad: múltiples barreras de detección para que comprometer una sola no sea suficiente para que el fraude pase desapercibido."

---

## Acto 2 — Datos y arquitectura (~1 min 15 seg)

*Pantalla: sección "Cargar / generar datasets" en la UI*

**I1:** "Generamos nueve conjuntos de datos con un script de Python, usando una semilla aleatoria fija: RANDOM_SEED igual a 42. Eso garantiza que los datos sean exactamente los mismos en cada ejecución.

¿Por qué datos sintéticos y no datos reales? Seguimos el principio de Privacy by Design: la protección de datos personales no es un parche al final, sino una decisión de arquitectura desde el inicio. No procesamos ningún dato personal real — no hay riesgo de fuga de información, no hay exposición de datos privados de ciudadanos.

¿Y por qué semilla fija? Porque en auditoría forense, una herramienta que produce resultados distintos en cada ejecución no puede usarse como evidencia. Con semilla fija, cualquier tercero ejecuta el mismo análisis y obtiene los mismos hallazgos. Eso es reproducibilidad auditable: misma entrada, mismo resultado.

*Pantalla: diagrama de capas de la arquitectura*

La arquitectura es un monolito modular por capas: la interfaz de usuario no contiene lógica de detección. Los detectores no conocen la interfaz. La carga de datos no mezcla validación con análisis.

¿Por qué esta separación? Porque en seguridad, la responsabilidad única no es solo una buena práctica de software — es un control. Si la lógica de detección viviera en la interfaz, un cambio visual podría alterar inadvertidamente una regla de detección. Con capas separadas, los cambios son localizables y trazables: si falla la detección, sabemos exactamente dónde buscar.

Además, la capa de validación opera como fail-secure: si los datos de entrada no pasan la validación de esquema, el sistema bloquea el análisis. No genera alertas basadas en datos corruptos. En seguridad, un sistema que falla silenciosamente con datos inválidos es más peligroso que uno que rechaza la entrada y detiene el proceso."

---

## Acto 3 — Técnicas de detección (~1 min 45 seg)

*Pantalla: tabla de alertas del EligibilityDetector o ResultsDetector*

**I2:** "Implementamos exactamente dos técnicas de detección: reglas determinísticas y Z-score. Las elegimos deliberadamente, y voy a explicar qué es cada una y por qué.

Una regla determinística es una condición binaria: o se cumple o no se cumple, sin grados intermedios. La usamos cuando la anomalía es absoluta, no relativa. Si una persona tiene fecha de defunción anterior a la elección y aparece con voto registrado, eso no es un outlier estadístico — es una violación lógica. No existe ningún umbral que lo haga aceptable. Lo mismo aplica a una participación mayor al cien por ciento, o a una suma de votos que no cuadra con el total reportado. Usar estadística aquí solo introduciría falsos negativos innecesarios: casos reales de fraude que el sistema no marcaría porque 'estadísticamente no son tan raros'.

*Pantalla: histograma de participación por mesa*

Para variables donde la anomalía es relativa al contexto, usamos Z-score. El Z-score es una medida estadística que indica cuántas desviaciones estándar se aleja un valor respecto al promedio del grupo — en términos simples: qué tan raro es ese valor dentro del conjunto. Una participación del noventa y dos por ciento no es necesariamente fraude: depende de si esa mesa se comporta igual que las demás o se aleja significativamente de ellas. El Z-score mide exactamente eso.

Usamos un umbral de Z mayor o igual a tres. ¿Por qué tres y no dos? Con umbral dos, aproximadamente el cinco por ciento de las mesas quedarían marcadas solo por variabilidad estadística normal — demasiado ruido, y eso diluye los hallazgos reales. Con umbral tres, estamos en el cero punto veintisiete por ciento de la distribución: los extremos genuinos. Es la regla de las tres sigmas, estándar en control estadístico de calidad, con respaldo bibliográfico y sin necesidad de calibración arbitraria por dominio.

¿Por qué no clustering ni modelos de machine learning, si el enunciado lo permitía? Porque en auditoría electoral, los hallazgos tienen que ser explicables. Un auditor puede presentar ante una comisión electoral: 'este valor está a 4.2 desviaciones estándar sobre la media'. No puede presentar: 'el modelo lo marcó como anómalo porque cayó fuera de su cluster de densidad variable'. En contextos forenses, la explicabilidad no es una preferencia estética — es un requisito."

---

## Acto 4 — Controles de ciberseguridad (~2 min)

*Pantalla: sección "Logs e integridad" → tabla de alertas*

**I3:** "Esta etapa concentra el mayor diseño de seguridad del sistema. Implementamos cuatro controles — cada uno responde a un vector de ataque concreto.

*Pantalla: filtrar alertas LOG-02*

El primer control es RBAC: Control de Acceso Basado en Roles. Define qué operaciones puede ejecutar cada tipo de usuario según su función en el proceso electoral. Detectamos acciones realizadas por usuarios fuera de las operaciones permitidas para su rol. ¿Por qué RBAC? Porque el principio de mínimo privilegio establece que cada actor debe tener acceso únicamente a lo que necesita para su función. Si un jurado de mesa puede modificar resultados de otras mesas, el sistema de permisos está comprometido. RBAC es el control estándar definido en NIST SP 800-162, y aquí lo modelamos como una matriz de roles versus acciones permitidas.

*Pantalla: filtrar alertas LOG-06*

El segundo control es Segregación de Funciones. Detectamos casos donde el mismo usuario que realizó un cambio también lo aprobó. ¿Por qué es un control? Porque si quien modifica también aprueba, basta con comprometer una sola cuenta para falsificar evidencia sin dejar rastro de colusión. Con segregación de funciones se requieren al menos dos actores comprometidos — eso eleva el costo del ataque y aumenta la superficie de detección.

*Pantalla: filtrar alertas INT-01*

El tercer control es integridad por hash criptográfico. Un hash es una función matemática que produce una huella digital única de un documento: si el contenido cambia aunque sea un carácter, el hash cambia completamente. Comparamos el hash original de cada acta contra su hash actual. Si difieren sin un evento de modificación autorizado, es una señal de alteración no autorizada. ¿Por qué hashes? Porque en auditoría electoral, las actas firmadas son evidencia legal. La integridad criptográfica es el único mecanismo que permite demostrar objetivamente que un documento no fue alterado después de su firma. Modelamos el algoritmo SHA-256, recomendado por el estándar NIST FIPS 180-4.

*Pantalla: filtrar alertas LOG-01*

El cuarto control es inmutabilidad post-cierre. Detectamos eventos registrados después del horario de cierre electoral configurado en el sistema. ¿Por qué es crítico? Porque en un proceso electoral, la ventana de modificación legítima se cierra cuando termina la jornada. Cualquier cambio posterior requiere justificación formal y aprobación explícita. Un cambio tardío sin esa justificación es una señal de manipulación — uno de los vectores más documentados en fraudes electorales reales."

---

## Acto 5 — Resultados y métricas (~50 seg)

*Pantalla: ranking de riesgo ponderado*

**I3:** "El sistema consolida todas las alertas en un ranking de riesgo ponderado. Cada alerta tiene un peso según su severidad: crítica vale tres puntos, alta vale dos, media vale uno. Las entidades con score mayor a doce se marcan como revisión prioritaria, y ese umbral es configurable.

*Pantalla: métricas de evaluación contra el ground truth*

Para medir qué tan bien funciona el sistema, lo comparamos contra un ground truth: el conjunto de anomalías que nosotros inyectamos al generar los datos sintéticos, y que conocemos con certeza. Usamos dos métricas estándar. La precisión indica, de todas las alertas que generó el sistema, qué porcentaje corresponde a anomalías reales. La cobertura indica, de todas las anomalías reales que existen, qué porcentaje logró detectar el sistema.

Obtuvimos precisión del sesenta y siete por ciento y cobertura del sesenta y seis por ciento. ¿Por qué no más? El Z-score puede marcar mesas que no están en el ground truth pero sí son outliers estadísticos genuinos. Eso genera falsos positivos — alertas sobre mesas que en realidad no tienen fraude. Pero en auditoría, el costo de un falso negativo, pasar por alto una mesa con fraude real, es mayor que el costo de un falso positivo, revisar una mesa que resulta limpia. El sistema está calibrado deliberadamente para no perder anomalías reales, a costa de marcar algunas adicionales para revisión humana.

La evidencia se exporta en CSV: formato neutral, legible sin software propietario, que cualquier auditor puede importar. Eso sigue las guías del EAC para auditorías post-electorales."

---

## Acto 6 — Cierre (~20 seg)

*Pantalla: advertencia ética del sistema*

**I1:** "Este proyecto no busca probar fraude real. Busca demostrar cómo se modela un sistema de auditoría defensivo: con datos validados, pipeline trazable, reglas explicables, estadística transparente, y controles de acceso e integridad sobre los registros del sistema.

Un sistema de auditoría confiable no es el que detecta todo — es el que puede justificar cada hallazgo. Todos los datos son sintéticos. Las alertas son señales de revisión, no conclusiones. Gracias."

---

## Preguntas del evaluador — preparación oral (no se graba)

**"¿Por qué no usaron clustering o Isolation Forest si el enunciado lo permitía?"**

> Lo descartamos conscientemente. Isolation Forest y clustering no ofrecen interpretabilidad directa. Un auditor necesita poder explicar ante una comisión por qué una mesa fue marcada. "Este valor está a 4.2 desviaciones estándar sobre la media" es un argumento defendible. "El algoritmo lo clasificó porque cayó fuera de su cluster" no lo es. En ciberseguridad forense, la explicabilidad no es opcional.

---

**"¿Por qué Z = 3 y no Z = 2 o Z = 2.5?"**

> Con Z = 2 marcamos el cinco por ciento de las mesas solo por variabilidad estadística normal — demasiado ruido. Con Z = 3 estamos en el cero punto veintisiete por ciento de la distribución: los extremos genuinos. Es el umbral de la regla de las tres sigmas, estándar en control estadístico de procesos, con respaldo bibliográfico y sin calibración arbitraria.

---

**"¿Qué pasa si el dataset tiene pocos registros? ¿El Z-score sigue siendo válido?"**

> Con n pequeño, el Z-score tiene menos potencia estadística. Nuestro código maneja explícitamente el caso de baja varianza: si la desviación estándar es cero, retorna ceros en lugar de dividir por cero. Para muestras pequeñas, el sistema señala pero no afirma certeza estadística. Un analista debería complementar con revisión manual.

---

**"Los hashes en el dataset, ¿son hashes SHA-256 reales?"**

> No, son valores simulados que representan el concepto. Modelamos el control de integridad criptográfica sin implementar PKI ni firma real, porque eso requeriría infraestructura de clave pública fuera del alcance académico. El valor está en demostrar que el control existe y que el detector lo verifica: si hash_original es diferente de hash_actual, hay una señal de alteración.

---

**"¿Por qué RBAC y no ABAC?"**

> En un proceso electoral los roles son finitos y bien definidos: jurado, administrador, auditor, operador. ABAC requiere definir políticas sobre atributos dinámicos, lo que introduce más superficie de error de configuración. RBAC con mínimo privilegio y segregación de funciones cubre los vectores relevantes con un modelo más simple y verificable.

---

**"¿Cómo saben que el ground truth es correcto?"**

> Lo generamos nosotros al inyectar las anomalías. Sabemos exactamente qué pusimos porque nosotros lo hicimos. Por eso las métricas son "aproximadas": no evaluamos contra datos reales, sino que verificamos que el sistema detecta lo que fue diseñado para detectar. En un sistema real, el ground truth vendría de auditorías manuales certificadas.

---

**"¿Por qué bloquean el análisis si falla la validación en lugar de continuar con advertencias?"**

> Fail-secure. Si procesamos datos con columnas faltantes o tipos incorrectos, el detector puede generar alertas basadas en valores nulos — eso produce falsa confianza, que es peor que no ejecutar. En seguridad, validar antes de procesar es el mismo principio que la sanitización de entradas en OWASP: validas primero, procesas después.
