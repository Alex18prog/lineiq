"""
tests/test_app_smoke.py

A smoke test for the dashboard itself, using Streamlit's official
headless testing framework (AppTest) -- runs app.py exactly as
Streamlit would, without needing a browser, and fails if the script
raises any exception or the expected widgets don't render.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_runs_without_exceptions():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception, f"App raised: {at.exception}"


def test_app_renders_four_kpi_cards():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    labels = {m.label for m in at.metric}
    assert labels == {"OEE", "Availability", "Performance", "Quality"}


def test_kpi_values_are_plausible_percentages():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    for m in at.metric:
        value = float(m.value.strip("%"))
        assert 0.0 <= value <= 100.0
