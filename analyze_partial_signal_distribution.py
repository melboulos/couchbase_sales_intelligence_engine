# =====================================================
# PARTIAL SIGNAL DISTRIBUTION
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# review_tier4_full.py found that 1,820 Tier 4 accounts
# already have SOME engine recognition (overall_coi > 0)
# but not enough to clear the Tier 3 threshold (40 points).
# This script answers: how close are they? A histogram
# clustered near 40 means a small, systemic scoring/pattern
# adjustment could flip hundreds of accounts into Tier 3 at
# once. A histogram scattered low (near 0-15) means each
# needs individual, real pattern/known_companies work - no
# shortcut available.
#
# Usage:
#     python3 analyze_partial_signal_distribution.py
# =====================================================

import pandas as pd

INPUT_FILE = "output/precursor_review.xlsx"

TIER3_THRESHOLD = 40  # from modules/scoring_engine.py

print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)

tier4 = accounts[accounts["priority_tier"] == "Tier 4 Monitor"].copy()
tier4 = tier4.drop_duplicates(subset="Account Name", keep="first")

partial = tier4[tier4["overall_coi"].fillna(0) > 0].copy()

print(f"Tier 4 accounts (deduped): {len(tier4)}")
print(f"With partial signal (overall_coi > 0): {len(partial)}")
print()

# -----------------------------------------------------
# HISTOGRAM BUCKETS
# -----------------------------------------------------

bins = [0, 5, 10, 15, 20, 25, 30, 35, 40]
labels = [
    "1-5", "6-10", "11-15", "16-20",
    "21-25", "26-30", "31-35", "36-39"
]

partial["coi_bucket"] = pd.cut(
    partial["overall_coi"],
    bins=bins,
    labels=labels,
    include_lowest=False,
    right=True
)

bucket_counts = partial["coi_bucket"].value_counts().sort_index()

print("=========================================================")
print(f"DISTRIBUTION OF overall_coi WITHIN THE PARTIAL-SIGNAL GROUP")
print(f"(Tier 3 threshold is {TIER3_THRESHOLD} - none of these have reached it)")
print("=========================================================")
print()
for label in labels:
    count = int(bucket_counts.get(label, 0))
    bar = "#" * (count // max(1, len(partial) // 100) or 1)
    print(f"{label:>6} pts: {count:>5}  {bar}")
print()

near_threshold = partial[partial["overall_coi"] >= 30]
low_score = partial[partial["overall_coi"] < 15]

print(f"Near threshold (30-39, likely 1-2 signals away from Tier 3): "
      f"{len(near_threshold)}")
print(f"Low score (1-14, would need substantial new evidence):        "
      f"{len(low_score)}")
print()

if len(near_threshold) >= len(partial) * 0.15:
    print(">>> SIGNIFICANT cluster near the threshold. Worth reviewing")
    print(">>> what's actually missing for a sample of the 30-39 group -")
    print(">>> a single additional matched signal (e.g. one more")
    print(">>> keyword/pattern) could flip many of these into Tier 3")
    print(">>> at once, without needing per-account research.")
else:
    print(">>> No major cluster near the threshold - most partial-signal")
    print(">>> accounts are scattered well below it. This suggests")
    print(">>> individual pattern/known_companies research (like the")
    print(">>> work already done for banks/telecom/healthcare) is the")
    print(">>> only real lever here, not a systemic scoring tweak.")
print()

# Save the near-threshold group specifically, since it's the
# highest-leverage subset to look at first if the cluster is real.
OUTPUT_FILE = "output/near_threshold_accounts.xlsx"
near_threshold.sort_values("overall_coi", ascending=False).to_excel(
    OUTPUT_FILE, index=False
)
print(f"Saved near-threshold (30-39 pt) accounts to: {OUTPUT_FILE}")
