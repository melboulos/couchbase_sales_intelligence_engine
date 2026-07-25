# =====================================================
# RETROACTIVE NARRATIVE CAVEAT (free - no new LLM calls)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# apply_narrative_caveat() was added to
# modules/sales_intelligence_pipeline.py AFTER the current
# ~3,018-account run_new_llm_candidates.py job already started.
# Python doesn't reload code from disk mid-execution, so every
# account processed by that already-running job was saved
# WITHOUT the caveat, even after the fix landed on disk.
#
# This applies the caveat retroactively to the raw checkpoint
# (output/llm_validation_results.xlsx) with ZERO new LLM calls -
# pure post-processing of already-collected results. Idempotent:
# safe to run multiple times, will never double-apply the caveat
# to a row that already has it.
#
# After running this, re-run run_new_llm_candidates.py once -
# since every account will already show llm_validation == True,
# it will make NO new Bedrock calls and go straight to the merge
# step, carrying the now-caveated results into the final file.
#
# Usage:
#     python3 apply_caveat_retroactively.py
# =====================================================

import ast
import pandas as pd

from modules.sales_intelligence_pipeline import apply_narrative_caveat

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
    """
    Excel round-trips booleans as raw floats (0.0/1.0/nan), not
    real Python bool - confirmed via testing: reading a column that
    was written as True/False/None back from Excel gives 1.0/0.0/nan
    as plain floats. apply_narrative_caveat() and
    enforce_company_recognition_cap() both use strict 'is True'
    checks, which silently fail against these float values (nan is
    also falsy here, unlike Python's own truthiness rules where nan
    is truthy - this function deliberately treats nan as not-true).
    """
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

if "llm_recognition_verified" not in results.columns:
    raise SystemExit(
        "No llm_recognition_verified column found - is this really "
        "the LLM validation checkpoint file?"
    )

already_caveated = 0
newly_caveated = 0
skipped_verified = 0
skipped_not_validated = 0

# Same fix as every other script in this session that writes mixed
# types back after an Excel round-trip: a column that's all-blank
# for some rows gets inferred as float64, and writing a string/bool
# into it raises LossySetitemError.
TARGET_COLS = ["engineering_implications", "couchbase_point_of_view", "llm_narrative_caveated"]
for col in TARGET_COLS:
    if col in results.columns:
        results[col] = results[col].astype(object)

for idx, row in results.iterrows():

    if not is_true(row.get("llm_validation")):
        skipped_not_validated += 1
        continue

    if is_true(row.get("llm_narrative_caveated")):
        already_caveated += 1
        continue

    result = row.to_dict()
    result["engineering_implications"] = parse_field(result.get("engineering_implications"))
    result["llm_recognition_verified"] = is_true(result.get("llm_recognition_verified"))

    was_verified = result["llm_recognition_verified"]

    apply_narrative_caveat(result)

    if not was_verified:
        newly_caveated += 1
    else:
        skipped_verified += 1

    # Write the (possibly modified) fields back into the dataframe.
    # engineering_implications and couchbase_point_of_view are the
    # only fields apply_narrative_caveat touches.
    results.at[idx, "engineering_implications"] = str(result["engineering_implications"])
    results.at[idx, "couchbase_point_of_view"] = result["couchbase_point_of_view"]
    results.at[idx, "llm_narrative_caveated"] = result["llm_narrative_caveated"]

print()
print("=========================================================")
print("RETROACTIVE CAVEAT SUMMARY")
print("=========================================================")
print(f"Newly caveated (unverified, fix now applied): {newly_caveated}")
print(f"Already had the caveat (no change needed):     {already_caveated}")
print(f"Verified accounts (no caveat needed):           {skipped_verified}")
print(f"Not yet LLM-validated (skipped):                {skipped_not_validated}")

results.to_excel(CHECKPOINT_FILE, index=False)
print()
print(f"Saved: {CHECKPOINT_FILE}")
print()
print("Next step: re-run run_new_llm_candidates.py. Every account")
print("already shows llm_validation == True, so it will make ZERO")
print("new Bedrock calls and go straight to the merge step, carrying")
print("these caveated results into the final scored file.")
