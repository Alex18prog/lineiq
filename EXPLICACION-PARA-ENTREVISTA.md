# LineIQ — Guía para entenderlo y explicarlo en una entrevista

Este documento es para ti, no para el repositorio de GitHub (ese README ya
está en inglés, orientado al reclutador que lo lee por encima). Este es para
que te prepares y puedas hablar de LineIQ con soltura, aunque hayas
empezado en Python casi desde cero.

---

## 1. Qué es esto, en una frase

**LineIQ es un dashboard que calcula y visualiza el OEE (eficiencia de
producción) de varias líneas de fabricación, a partir de datos de
producción — turnos, paradas, piezas buenas/defectuosas.**

Si alguien te pregunta "¿qué hace tu proyecto?", esa frase es tu punto de
partida. Luego puedes profundizar según lo que te pregunten.

---

## 2. El concepto de negocio: qué es OEE y por qué importa

OEE (Overall Equipment Effectiveness / Eficiencia General del Equipo) es
**la métrica estándar de la industria manufacturera** para medir qué
porcentaje de la capacidad teórica de una línea se convierte realmente en
producto bueno. La usan de verdad fábricas reales — no es una métrica que
me haya inventado para el proyecto.

Se calcula multiplicando tres factores, cada uno respondiendo una pregunta
distinta:

| Factor | Pregunta que responde | Fórmula |
|---|---|---|
| **Disponibilidad** | ¿Estuvimos parados o funcionando? | Tiempo en marcha ÷ Tiempo planificado |
| **Rendimiento** | Mientras funcionábamos, ¿íbamos a velocidad completa? | Producción real ÷ Producción teórica máxima |
| **Calidad** | De lo que hicimos, ¿cuánto era vendible? | Piezas buenas ÷ Piezas totales |

**El detalle que más impresiona si lo explicas bien**: multiplicar los tres
factores es *intencionadamente castigador*. Si tienes 90% de disponibilidad,
90% de rendimiento y 90% de calidad, tu OEE no es 90% — es 0.9 × 0.9 × 0.9
≈ **73%**. Tres pérdidas "pequeñas" en sitios distintos se combinan en una
pérdida grande. Esa es la razón de ser de la métrica: obliga a mirar los
tres frentes a la vez, no solo el más visible.

Valores de referencia que puedes citar de memoria:
- **85% OEE** → el benchmark de "clase mundial" citado habitualmente en el sector
- **60%** → una fábrica media/típica
- **Por debajo del 40%** → normalmente hay un problema real detrás

En mis datos sintéticos, el OEE global sale en torno al **78%**, con una
línea (Line C) deliberadamente peor (~73%) que las otras dos (~80-81%) —
lo hice así a propósito para que el dashboard tuviera una historia real que
contar, no tres líneas idénticas y aburridas.

---

## 3. Por qué estas decisiones técnicas

Prepárate para que te pregunten "¿por qué Python y no Java, si tu otro
proyecto es Java?" — es una pregunta que demuestra que sabes elegir
herramienta según el problema, no que solo sabes una tecnología:

- **Python + pandas**: es la herramienta estándar de facto para análisis de
  datos en la industria. Usar Java aquí habría sido forzar una herramienta
  equivocada solo por consistencia de portfolio — mejor mostrar que sé
  elegir la herramienta correcta para cada problema.
- **Streamlit** en vez de construir un frontend React desde cero: para un
  dashboard de análisis de datos, Streamlit convierte una función de Python
  directamente en una web interactiva, sin tener que escribir HTML/CSS/JS
  aparte. Es exactamente la herramienta que un analista de datos usaría en
  este contexto — y me deja centrar el esfuerzo en el análisis, no en
  reconstruir infraestructura de frontend que ya demostré saber hacer en
  PlantPulse.
- **Plotly**: gráficos interactivos (zoom, hover con valores exactos) en
  vez de imágenes estáticas — se ve mucho mejor en una demo en vivo.
- **Datos sintéticos, no un dataset real descargado**: así puedo controlar
  exactamente qué historia cuentan los datos (una línea peor que las
  otras, una causa de parada dominante) y cualquiera puede ejecutar el
  proyecto sin depender de una fuente de datos externa que podría
  desaparecer o requerir registro.

---

## 4. Recorrido por el código, archivo a archivo

### `oee.py` — el núcleo

Es el archivo más importante para explicar bien, porque es donde está toda
la lógica de negocio, separada a propósito del dashboard.

- `availability()`, `performance()`, `quality()`, `oee()`: cada una
  implementa literalmente la fórmula de la tabla de arriba. Funciones
  pequeñas, una responsabilidad cada una — fáciles de testear por
  separado.
- `compute_oee_columns()`: aplica esas fórmulas a todas las filas de un
  DataFrame de golpe (una fila = un turno de una línea en un día).
- `weighted_average_oee()`: **esta es la función que más vale la pena
  explicar en detalle si te preguntan por una decisión de diseño
  interesante.** Ver punto 5 más abajo — evita un error muy típico en
  dashboards de OEE mal hechos.

### `data_generator.py` — los datos sintéticos

Simula 3 líneas × 3 turnos × 30 días. Para cada turno genera minutos de
parada (con motivo: avería, cambio de formato, paradas menores, falta de
material, mantenimiento planificado), y a partir de ahí calcula cuántas
piezas se hicieron y cuántas salieron defectuosas. La línea "Line C" tiene
un sesgo intencionado hacia más averías y más defectos — es la que hace
interesante la comparativa entre líneas.

Usa una semilla fija (`RNG_SEED = 42`) para que los datos sean
**reproducibles**: cada vez que se ejecuta, salen los mismos números. Esto
es importante para una demo — no quieres que el reclutador vea números
distintos cada vez que recarga la página.

### `app.py` — el dashboard

Ensambla todo: carga los datos (con caché de Streamlit para no
regenerarlos en cada interacción), aplica los filtros de la barra lateral
(rango de fechas, líneas, turnos), y pinta las 4 tarjetas de KPI, el
gráfico de tendencia, la comparativa por línea y turno, y el Pareto de
paradas.

### `tests/`

Dos archivos: `test_oee.py` (12 tests de la lógica de cálculo, con números
que puedes comprobar a mano) y `test_app_smoke.py` (3 tests que ejecutan
el dashboard completo de forma automática con el framework oficial de
testing de Streamlit, `AppTest`, y comprueban que no lanza ninguna
excepción). 15 tests en total, todos en verde.

---

## 5. La decisión de diseño que más vale la pena mencionar

Si en la entrevista quieres enseñar que piensas más allá de "hacer que
funcione", esta es la anécdota a contar:

**El error típico**: si tienes varios turnos y calculas el OEE de cada uno
por separado, y luego simplemente haces la media de esos porcentajes, un
turno corto (por ejemplo, uno que casi no llegó a arrancar) pesa
exactamente igual que un turno completo de 8 horas. Eso es matemáticamente
incorrecto — un turno de 8 horas representa mucha más producción real que
uno de 20 minutos, así que debería pesar mucho más en el promedio.

**La solución en `weighted_average_oee()`**: en vez de promediar
porcentajes, sumo primero los minutos y unidades reales de todos los
turnos, y calculo el OEE **una sola vez** sobre esos totales agregados.
Así un turno corto y malo no arrastra el número igual que uno largo y
bueno.

Hay un test específico para esto — `test_weighted_average_oee_is_not_a_naive_mean`
— que construye a propósito un turno corto y malo junto a uno largo y
bueno, y comprueba que el resultado se parece mucho más al turno largo que
a una media 50/50. Si te preguntan "¿cómo sabes que tu código está bien?",
esto es un ejemplo concreto y explicable, no solo "porque pasan los
tests".

---

## 6. Preguntas típicas de entrevista y cómo responderlas

**"¿Por qué OEE y no otra métrica?"**
Es la métrica estándar del sector para eficiencia de producción — la
reconoce cualquier persona de manufactura sin que se la tengas que
explicar, a diferencia de una métrica inventada para el proyecto.

**"¿De dónde salen los datos?"**
Son sintéticos, generados con una semilla fija para que sean
reproducibles. Lo hice así a propósito: así controlo que los datos
cuenten una historia real (una línea peor que las demás) y cualquiera
puede clonar el repo y verlo funcionar sin depender de una fuente externa.

**"¿Cómo sabes que el cálculo es correcto?"**
15 tests automatizados: 12 sobre la lógica de cálculo pura (con números
que se pueden comprobar a mano), y 3 que ejecutan el dashboard entero de
forma automática para comprobar que no falla. Uno de los tests
específicamente verifica que el promedio ponderado no comete el error
típico de tratar un turno corto igual que uno largo.

**"¿Por qué Streamlit y no [Django/Flask/React]?"**
Porque es la herramienta correcta para este trabajo concreto: convierte
una función de Python en un dashboard interactivo sin escribir
HTML/CSS/JS aparte, que es justo lo que un analista de datos usaría. Ya
demostré que sé construir un frontend completo en React en mi otro
proyecto (PlantPulse) — aquí quería que el esfuerzo estuviera en el
análisis, no en repetir esa misma habilidad.

**"¿Qué harías distinto si fuera para producción real?"**
Conectaría a una fuente de datos real (un ERP/MES, o una base de datos)
en vez de datos sintéticos, y probablemente separaría el cálculo en un
servicio/API independiente del dashboard para que otros sistemas también
pudieran consumir esos números — ahora mismo `oee.py` ya está desacoplado
de Streamlit precisamente para que ese cambio fuera sencillo el día de
mañana.

**"¿Cuál es la limitación más honesta del proyecto?"**
Los datos son sintéticos, no de una fábrica real — y aunque el generador
está diseñado para producir números realistas, un caso real tendría
patrones más complejos (estacionalidad, turnos que se solapan,
mantenimiento no programado que depende de otros factores). Es una
simplificación deliberada para un proyecto de portfolio, no un descuido.

---

## 7. Cómo hacer una demo en vivo (guion sugerido, ~90 segundos)

1. Arranca con `streamlit run app.py` y muestra las 4 tarjetas de KPI
   arriba — "esto es el resumen: 78% de OEE global, con disponibilidad
   alta pero rendimiento algo más bajo".
2. Señala el gráfico de barras "OEE by line" — "aquí se ve que Line C va
   peor que las otras dos".
3. Pasa al Pareto de paradas — "y aquí se ve por qué: Breakdown es la
   causa dominante de tiempo perdido, así que si yo fuera el responsable
   de planta, empezaría por ahí, no por optimizar cambios de formato que
   pesan mucho menos".
4. Usa los filtros de la barra lateral para quedarte solo con Line C y el
   turno de noche — "y aquí puedes ver cómo cambian los números al filtrar
   por línea o turno específico".
5. Cierra con los tests: "todo esto está testeado — 15 tests, incluyendo
   uno que verifica específicamente que el promedio entre turnos está bien
   ponderado, que es un error común en dashboards de OEE mal hechos".

---

## 8. Si te preguntan "¿qué añadirías después?"

Tienes una respuesta lista en el roadmap del README técnico: desplegarlo
en Streamlit Community Cloud (gratis, y mucho más simple que la odisea de
tres servicios que fue desplegar PlantPulse — vale la pena mencionar esa
diferencia si sale el tema), dejar que alguien suba su propio CSV en vez
de solo usar datos sintéticos, añadir una previsión simple de hacia dónde
va el OEE la semana que viene, o exportar un informe en PDF/Excel por
turno.
