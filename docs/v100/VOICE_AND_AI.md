# Voz, LLM y RAG: resultados reales y límites

## Selección y licencias

No había modelos/paquetes STT instalados. Se revisó documentación oficial de Vosk, faster-whisper/whisper.cpp y Piper; no se inventó una comparación empírica entre motores. Se eligió Vosk pequeño EN 0.15 / ES 0.42, API 0.3.45, CPU y licencia Apache-2.0; se anunciaron modelo/tamaño/licencia antes de descargar. [Modelos oficiales](https://alphacephei.com/vosk/models), [licencia API](https://github.com/alphacep/vosk-api/blob/master/COPYING). voice-model-downloads.json y voice_assets/models.json fijan URL/bytes/hashes; no son firma del fabricante. Setup explícito, nunca descarga en runtime.

[faster-whisper](https://github.com/SYSTRAN/faster-whisper) requiere runtime/modelos adicionales; no se instaló ni midió otra alternativa. [Piper](https://github.com/OHF-Voice/piper1-gpl) ofrece TTS neural local y requiere revisar licencias del motor y de cada voz. Se reutilizó [System.Speech](https://learn.microsoft.com/en-us/dotnet/api/system.speech.synthesis.speechsynthesizer?view=netframework-4.8.1) con David Desktop EN y Helena Desktop ES ya presentes. No usa Web Speech/cloud. Windows/vozes propietarios no se redistribuyen; naturalidad no puntuada por humanos. Ollama/Qwen permanecen existentes; pesos no incluidos y condiciones originales deben revisarse antes de redistribuir.

## STT/TTS reales

32 referencias redactadas ANTES de predecir (16 EN + 16 ES), sintetizadas por SAPI local, no habla clínica humana. Corpus WER EN 11.11% (12/16 exactas), ES 24.66% (8/16). Orthostatic hypotension, microgravedad y cetoacidosis mostraron errores importantes. Confianza Vosk no es tasa de exactitud ni garantía médica. Cero flags de negación en este corpus no garantiza significado correcto.

Medianas STT EN 2.093 s / ES 0.898 s; TTS EN 0.742 s / ES 0.811 s. Audios de referencias 1.425–4.695 s EN y 1.55–4.87 s ES; resúmenes clínicos TTS son más largos. Cargas frías/calientes/idioma en resultados por frase. Archivos ZIP: 81,023,764 bytes; modelos expandidos: 131,185,565. Sólo un idioma STT en caché; no garantía de liberar toda memoria nativa. CPU benchmark 54.938 s; muestra final working set 168,284,160 bytes, privada 570,093,568. VRAM GLOBAL antes/después 3948 MiB, no atribuible exclusivamente a voz; Vosk/SAPI CPU. Sin medición de potencia.

Vacío/corrupto/silencio rechazados. Ruido blanco produjo «huh» y audio en idioma incorrecto una frase espuria. No hay detector fiable de todo ruido/idioma erróneo; SIEMPRE transcript editable y envío manual. Denegación/desconexión/cancelación/carreras se probaron con simulación Node, no hardware físico.

## Circuito y modos

Nueve escenarios en e2e-r2/results.json: WAV→Vosk→revisión explícita de referencia→asistente real o fallback→SAPI, EN/ES, FULL/LOW_POWER/CRITICAL, conexión rechazada loopback del adaptador y recuperación. No se paró/reconfiguró Ollama para el fallo. CRITICAL/OUTAGE: cero solicitudes de generación; resultados clínicos invariantes y 76 replays coincidentes.

«Fin de captura de referencia→WAV listo» NO mide micrófono/espera humana/altavoz. UI instrumenta fin de grabación, STT, envío, respuesta, síntesis e inicio de playback incluyendo esperas voluntarias. En navegador se observó síntesis 0.87 s / solicitud→reproducción 0.93 s antes de interrumpir prueba de micrófono; no se puntuó calidad perceptual. Captura física sigue pendiente.

Voz CPU usa mismo perfil en FULL/LOW_POWER: no ahorro energético demostrado. LOW_POWER reduce contexto/hilos/tokens LLM según política previa, pero aquí no fue más rápido. CRITICAL no infiere; voz sólo si disponible/admitida por recursos. 512 MiB libres es umbral TÉCNICO, no clínico. Falta de voz conserva texto; falta de LLM conserva motor.

## Explicación y recuperación

Hechos Pydantic con original/display (HALF_EVEN 3 decimales sólo visual), unidad, evidencia, mediciones, sujeto/misión/objetivo/fecha del ciclo/hashes. Comparación previa nunca se etiqueta baseline. Qwen genera lenguaje controlado que se verifica determinísticamente por variable/valor/unidad/rol/negación, sin juicio del propio modelo. Fechas/contexto añadidos por motor. Criterios/urgencia/confirmación/faltantes/protocolo/tratamiento permanecen texto determinista; rechazos nunca pasan a TTS.

BM25 bilingüe local comprueba hashes/offsets/autoridad antes de ranking; mantiene números/negaciones, encabezados y diversidad. Diferencia primario/síntesis/contrato. Qrels públicos originales: top3 4/12→10/12, top5 8/12→11/12. Adicionales no usados para ajustar: 4/8 y 6/8. Pertinencia etiquetada por desarrollador, no revisión clínica independiente.

Banco reservado R1 UNA ejecución tras congelación: 12 respuestas, 5 con generación aceptada, 0 errores de ejecución. Aceptación NO equivale a pertinencia/validez. Casos 02/05 devolvieron hechos insuficientes para la pregunta; 09 no rechazó explícitamente «otro astronauta» aunque sólo devolvió datos propios; 11 no calculó riesgo vital pero tampoco explicitó falta de capacidad. R2 añade guardas/lectura determinista; no se reejecutó el banco ni se considera inédito. Nuevas regresiones están contaminadas como evaluación de desarrollo. Todas las respuestas/raw/tiempos se conservan.