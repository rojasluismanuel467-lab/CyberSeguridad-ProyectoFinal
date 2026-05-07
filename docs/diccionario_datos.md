# Diccionario de Datos

## 01_padron_votantes.csv
- **Descripción**: padrón electoral simulado.
- **Claves**: `voter_id`.
- **Columnas**: `voter_id`, `documento_hash`, `fecha_nacimiento`, `edad`, `fecha_defuncion`, `estado_documento`, `condicion_legal`, `habilitado_legalmente`, `estado_padron`, `municipio`, `zona_id`, `circunscripcion_autorizada`, `mesa_asignada`.
- **Anomalías relacionadas**: PAD-01..PAD-06.

## 02_asignacion_mesas.csv
- **Descripción**: asignación de mesa/puesto/zona/circunscripción por votante.
- **Claves**: `voter_id`.
- **Columnas**: `voter_id`, `mesa_asignada`, `puesto_asignado`, `zona_asignada`, `municipio_asignado`, `circunscripcion_autorizada`, `tipo_boleta_autorizada`, `puede_votar_en_otro_puesto`, `justificacion_excepcion`.
- **Anomalías relacionadas**: CIR-01..CIR-03.

## 03_registro_sufragio.csv
- **Descripción**: registros de check-in/sufragio durante jornada.
- **Claves**: `suffrage_id`.
- **Columnas**: `suffrage_id`, `voter_id`, `fecha_eleccion`, `voto_registrado`, `mesa_voto`, `puesto_voto`, `zona_voto`, `municipio_voto`, `circunscripcion_voto`, `hora_checkin`, `metodo_checkin`, `operador_checkin`.
- **Anomalías relacionadas**: SUF-01..SUF-04, CIR-01, CIR-02.

## 04_clasificacion_votos_manual.csv
- **Descripción**: clasificación manual simulada de votos.
- **Claves**: `ballot_id`.
- **Columnas**: `ballot_id`, `mesa_id`, `voter_id`, `marca_simulada`, `clasificacion_objetiva`, `clasificacion_jurado`, `clasificacion_auditoria`, `usuario_clasificador`.
- **Anomalías relacionadas**: MAN-01..MAN-04.

## 05_resultados_mesa.csv
- **Descripción**: consolidado de resultados por mesa.
- **Claves**: `mesa_id`.
- **Columnas**: `mesa_id`, `municipio`, `zona_id`, `circunscripcion`, `electores_habilitados`, `sufragantes_registrados`, `votos_candidato_A`, `votos_candidato_B`, `votos_candidato_C`, `votos_blancos`, `votos_nulos`, `votos_invalidos`, `total_calculado`, `total_reportado`, `participacion_pct`, `ganador`, `concentracion_ganador_pct`, `margen_victoria_pct`.
- **Anomalías relacionadas**: RES-01..RES-06.

## 06_logs_eventos.csv
- **Descripción**: trazabilidad de acciones y eventos de seguridad.
- **Claves**: `evento_id`.
- **Columnas**: `evento_id`, `timestamp`, `usuario_id`, `rol_usuario`, `accion`, `recurso`, `mesa_id`, `zona_id`, `resultado_accion`, `ip_origen`, `requiere_aprobacion`, `aprobado_por`, `hash_antes`, `hash_despues`.
- **Anomalías relacionadas**: LOG-01..LOG-06.

## 07_integridad_archivos.csv
- **Descripción**: estado de integridad de archivos publicados.
- **Claves**: `archivo_id`.
- **Columnas**: `archivo_id`, `tipo_archivo`, `mesa_id`, `version`, `hash_original`, `hash_actual`, `timestamp_firma`, `timestamp_publicacion`, `usuario_publicador`, `estado_integridad`, `reporte_firmado_total`, `reporte_publicado_total`.
- **Anomalías relacionadas**: INT-01..INT-04.

## 08_alertas_esperadas.csv
- **Descripción**: ground truth sintético de anomalías inyectadas.
- **Claves**: `alerta_id`.
- **Columnas**: `alerta_id`, `codigo_alerta`, `entidad_tipo`, `entidad_id`, `dataset_origen`, `severidad`, `descripcion`.

## usuarios_sistema.csv
- **Descripción**: usuarios y permisos simulados.
- **Claves**: `usuario_id`.
- **Columnas**: `usuario_id`, `nombre_usuario`, `rol`, `estado_usuario`, `zona_asignada`, `mesa_asignada`, `puede_modificar_padron`, `puede_registrar_sufragio`, `puede_clasificar_votos`, `puede_modificar_resultados`, `puede_aprobar_cambios`, `puede_ver_logs`, `requiere_mfa`.
