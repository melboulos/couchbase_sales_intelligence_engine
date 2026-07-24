# =====================================================
# VERTICAL LAGGARD CHECK
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# near_threshold_differential.py found that the 398-account
# near-threshold cluster is dominated by 4 workload profiles
# (insurance_platform, pharma_device_platform,
# utilities_platform, media_platform), each capped at lower
# database_intensity/operational_complexity/realtime_requirement
# points than other profiles in data/company_patterns.json.
#
# This pulls a real, named sample from each of those 4
# profiles so you can eyeball whether they're genuinely
# legacy/lower-complexity players (confirming the low
# ratings are correct - these ARE laggard verticals for
# Couchbase) or modern/digital-native operators being
# under-scored by a stale flat rating (a real coverage gap,
# same failure mode as the LLM calibration bug fixed earlier
# this session).
#
# Usage:
#     python3 vertical_laggard_check.py
# =====================================================

import pandas as pd

INPUT_FILE = "output/precursor_review.xlsx"
OUTPUT_FILE = "output/vertical_laggard_sample.xlsx"

TARGET_PROFILES = [
    "insurance_platform",
    "pharma_device_platform",
    "utilities_platform",
    "media_platform",
]

SAMPLE_PER_PROFILE = 20
RANDOM_SEED = 42

DISPLAY_COLUMNS = [
    "Account Name",
    "workload_profile",
    "overall_coi",
    "industry",
    "company_archetype",
    "signals_found",
    "debug_text_sample",
]


print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)
accounts = accounts.drop_duplicates(subset="Account Name", keep="first")

if "workload_profile" not in accounts.columns:
    raise SystemExit(
        "No 'workload_profile' column found in this file. This script "
        "needs the full enriched output (same file "
        "near_threshold_differential.py used), not the lean input file."
    )

near_threshold = accounts[
    (accounts["overall_coi"] >= 26) & (accounts["overall_coi"] < 40)
].copy()

print(f"Near-threshold group (26-39 pts): {len(near_threshold)}")
print()

display_cols = [c for c in DISPLAY_COLUMNS if c in near_threshold.columns]

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

    for profile in TARGET_PROFILES:

        subset = near_threshold[near_threshold["workload_profile"] == profile]
        n = len(subset)

        sample_n = min(SAMPLE_PER_PROFILE, n)

        print(f"{profile}: {n} accounts in near-threshold cluster "
              f"(sampling {sample_n})")

        if sample_n == 0:
            continue

        sample = subset.sample(n=sample_n, random_state=RANDOM_SEED)
        sample = sample[display_cols].sort_values("overall_coi", ascending=False)

        sheet_name = profile[:31]  # Excel sheet name limit
        sample.to_excel(writer, sheet_name=sheet_name, index=False)

print()
print(f"Saved: {OUTPUT_FILE}")
print("One sheet per workload profile, sorted by overall_coi descending.")
print()
print("WHAT TO LOOK FOR PER SHEET:")
print("- If names are mostly recognizable legacy/traditional")
print("  incumbents in that vertical -> the low rating is likely")
print("  correct. These verticals genuinely are lower-priority for")
print("  Couchbase, and Tier 4 is the right outcome.")
print("- If you spot modern/digital-native operators (e.g. an")
print("  insurtech, a smart-grid/IoT utility, a real-time ad-tech")
print("  platform, a connected-device pharma/medtech company) sitting")
print("  in the same low-scoring bucket as legacy players -> the flat")
print("  per-profile rating is masking real differences, the same")
print("  category-vs-specific-company problem already fixed on the")
print("  LLM scoring side. Worth splitting that profile into a")
print("  legacy/modern distinction rather than raising the whole")
print("  vertical's score uniformly.")
