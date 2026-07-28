# =====================================================
# RETROACTIVE UNGROUNDED-SCORE FIX (free - no new LLM calls)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# detect_ungrounded_score() was added to
# modules/sales_intelligence_pipeline.py AFTER a batch of accounts
# had already been processed. Since this is a POST-PROCESSING check
# (it reads the already-generated llm_score_reasoning and
# llm_specific_fact, it doesn't change the prompt sent to the LLM),
# there's no need to re-call the LLM to benefit from it - same
# pattern as apply_caveat_retroactively.py and
# apply_defunct_check_retroactively.py earlier this session.
#
# This re-applies the check against every already-completed
# account's saved reasoning, with ZERO new LLM calls. Idempotent -
# safe to run multiple times, and safe to run WHILE
# rerun_qualified_with_search.py is still going in another terminal,
# since it only reads/writes the checkpoint file between runs of
# this script, not during the main run itself.
#
# Usage:
#     python3 apply_ungrounded_score_check_retroactively.py
# =====================================================

import pandas as pd

from modules.sales_intelligence_pipeline import detect_ungrounded_score

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
    "llm_score_ungrounded", "llm_workload_score", "llm_realtime_score",
    "llm_complexity_score", "llm_total_score", "llm_score_reasoning",
]
for col in TARGET_COLS:
    if col in results.columns:
        results[col] = results[col].astype(object)
    else:
        results[col] = None

already_flagged = 0
newly_capped = 0
genuinely_grounded = 0
not_verified = 0
skipped_not_validated = 0

for idx, row in results.iterrows():

    if not is_true(row.get("llm_validation")):
        skipped_not_validated += 1
        continue

    if is_true(row.get("llm_score_ungrounded")):
        already_flagged += 1
        continue

    result = row.to_dict()
    result["llm_recognition_verified"] = is_true(result.get("llm_recognition_verified"))

    if not result["llm_recognition_verified"]:
        not_verified += 1
        results.at[idx, "llm_score_ungrounded"] = False
        continue

    old_total = result.get("llm_total_score")

    detect_ungrounded_score(result)

    if result["llm_score_ungrounded"]:
        newly_capped += 1
    else:
        genuinely_grounded += 1

    for col in TARGET_COLS:
        results.at[idx, col] = result.get(col)

print()
print("=========================================================")
print("RETROACTIVE UNGROUNDED-SCORE SUMMARY")
print("=========================================================")
print(f"Newly detected as ungrounded (score capped):  {newly_capped}")
print(f"Already had the flag (no change needed):      {already_flagged}")
print(f"Checked, genuinely grounded (unchanged):       {genuinely_grounded}")
print(f"Not verified (handled by the OLD cap already): {not_verified}")
print(f"Not yet LLM-validated (skipped):               {skipped_not_validated}")

total_checked = newly_capped + already_flagged + genuinely_grounded
if total_checked > 0:
    rate = 100 * (newly_capped + already_flagged) / total_checked
    print(f"\nUngrounded rate among verified accounts: {rate:.1f}%")

results.to_excel(CHECKPOINT_FILE, index=False)
print()
print(f"Saved: {CHECKPOINT_FILE}")
print()
print("Next: resume/re-run rerun_qualified_with_search.py's merge step")
print("(or just let it finish naturally) to carry these corrected")
print("scores into the final scored file.")
