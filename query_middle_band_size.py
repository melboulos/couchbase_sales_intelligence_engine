# =====================================================
# QUERY: MIDDLE-BAND SIZE (grounded, but no extractable magnitude)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Sizes the exact population that would need a second-pass LLM
# re-evaluation: accounts that are verified, passed the ungrounded-
# evidence check (cited SOME real fact), but had no extractable
# dollar figure or employee count for the magnitude-based code
# correction to grab onto. This is the uncorrected middle band -
# real evidence exists, but nothing currently checks whether the
# score actually reflects it.
#
# Usage:
#     python3 query_middle_band_size.py
# =====================================================

import pandas as pd


def is_true(value):
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1.0:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


CHECKPOINT_FILE = "output/llm_validation_results.xlsx"

print(f"Loading: {CHECKPOINT_FILE}")
df = pd.read_excel(CHECKPOINT_FILE)

validated = df[df["llm_validation"].apply(is_true)].copy()
verified = validated[validated["llm_recognition_verified"].apply(is_true)].copy()
print(f"Verified accounts: {len(verified)}")

grounded = verified[~verified["llm_score_ungrounded"].apply(is_true)].copy()
print(f"Grounded (cited some evidence): {len(grounded)}")

middle_band = grounded[grounded["llm_magnitude_bucket"].isna()].copy()
print()
print("=========================================================")
print(f"MIDDLE BAND (grounded, no extractable magnitude): {len(middle_band)}")
print("=========================================================")
print("These accounts have real evidence but no dollar figure or")
print("employee count for the code-level check to correct. A second")
print("LLM pass targeting just this group would cost roughly:")

AVG_TOKENS_PER_REEVAL_CALL = 400  # much smaller than a full intelligence call
COST_PER_1K = 0.00072
estimated_cost = (len(middle_band) * AVG_TOKENS_PER_REEVAL_CALL / 1000) * COST_PER_1K
print(f"~${estimated_cost:.4f} (rough estimate, {AVG_TOKENS_PER_REEVAL_CALL} tokens/call assumed)")

middle_band.to_excel("output/middle_band_accounts.xlsx", index=False)
print()
print("Saved: output/middle_band_accounts.xlsx (for review)")
