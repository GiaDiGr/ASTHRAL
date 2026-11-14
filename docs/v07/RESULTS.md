# Resultados reales v0.7.0

Fecha de entrega: 21-10-2026, America/Lima. Fuentes nuevas verificadas el 20-10-2026.

- Suite: 490 aprobadas; 0 fallos; 0 errores; 97.36 s.
- Demostración API: 15 ciclos, 15 reproducciones coincidentes, reader lectura autorizada/escritura denegada.
- Latencia de POST en TestClient: mediana 47.41 ms; rango 34.00–191.66 ms. SQLite 3133440 bytes. Carga concurrente de pytest; no benchmark de vuelo.
- HTTP real: 15 ciclos y 20 evaluaciones clínicas reproducidas; aislamiento de ámbitos y auditoría comprobados.
- Ollama: `vigile-qwen3-4b:latest`, inferencia ANSWERED, 9.61 s en la consulta registrada. Sin cambio de configuración.
- Corpus original: 105 archivos científicos y 8 JSON clínicos intactos.
- SHA256 implementación: `d4d5475981df7b1874c511f3ed51678ecf7d19b44997f6fee92cf275da3bd321`.
- SHA256 conocimiento clínico: `b8c568bd645154e5fd67630c7a670ca53904dc04f54904315047a89923839d4e`.

Ver JSON y XML adjuntos para resultados completos. La captura `dashboard.png` verifica la sección de vigilancia experimental en el portal. Las pruebas no constituyen validación clínica.
