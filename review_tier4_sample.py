# =====================================================
# TIER 4 SAMPLE REVIEW
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Pulls a random sample of "Tier 4 Monitor" accounts from
# precursor_review.py's output, so you can manually spot-
# check whether they're genuinely low-fit, or whether the
# company is real and well-known but company_patterns.json
# simply doesn't recognize it yet (a coverage gap, not a
# fit problem).
#
# Usage:
#     python3 review_tier4_sample.py
# =====================================================

import pandas as pd

INPUT_FILE = "output/precursor_review.xlsx"
OUTPUT_FILE = "output/tier4_sample_for_review.xlsx"

SAMPLE_SIZE = 40
RANDOM_SEED = 42  # fixed seed so the sample is reproducible if you re-run this

# Columns to show, in priority order. Only ones that actually
# exist in your output are used - this list is intentionally
# generous so it works whether or not you re-run the full
# pipeline vs. just the precursor stages.
DISPLAY_COLUMNS = [
    "Account Name",
    "industry",
    "financial_segment",
    "company_archetype",
    "business_model",
    "workload_profile",
    "overall_coi",
    "priority_tier",
    "gate_reason",
    "why_score",
    "signals_found",
    "debug_text_sample",
]


print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts")

if "priority_tier" not in accounts.columns:
    raise SystemExit(
        "No 'priority_tier' column found - is this really the "
        "precursor_review.py output file?"
    )

tier4 = accounts[accounts["priority_tier"] == "Tier 4 Monitor"]
print(f"Tier 4 Monitor accounts: {len(tier4)}")

sample_n = min(SAMPLE_SIZE, len(tier4))
sample = tier4.sample(n=sample_n, random_state=RANDOM_SEED)

display_cols = [c for c in DISPLAY_COLUMNS if c in sample.columns]
sample_display = sample[display_cols].reset_index(drop=True)

sample_display.to_excel(OUTPUT_FILE, index=False)

print()
print("=========================================================")
print(f"RANDOM SAMPLE OF {sample_n} TIER 4 MONITOR ACCOUNTS")
print("=========================================================")
print()
print(sample_display.to_string(index=False))
print()
print(f"Saved to: {OUTPUT_FILE}")
print()
print("WHAT TO LOOK FOR:")
print("- Real, recognizable companies with no workload_profile and")
print("  generic/empty gate_reason -> likely a company_patterns.json")
print("  coverage gap (the company is fine, the pattern library just")
print("  doesn't know it yet).")
print("- Genuinely small/unknown/niche companies with no signals ->")
print("  likely a correct Tier 4 (low fit or insufficient evidence),")
print("  not a coverage problem.")
print("- If you spot 5+ names you personally recognize as legitimate")
print("  enterprise accounts in this sample, that's a strong signal")
print("  the coverage gap is systemic across the full 9,758, not")
print("  just the 4 examples we already found.")
