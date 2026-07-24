# =====================================================
# NEAR-THRESHOLD DIFFERENTIAL ANALYSIS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# analyze_partial_signal_distribution.py found ~398 Tier 4
# accounts scoring 26-39 points - close to the Tier 3 cutoff
# of 40, with almost nothing in the 16-25 range (a gap that
# suggests scores cluster by WHICH combination of discrete
# signal bonuses fired, not a smooth distribution).
#
# This script compares that near-threshold group against
# real Tier 3 accounts (40-59 points) to find which specific
# signal(s) the Tier 3 group has that the near-threshold
# group is missing - the actual differentiator, rather than
# guessing from eyeballing individual rows.
#
# Usage:
#     python3 near_threshold_differential.py
# =====================================================

import pandas as pd
from collections import Counter

INPUT_FILE = "output/precursor_review.xlsx"

print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)
accounts = accounts.drop_duplicates(subset="Account Name", keep="first")

near_threshold = accounts[
    (accounts["overall_coi"] >= 26) & (accounts["overall_coi"] < 40)
].copy()

tier3 = accounts[
    (accounts["overall_coi"] >= 40) & (accounts["overall_coi"] < 60)
].copy()

print(f"Near-threshold group (26-39 pts): {len(near_threshold)}")
print(f"Real Tier 3 comparison group (40-59 pts): {len(tier3)}")
print()

if len(tier3) == 0:
    print("No Tier 3 (40-59) accounts found to compare against - "
          "cannot run differential. Check overall_coi values in the file.")
    raise SystemExit()


def signal_frequency(df, column="signals_found"):
    """
    signals_found is stored as a list (or list-like string) per
    row. Count how often each individual signal appears across
    the group, as a percentage of the group size.
    """
    counter = Counter()
    n = len(df)

    for value in df.get(column, []):
        if isinstance(value, str):
            # If it came back from Excel as a string
            # representation of a list, strip brackets/quotes.
            cleaned = value.strip("[]").replace("'", "").replace('"', "")
            items = [s.strip() for s in cleaned.split(",") if s.strip()]
        elif isinstance(value, list):
            items = value
        else:
            items = []

        for item in items:
            counter[item] += 1

    return {
        signal: round(100 * count / n, 1)
        for signal, count in counter.items()
    } if n else {}


near_freq = signal_frequency(near_threshold)
tier3_freq = signal_frequency(tier3)

all_signals = set(near_freq) | set(tier3_freq)

print("=========================================================")
print("SIGNAL PRESENCE: NEAR-THRESHOLD (26-39) vs TIER 3 (40-59)")
print("=========================================================")
print(f"{'Signal':<40} {'Near-Thresh %':>15} {'Tier 3 %':>12} {'Gap':>8}")

rows = []
for signal in all_signals:
    near_pct = near_freq.get(signal, 0)
    tier3_pct = tier3_freq.get(signal, 0)
    gap = tier3_pct - near_pct
    rows.append((signal, near_pct, tier3_pct, gap))

rows.sort(key=lambda r: r[3], reverse=True)

for signal, near_pct, tier3_pct, gap in rows:
    print(f"{signal:<40} {near_pct:>14}% {tier3_pct:>11}% {gap:>7}%")

print()
if rows:
    top_signal, top_near, top_tier3, top_gap = rows[0]
    print(f">>> BIGGEST GAP: '{top_signal}'")
    print(f">>> Present in {top_tier3}% of real Tier 3 accounts, but only")
    print(f">>> {top_near}% of the near-threshold group. This is the")
    print(f">>> strongest candidate for 'the one thing missing' - check")
    print(f">>> whether expanding the pattern/keyword list that produces")
    print(f">>> this specific signal would be the highest-leverage next")
    print(f">>> step, before doing broad per-account research.")
