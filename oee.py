"""
oee.py

Core OEE (Overall Equipment Effectiveness) calculations. Kept separate
from the Streamlit app on purpose: this is the "business logic" a
recruiter or interviewer would want to see tested in isolation, with
no dependency on the dashboard framework.

OEE = Availability x Performance x Quality

  Availability = Run Time / Planned Production Time
      Run Time = Planned Production Time - Unplanned Downtime
      (i.e. were we actually running, or stopped for a breakdown,
      changeover, etc.?)

  Performance = (Ideal Cycle Time x Total Units) / Run Time
      (i.e. while running, were we running at full speed, or slower
      than the machine's rated cycle time?)

  Quality = Good Units / Total Units
      (i.e. of what we made, how much was actually sellable?)

Reference values, for interpreting the numbers this module produces:
  - 100% OEE is theoretically perfect production: only good parts, as
    fast as possible, with no stop time.
  - 85% OEE is the commonly cited "world class" benchmark for discrete
    manufacturing.
  - 60% is typical/average for many plants.
  - Below 40% usually signals a real underlying problem.
"""

from __future__ import annotations

import pandas as pd


def availability(run_time_minutes: float, planned_minutes: float) -> float:
    """Fraction of planned time that was actually spent running."""
    if planned_minutes <= 0:
        return 0.0
    return max(0.0, min(1.0, run_time_minutes / planned_minutes))


def performance(total_units: float, ideal_cycle_seconds: float, run_time_minutes: float) -> float:
    """
    Fraction of the theoretical max output achieved while running.
    Capped at 1.0: running "faster than ideal" isn't a meaningful loss
    category, and small measurement noise shouldn't produce >100%.
    """
    if run_time_minutes <= 0:
        return 0.0
    run_time_seconds = run_time_minutes * 60
    theoretical_units = run_time_seconds / ideal_cycle_seconds
    if theoretical_units <= 0:
        return 0.0
    return max(0.0, min(1.0, total_units / theoretical_units))


def quality(good_units: float, total_units: float) -> float:
    """Fraction of everything produced that was actually good."""
    if total_units <= 0:
        return 0.0
    return max(0.0, min(1.0, good_units / total_units))


def oee(availability_pct: float, performance_pct: float, quality_pct: float) -> float:
    """Combine the three factors. Each input is a 0-1 fraction, not a %."""
    return availability_pct * performance_pct * quality_pct


def compute_oee_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given the raw shift-level production log (one row per line/day/shift),
    add availability / performance / quality / oee columns.

    Expects columns: run_time_minutes, planned_minutes, total_units,
    ideal_cycle_seconds, good_units.
    """
    out = df.copy()
    out["availability"] = out.apply(
        lambda r: availability(r["run_time_minutes"], r["planned_minutes"]), axis=1
    )
    out["performance"] = out.apply(
        lambda r: performance(r["total_units"], r["ideal_cycle_seconds"], r["run_time_minutes"]),
        axis=1,
    )
    out["quality"] = out.apply(
        lambda r: quality(r["good_units"], r["total_units"]), axis=1
    )
    out["oee"] = out["availability"] * out["performance"] * out["quality"]
    return out


def weighted_average_oee(df: pd.DataFrame) -> dict:
    """
    Aggregate OEE across many shifts correctly: a straight mean of
    per-shift OEE percentages is misleading because it treats a 2-hour
    shift the same as an 8-hour one. Instead, sum the underlying
    minutes/units across all shifts first, then recompute the three
    factors once from those totals. Returns a dict with the four
    metrics as 0-1 fractions.
    """
    if df.empty:
        return {"availability": 0.0, "performance": 0.0, "quality": 0.0, "oee": 0.0}

    total_planned = df["planned_minutes"].sum()
    total_run = df["run_time_minutes"].sum()
    total_units = df["total_units"].sum()
    total_good = df["good_units"].sum()

    # weighted ideal cycle time: total run seconds / theoretical units
    # implied by each row's own cycle time, summed
    theoretical_units = (df["run_time_minutes"] * 60 / df["ideal_cycle_seconds"]).sum()

    avail = availability(total_run, total_planned)
    perf = max(0.0, min(1.0, total_units / theoretical_units)) if theoretical_units > 0 else 0.0
    qual = quality(total_good, total_units)

    return {
        "availability": avail,
        "performance": perf,
        "quality": qual,
        "oee": avail * perf * qual,
    }
