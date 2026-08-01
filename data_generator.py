"""
data_generator.py

Generates a realistic-but-synthetic production log for a small factory,
so LineIQ has something meaningful to analyze without needing real
factory data. No manual data entry required to see the dashboard work.

Model: 3 production lines, 3 shifts/day, 30 days. For each
line/shift/day we simulate:
  - planned production minutes (a shift is 8h = 480 min, minus a fixed
    30 min break that's *planned* downtime, not a loss)
  - unplanned downtime events, each with a reason ("the six big losses"
    family: Breakdown, Changeover, Minor Stops, Material Shortage,
    Reduced Speed is handled separately via cycle time, Startup Rejects
    folds into quality)
  - units produced, split into good vs defective

Line C is deliberately made worse (more breakdowns, more defects) than
Line A and B, so the dashboard's line-comparison and Pareto views have
a real story to tell instead of three identical lines.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RNG_SEED = 42

LINES = {
    # line_id: (display name, ideal_cycle_time_seconds, breakdown_bias, defect_bias)
    "LINE_A": ("Line A — Bottling", 1.8, 1.0, 1.0),
    "LINE_B": ("Line B — Packaging", 2.4, 1.0, 1.0),
    "LINE_C": ("Line C — Assembly", 3.0, 1.8, 2.2),  # deliberately the "problem" line
}

SHIFTS = {
    "MORNING": (6, 14),    # 06:00-14:00
    "AFTERNOON": (14, 22),  # 14:00-22:00
    "NIGHT": (22, 6),      # 22:00-06:00
}

SHIFT_MINUTES = 8 * 60
PLANNED_BREAK_MINUTES = 30  # counted as planned downtime, not a loss
N_DAYS = 30

DOWNTIME_REASONS = [
    # reason, relative weight (higher = more common), avg minutes per event
    ("Breakdown", 3, 35),
    ("Changeover", 4, 20),
    ("Minor Stops", 6, 6),
    ("Material Shortage", 2, 25),
    ("Planned Maintenance", 1, 45),
]


def _simulate_shift(rng: np.random.Generator, line_id: str, day: int, shift_name: str) -> dict:
    _, ideal_cycle_s, breakdown_bias, defect_bias = LINES[line_id]

    available_minutes = SHIFT_MINUTES - PLANNED_BREAK_MINUTES

    # --- unplanned downtime for this shift ---
    downtime_events = []
    # number of downtime events this shift, biased per line
    n_events = rng.poisson(1.4 * breakdown_bias)
    remaining_minutes = available_minutes
    for _ in range(n_events):
        reasons, weights, avg_minutes = zip(*DOWNTIME_REASONS)
        weights = np.array(weights, dtype=float)
        # breakdown-prone lines see relatively more "Breakdown" events
        weights[0] *= breakdown_bias
        weights = weights / weights.sum()
        reason = rng.choice(reasons, p=weights)
        base_minutes = dict(zip(reasons, avg_minutes))[reason]
        minutes = max(1, int(rng.normal(base_minutes, base_minutes * 0.3)))
        minutes = min(minutes, max(1, remaining_minutes - 10))
        if minutes <= 0:
            continue
        downtime_events.append({"reason": reason, "minutes": minutes})
        remaining_minutes -= minutes

    total_downtime = sum(e["minutes"] for e in downtime_events)
    run_time_minutes = max(10, available_minutes - total_downtime)

    # --- throughput: how many units did we actually make in run_time? ---
    # operators rarely hit the ideal cycle time exactly; add realistic slack
    actual_cycle_s = ideal_cycle_s * rng.normal(1.15, 0.08)
    actual_cycle_s = max(ideal_cycle_s * 0.95, actual_cycle_s)
    total_units = int((run_time_minutes * 60) / actual_cycle_s)

    # --- quality: defect rate, worse for defect-prone lines ---
    base_defect_rate = 0.02 * defect_bias
    defect_rate = max(0.0, rng.normal(base_defect_rate, base_defect_rate * 0.4))
    good_units = int(total_units * (1 - defect_rate))
    defective_units = total_units - good_units

    return {
        "line_id": line_id,
        "line_name": LINES[line_id][0],
        "day": day,
        "shift": shift_name,
        "planned_minutes": available_minutes,
        "downtime_minutes": total_downtime,
        "run_time_minutes": run_time_minutes,
        "ideal_cycle_seconds": round(ideal_cycle_s, 2),
        "total_units": total_units,
        "good_units": good_units,
        "defective_units": defective_units,
        "downtime_events": downtime_events,
    }


def generate_production_log(seed: int = RNG_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns two DataFrames:
      - shifts_df: one row per (line, day, shift) with production totals
      - downtime_df: one row per individual downtime event (for the Pareto chart)
    """
    rng = np.random.default_rng(seed)

    shift_rows = []
    downtime_rows = []

    start_date = pd.Timestamp.today().normalize() - pd.Timedelta(days=N_DAYS)

    for day in range(N_DAYS):
        date = start_date + pd.Timedelta(days=day)
        for line_id in LINES:
            for shift_name in SHIFTS:
                record = _simulate_shift(rng, line_id, day, shift_name)
                record["date"] = date
                events = record.pop("downtime_events")
                shift_rows.append(record)
                for e in events:
                    downtime_rows.append({
                        "date": date,
                        "line_id": line_id,
                        "line_name": LINES[line_id][0],
                        "shift": shift_name,
                        "reason": e["reason"],
                        "minutes": e["minutes"],
                    })

    shifts_df = pd.DataFrame(shift_rows)
    downtime_df = pd.DataFrame(downtime_rows)
    return shifts_df, downtime_df


if __name__ == "__main__":
    shifts_df, downtime_df = generate_production_log()
    shifts_df.to_csv("data/production_log.csv", index=False)
    downtime_df.to_csv("data/downtime_log.csv", index=False)
    print(f"Wrote {len(shifts_df)} shift records and {len(downtime_df)} downtime events.")
