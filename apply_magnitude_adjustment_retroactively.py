# =====================================================
# RETROACTIVE MAGNITUDE-ADJUSTMENT FIX (free - no new LLM calls)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# apply_magnitude_based_score_adjustment() was added AFTER a batch
# of accounts had already been processed. Same pattern as the two
# prior retroactive-fix scripts this session: this is a post-
# processing check reading already-saved llm_specific_fact/
# llm_score_reasoning text, so there's no need to re-call the LLM.
#
# IMPORTANT: only run this when rerun_qualified_with_search.py is
# NOT actively running - a still-running process periodically
# overwrites the entire checkpoint file from its own in-memory
# snapshot, silently erasing whatever this script just fixed
# (confirmed the hard way earlier this session).
#
# Usage:
#     python3 apply_magnitude_adjustment_retroactively.py
# =====================================================

import pandas as pd

from modules.sales_intelligence_pipeline import apply_magnitude_based_score_adjustment

CHECKPOINT_FILE = "output/llm_validation_results.xlsx"


def is_true(value):
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1.0:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


print(f"Loading: {CHECKPOINT_FILE}")
results = pd.read_excel(CHECKPOINT_FILE)
print(f"Total rows: {len(results)}")

TARGET_COLS = [
    "llm_magnitude_bucket", "llm_workload_score", "llm_realtime_score",
    "llm_complexity_score", "llm_total_score",
]
for col in TARGET_COLS:
    if col in results.columns:
        results[col] = results[col].astype(object)
    else:
        results[col] = None

already_bucketed = 0
newly_large = 0
newly_small = 0
newly_medium = 0
no_magnitude_found = 0
not_verified = 0
skipped_not_validated = 0

for idx, row in results.iterrows():

    if not is_true(row.get("llm_validation")):
        skipped_not_validated += 1
        continue

    existing_bucket = row.get("llm_magnitude_bucket")
    if isinstance(existing_bucket, str) and existing_bucket in ("large", "small", "medium"):
        already_bucketed += 1
        continue

    result = row.to_dict()
    result["llm_recognition_verified"] = is_true(result.get("llm_recognition_verified"))

    if not result["llm_recognition_verified"]:
        not_verified += 1
        continue

    before_total = result.get("llm_total_score")

    apply_magnitude_based_score_adjustment(result)

    bucket = result.get("llm_magnitude_bucket")
    if bucket == "large":
        newly_large += 1
    elif bucket == "small":
        newly_small += 1
    elif bucket == "medium":
        newly_medium += 1
    else:
        no_magnitude_found += 1

    for col in TARGET_COLS:
        results.at[idx, col] = result.get(col)

print()
print("=========================================================")
print("RETROACTIVE MAGNITUDE-ADJUSTMENT SUMMARY")
print("=========================================================")
print(f"Already bucketed (no change needed):        {already_bucketed}")
print(f"Newly bucketed 'large' (score floored up):  {newly_large}")
print(f"Newly bucketed 'small' (score capped down):  {newly_small}")
print(f"Newly bucketed 'medium' (unchanged):          {newly_medium}")
print(f"No magnitude found (unchanged):                {no_magnitude_found}")
print(f"Not verified (skipped):                         {not_verified}")
print(f"Not yet LLM-validated (skipped):                {skipped_not_validated}")

results.to_excel(CHECKPOINT_FILE, index=False)
print()
print(f"Saved: {CHECKPOINT_FILE}")
