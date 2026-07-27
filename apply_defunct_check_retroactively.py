# =====================================================
# RETROACTIVE DEFUNCT-DETECTION FIX (free - no new LLM calls)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# detect_defunct_company() was added to
# modules/sales_intelligence_pipeline.py AFTER a batch of accounts
# had already been processed by rerun_qualified_with_search.py.
# Since this is a POST-PROCESSING check (it reads the already-
# generated llm_specific_fact, it doesn't change the prompt sent to
# the LLM), there's no need to re-call the LLM to benefit from it -
# the same pattern as apply_caveat_retroactively.py earlier this
# session.
#
# This re-applies the check against every already-completed
# account's saved llm_specific_fact, with ZERO new LLM calls.
# Idempotent - safe to run multiple times.
#
# After running this, resume rerun_qualified_with_search.py as
# normal for any remaining not-yet-processed accounts - it will
# pick up these corrected values during its merge step.
#
# Usage:
#     python3 apply_defunct_check_retroactively.py
# =====================================================

import ast
import pandas as pd

from modules.sales_intelligence_pipeline import detect_defunct_company

CHECKPOINT_FILE = "output/llm_validation_results.xlsx"


def parse_field(value):
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


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
    "engineering_implications", "couchbase_point_of_view",
    "llm_narrative_caveated", "llm_defunct_detected",
    "llm_workload_score", "llm_realtime_score", "llm_complexity_score",
    "llm_total_score", "llm_score_reasoning",
]
for col in TARGET_COLS:
    if col in results.columns:
        results[col] = results[col].astype(object)
    else:
        results[col] = None

already_defunct = 0
newly_defunct = 0
not_defunct = 0
skipped_not_validated = 0

for idx, row in results.iterrows():

    if not is_true(row.get("llm_validation")):
        skipped_not_validated += 1
        continue

    if is_true(row.get("llm_defunct_detected")):
        already_defunct += 1
        continue

    result = row.to_dict()
    result["engineering_implications"] = parse_field(result.get("engineering_implications"))

    was_defunct_before = False  # column didn't exist or was False/blank

    detect_defunct_company(result)

    if result["llm_defunct_detected"]:
        newly_defunct += 1
    else:
        not_defunct += 1

    for col in [
        "engineering_implications", "couchbase_point_of_view",
        "llm_narrative_caveated", "llm_defunct_detected",
        "llm_workload_score", "llm_realtime_score", "llm_complexity_score",
        "llm_total_score",
    ]:
        if col == "engineering_implications":
            results.at[idx, col] = str(result[col])
        else:
            results.at[idx, col] = result.get(col)

print()
print("=========================================================")
print("RETROACTIVE DEFUNCT-DETECTION SUMMARY")
print("=========================================================")
print(f"Newly detected as defunct (score capped, flagged):  {newly_defunct}")
print(f"Already had the flag (no change needed):            {already_defunct}")
print(f"Checked, genuinely not defunct:                      {not_defunct}")
print(f"Not yet LLM-validated (skipped):                     {skipped_not_validated}")

results.to_excel(CHECKPOINT_FILE, index=False)
print()
print(f"Saved: {CHECKPOINT_FILE}")
print()
print("Next: resume rerun_qualified_with_search.py as normal for any")
print("remaining not-yet-processed accounts. It will pick up these")
print("corrected values during its merge step - no need to force")
print("re-run anything that just got fixed here.")
