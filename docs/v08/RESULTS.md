# Resultados finales v0.8.0

Fecha: 21-10-2026, America/Lima. Solo datos sintéticos.

- Suite completa: **522 aprobadas**, 0 fallos, 0 errores, 0 omitidas; 74.86 s en JUnit. Una advertencia de deprecación Starlette/httpx.
- Incremento respecto a v0.7: 32 pruebas (8 biomédicas y 24 IA/integración).
- HTTP real: **15 ciclos y 20 evaluaciones reproducidas**. Registros persistidos sin modificaciones por lectura; auditoría válida; reader sin escritura ni acceso fuera de ámbito.
- Estados clínicos de los escenarios v0.7 y v0.8 coincidentes. Fuentes originales intactas: 105 archivos científicos y 8 JSON clínicos.
- Corpus RAG: 560 fragmentos literales de 6 archivos; no implica disponer del texto íntegro de todas las referencias citadas.
- Portal clínico anterior: respuesta real de Ollama `ANSWERED` en 4.91 s en la comprobación final. Las consultas de faltantes permanecen deterministas en los tres modos.

## Banco real final

| Modo | Expectativas cumplidas | Documento esperado top-5 | Llamadas a capa conversacional | Generaciones aceptadas | Fallbacks extractivos | Rechazos correctos de acción |
|---|---:|---:|---:|---:|---:|---:|
| FULL | 16/16 | 6/6 | 9 | 4 | 4 | 4 |
| LOW_POWER | 16/16 | 6/6 | 9 | 2 | 6 | 4 |
| CRITICAL | 16/16 | 6/6 | 0 | 0 | 0 | 4 |

Cada modo ejecutó las mismas 16 preguntas. El motor/extractos siguen disponibles cuando la generación se rechaza. Las llamadas a la capa conversacional pueden detenerse antes de invocar Ollama; ver `inference_executed` y motivos en cada respuesta. El caso de hipoglucemia reportó falta de contexto relevante en la capa de generación aunque conservó los bloques deterministas: pendiente mejorar selección de contexto, sin inventar información. CRITICAL no intentó inferencia.

Los recuentos no miden fiabilidad clínica ni errores semánticos no detectados. Las expectativas son de desarrollo y no un conjunto ciego independiente. Los fallbacks no son un recuento de alucinaciones. Consultar `bank-summary.json` y los JSON completos para estados, referencias y latencias.

## Incidencias e historial

Las corridas preliminares se conservan como tales. Se detectó y corrigió un falso rechazo de consulta radiológica y se fortaleció el check para preguntas legítimas. Dos intentos iniciales sufrieron desconexión HTTP; su causa no está demostrada. Las repeticiones finales completaron los checks. No se cambió Norton ni se atribuye el problema a sus protecciones.

## Reproducibilidad y límites

- Implementación final SHA256: `fb940e6f35764a3b060665269a4272f80038f724a830c0ac1e0441e89fdb15dd`.
- Conocimiento clínico SHA256: `b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e`.
- Demostración final: `engine/data/portal-v080-final`; anteriores preservadas.
- `change-manifest.json` incluye archivos y dependencias exactas; `source-inventory.json` fija corpus.
- SQLite sin cifrado; auditoría susceptible de reconstrucción por atacante que controle almacenamiento; aislamiento de procesos pendiente.
- No validación clínica, espacial, energética ni operativa. No terapias habilitadas.

## Comprobación adversarial adicional

Ollama real en FULL, loopback: **3/3 checks** sobre fuente ausente, documento contradictorio e inyección documental. Resultados en `bank-adversarial-real.json`. Son fixtures inyectados en la capa de biblioteca, no documentos incorporados al corpus ni una auditoría exhaustiva de ataques.
