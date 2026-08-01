"""
tests/test_oee.py

Tests for the core OEE math. These are deliberately simple, hand-checkable
numbers (not the synthetic generator's random data) so each test's
expected value can be verified by hand in about 10 seconds -- that's
the point of testing business logic in isolation.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oee import (
    availability,
    performance,
    quality,
    oee,
    compute_oee_columns,
    weighted_average_oee,
)


def test_availability_basic():
    # 400 minutes run out of 480 planned = 83.3%
    assert availability(400, 480) == pytest.approx(400 / 480)


def test_availability_zero_planned_time_is_zero_not_error():
    assert availability(100, 0) == 0.0


def test_availability_is_capped_at_one():
    # run time can't sensibly exceed planned time; guard against bad data
    assert availability(500, 480) == 1.0


def test_performance_basic():
    # ideal cycle = 2s, ran for 60 minutes (3600s) -> theoretical max = 1800 units
    # actually made 1500 units -> performance = 1500/1800
    assert performance(total_units=1500, ideal_cycle_seconds=2, run_time_minutes=60) == pytest.approx(1500 / 1800)


def test_performance_zero_run_time_is_zero_not_division_error():
    assert performance(100, 2, 0) == 0.0


def test_quality_basic():
    assert quality(good_units=950, total_units=1000) == pytest.approx(0.95)


def test_quality_zero_total_units_is_zero_not_error():
    assert quality(0, 0) == 0.0


def test_oee_multiplies_the_three_factors():
    # textbook example: 90% x 95% x 99% ~= 84.6%
    result = oee(0.90, 0.95, 0.99)
    assert result == pytest.approx(0.90 * 0.95 * 0.99)


def test_oee_of_perfect_shift_is_one():
    assert oee(1.0, 1.0, 1.0) == 1.0


def test_compute_oee_columns_matches_manual_calculation():
    df = pd.DataFrame([{
        "planned_minutes": 450,
        "run_time_minutes": 400,
        "total_units": 1800,
        "good_units": 1750,
        "ideal_cycle_seconds": 12,  # 400 min run -> 24000s / 12 = 2000 theoretical units
    }])
    result = compute_oee_columns(df).iloc[0]

    expected_availability = 400 / 450
    expected_performance = 1800 / 2000
    expected_quality = 1750 / 1800
    expected_oee = expected_availability * expected_performance * expected_quality

    assert result["availability"] == pytest.approx(expected_availability)
    assert result["performance"] == pytest.approx(expected_performance)
    assert result["quality"] == pytest.approx(expected_quality)
    assert result["oee"] == pytest.approx(expected_oee)


def test_weighted_average_oee_is_not_a_naive_mean():
    """
    A short shift with terrible OEE and a long shift with great OEE
    should NOT average 50/50 -- the long shift should dominate because
    it represents more actual production time. This is the classic bug
    naive OEE dashboards have.
    """
    df = pd.DataFrame([
        {  # short, bad shift: 30 planned min, ran only 5
            "planned_minutes": 30, "run_time_minutes": 5,
            "total_units": 50, "good_units": 50, "ideal_cycle_seconds": 6,
        },
        {  # long, great shift: 450 planned min, ran nearly all of it
            "planned_minutes": 450, "run_time_minutes": 440,
            "total_units": 4300, "good_units": 4270, "ideal_cycle_seconds": 6,
        },
    ])
    result = weighted_average_oee(df)

    # sanity: result should be much closer to the long shift's OEE than
    # to a plain average of the two shifts' individual OEE values
    per_shift = compute_oee_columns(df)
    naive_mean = per_shift["oee"].mean()

    assert result["oee"] > naive_mean  # the bad short shift shouldn't drag it down 50/50
    assert 0.0 <= result["oee"] <= 1.0


def test_weighted_average_oee_empty_dataframe():
    result = weighted_average_oee(pd.DataFrame(columns=[
        "planned_minutes", "run_time_minutes", "total_units", "good_units", "ideal_cycle_seconds"
    ]))
    assert result == {"availability": 0.0, "performance": 0.0, "quality": 0.0, "oee": 0.0}
