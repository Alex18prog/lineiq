# LineIQ

🇬🇧 [English](README.md) · 🇪🇸 Español

**Análisis de eficiencia de producción (OEE) para líneas de fabricación — construido con Python, pandas y Streamlit.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-data%20analysis-150458?logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)
![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC?logo=pytest&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**[▶ Demo en vivo](https://lineiq-oee.streamlit.app/)**
*(hosting de nivel gratuito — puede tardar unos segundos en despertar si lleva un rato inactivo)*

## Qué es esto

El OEE es la métrica estándar de la industria manufacturera para medir cuánto de la capacidad teórica de una línea se convierte realmente en producto bueno: `Disponibilidad × Rendimiento × Calidad`. LineIQ genera un registro de producción sintético pero realista (3 líneas, 3 turnos/día, 30 días, con eventos de parada y tasas de defectos que varían deliberadamente según la línea) y lo convierte en un dashboard interactivo: OEE global, tendencia en el tiempo, comparativa entre líneas y turnos, y un desglose Pareto de *por qué* se está perdiendo tiempo — la clásica vista de las "seis grandes pérdidas" que se usa en plantas de producción reales.

## Por qué este proyecto

- **Una métrica industrial real y estándar** — el OEE no me lo he inventado; es lo que ya monitorizan los responsables de planta. Un dashboard construido alrededor de esta métrica es legible al instante para cualquiera del sector manufacturero, no solo para desarrolladores.
- **La herramienta correcta para el dominio** — Python + pandas es con lo que realmente se construye este tipo de análisis en la industria, no un lenguaje elegido por consistencia de portfolio.
- **Lógica de negocio testeada de forma aislada** — `oee.py` no depende del framework del dashboard y está cubierto por 12 tests unitarios, incluyendo uno que protege específicamente contra un patrón de bug real (promediar ingenuamente los porcentajes de OEE por turno en vez de ponderar por tiempo de producción).
- **El dashboard en sí también está testeado** — `tests/test_app_smoke.py` usa el framework oficial `AppTest` de Streamlit para ejecutar la app completa sin interfaz gráfica y comprobar que renderiza sin excepciones, no solo que los cálculos son correctos.

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `oee.py` | El cálculo de OEE — `availability()`, `performance()`, `quality()`, `oee()`, más `weighted_average_oee()` para agregar correctamente turnos de distinta duración |
| `data_generator.py` | Generador de datos de producción sintéticos (semilla aleatoria fija, para que el demo sea reproducible) |
| `app.py` | El dashboard de Streamlit: tarjetas de KPI, gráfico de tendencia, comparativa por línea/turno, Pareto de paradas |
| `tests/test_oee.py` | Tests unitarios de la lógica de cálculo, con valores esperados comprobables a mano |
| `tests/test_app_smoke.py` | Tests de humo sin interfaz gráfica para el propio dashboard |

## Los tres factores, en breve

- **Disponibilidad** = Tiempo en marcha ÷ Tiempo de producción planificado — ¿estuvimos funcionando de verdad, o parados (avería, cambio de formato, falta de material...)?
- **Rendimiento** = Producción real ÷ Producción máxima teórica mientras funcionábamos — mientras funcionábamos, ¿íbamos a velocidad completa o más lento que el ciclo nominal?
- **Calidad** = Piezas buenas ÷ Piezas totales producidas — de lo que hicimos, ¿cuánto era realmente vendible?

Multiplicar los tres factores es deliberadamente severo: una línea disponible el 90% del tiempo, funcionando al 90% de velocidad, y produciendo un 90% de piezas buenas, no tiene un OEE del 90% — tiene 90%×90%×90% ≈ 73%. Ese efecto de composición es la razón de ser de la métrica, y por qué pérdidas "pequeñas" en tres sitios distintos se suman en una brecha total mucho mayor de lo que parece cada una por separado.

## Ponerlo en marcha en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. Los datos se generan al cargar con una semilla fija (`RNG_SEED = 42` en `data_generator.py`) — cada ejecución muestra los mismos números, así que el dashboard es reproducible sin necesitar una base de datos real.

### Ejecutar los tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap / posibles extensiones

- [x] Desplegar en Streamlit Community Cloud (enlazado arriba)
- [ ] Permitir que el usuario suba su propio CSV en vez de usar solo datos sintéticos
- [ ] Añadir una previsión simple (media móvil o tendencia lineal) de hacia dónde va el OEE la semana que viene
- [ ] Exportar un informe de turno en PDF/Excel

## Licencia

MIT — haz lo que quieras con esto, es un proyecto de portfolio.
