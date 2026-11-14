# Demostración de cinco minutos

Antes: seguir README, comprobar STT/TTS e idiomas. La prueba física de micrófono se interrumpió: realizarla con voluntario antes de afirmar ese tramo comprobado. No guardar habla privada. No presentar WAV pregrabado como generación en vivo.

0:00–0:35. Presentar prototipo, motor determinista, conversación de lectura, sin diagnóstico firmado ni terapia. Dos astronautas sintéticos/54 días; fuentes y hashes.

0:35–1:20. Astronauta A, día 35 (5/9/2026), Asistente → Ciclo de vigilancia. Mostrar baseline/tendencia. English, pulsar Hablar: «VIGILE, how has my physical condition changed during the mission?». Terminar; revisar/editar transcript y enviar manualmente. Mostrar generación separada de evidencia; pulsar reproducir/detener. Si falla captura, declarar fallo y usar texto o harness WAV explícitamente sintético.

1:20–2:15. B, día 18 (19/8/2026 07:00 PET): «VIGILE, why am I receiving this medical alert?». Banner DKA persistente, criterios/urgencia/confirmación separados y protocolo bloqueado. TTS sólo del texto validado visible; sin prescripción.

2:15–2:55. «What information is missing from my evaluation?». Mostrar alternativas bicarbonato/cetonas urinarias no bloqueantes y potasio pendiente para seguridad. Ausente no significa normal.

2:55–3:35. B, día 18p1 (19/8 09:24 PET), Español: «¿Qué cambió desde mi última evaluación?». Corregir transcript antes de enviar. Comparación respaldada/nuevo potasio y bloqueos conservados; previo no se etiqueta baseline.

3:35–4:20. FULL→LOW_POWER→CRITICAL. Sin inferencia en CRITICAL, motor conservado; voz sólo si disponible. No afirmar ahorro energético. Para caída Ollama usar harness que conecta sólo su adaptador a un puerto cerrado; no parar servicio real. Mostrar OUTAGE/RESTORED y WAV SAPI identificados como grabaciones cuando ya fueron generados.

4:20–5:00. Replay, fuentes y hashes. WER sintético EN11.1%/ES24.7% y errores médicos; revisión humana pendiente. SQLite sin cifrar/misma cuenta sin aislamiento/terapias bloqueadas. 633 tests no son validación clínica/espacial.

## Checklist físico pendiente

Voluntario EN/ES: permiso concedido/denegado, micrófono desconectado, grabar/terminar/cancelar, edición/envío por teclado, cambio de sujeto/idioma/modo durante captura, ocultar/salir. Comprobar indicador de micrófono apagado. Escuchar números/unidades/negaciones/restricciones en altavoz/auriculares. Medir fin captura→STT→respuesta→TTS→playback con panel, separando demoras humanas. No conservar audio por defecto. No dar por completado con mocks Node.

Capturas reales screenshots/: DKA con banner/transcript editable y diseño estrecho sin overflow de página. El texto del transcript de la captura se escribió manualmente, no vino de un micrófono. La captura estrecha no sustituye auditoría exhaustiva de accesibilidad.