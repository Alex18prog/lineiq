# LineIQ

🇬🇧 English · [🇪🇸 Español](README.es.md)

**OEE (Overall Equipment Effectiveness) analytics for manufacturing lines — built with Python, pandas, and Streamlit.**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-data%20analysis-150458?logo=pandas&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)
![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC?logo=pytest&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**[▶ Live demo](https://lineiq-oee.streamlit.app/)**
*(free-tier hosting — may take a few seconds to wake up if it's been idle)*

## What this is

OEE is the standard manufacturing metric for how much of a line's theoretical
capacity actually becomes good product: `Availability × Performance × Quality`.
LineIQ generates a realistic synthetic production log (3 lines, 3 shifts/day,
30 days, with downtime events and defect rates that vary deliberately by line)
and turns it into an interactive dashboard: overall OEE, trend over time,
comparison across lines and shifts, and a Pareto breakdown of *why* time is
being lost — the classic "six big losses" view used on real factory floors.

## Why this project

- **A real, standard industrial metric** — OEE isn't invented; it's what
  plant managers already track. A dashboard built around it is instantly
  legible to anyone in manufacturing, not just developers.
- **The right tool for the domain** — Python + pandas is what a data
  analytics task like this is actually built with in industry, not a
  language chosen for portfolio consistency.
- **Business logic tested in isolation** — `oee.py` has no dependency on
  the dashboard framework and is covered by 12 unit tests, including one
  that specifically guards against a real bug pattern (naively averaging
  per-shift OEE percentages instead of weighting by production time).
- **The dashboard itself is tested too** — `tests/test_app_smoke.py` uses
  Streamlit's official `AppTest` framework to run the full app headlessly
  and assert it renders without exceptions, not just that the math is right.

## Project structure

| File | Responsibility |
|---|---|
| `oee.py` | Core OEE math — `availability()`, `performance()`, `quality()`, `oee()`, plus `weighted_average_oee()` for correctly aggregating across shifts of different lengths |
| `data_generator.py` | Synthetic production log generator (fixed random seed, so the demo is reproducible) |
| `app.py` | The Streamlit dashboard: KPI cards, trend chart, line/shift comparison, downtime Pareto chart |
| `tests/test_oee.py` | Unit tests for the calculation logic, with hand-checkable expected values |
| `tests/test_app_smoke.py` | Headless smoke tests for the dashboard itself |

## The three factors, briefly

- **Availability** = Run Time ÷ Planned Production Time — were we actually
  running, or stopped (breakdown, changeover, material shortage...)?
- **Performance** = Actual Output ÷ Theoretical Max Output while running —
  while running, were we at full speed or slower than rated cycle time?
- **Quality** = Good Units ÷ Total Units — of what we made, how much was
  actually sellable?

Multiplying the three together is deliberately punishing: a line that's
available 90% of the time, running at 90% speed, and making 90% good parts
isn't at 90% OEE — it's at 90%×90%×90% ≈ 73%. That compounding effect is
the whole point of the metric, and why "small" losses in three different
places add up to a much bigger overall gap than they look individually.

## Running it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. Data is generated on load with a fixed
seed (`RNG_SEED = 42` in `data_generator.py`) — every run shows the same
numbers, so the dashboard is reproducible without needing a real database.

### Running the tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap / possible extensions

- [x] Deploy to Streamlit Community Cloud (linked above)
- [ ] Let a user upload their own CSV instead of only using synthetic data
- [ ] Add a simple forecast (e.g. rolling average or linear trend) for
      "where is OEE headed next week"
- [ ] Export a PDF/Excel shift report

## License

MIT — do whatever you want with this, it's a portfolio project.
