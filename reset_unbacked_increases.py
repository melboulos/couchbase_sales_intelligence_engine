# =====================================================
# RESET UNBACKED-INCREASE ACCOUNTS FOR RE-PROCESSING
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Before the dollar-backed-increase rule existed,
# reevaluate_middle_band_scores.py could let a score increase
# through with no real evidence backing it (confirmed real case:
# Tube City IMS, 65 -> 85, justified only by "80 customer sites in
# 13 countries" - no dollar figure anywhere).
#
# We only saved the TOTAL score before re-evaluation, not the
# individual workload/realtime/complexity breakdown - so we can't
# perfectly reconstruct the original three numbers for a pure
# retroactive patch. Instead, this finds exactly the accounts with
# an unbacked increase and resets llm_score_reevaluated back to
# False for JUST those - everyone else's re-evaluation stays
# untouched. Re-running reevaluate_middle_band_scores.py afterward
# will then genuinely re-process only this small, targeted subset
# under the new rule.
#
# Usage:
#     python3 reset_unbacked_increases.py
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

reevaluated = df[df["llm_score_reevaluated"].apply(is_true)].copy()
print(f"Total accounts already re-evaluated: {len(reevaluated)}")

unbacked_increase_mask = (
    df["llm_score_reevaluated"].apply(is_true)
    & (df["llm_total_score"] > df["llm_total_score_before_reeval"])
    & (df["llm_magnitude_bucket"] != "large")
)

unbacked_count = unbacked_increase_mask.sum()
print()
print("=========================================================")
print(f"Accounts with an unbacked increase (pre-dates the revert rule): {unbacked_count}")
print("=========================================================")

if unbacked_count > 0:
    print("Examples (up to 10):")
    for _, row in df[unbacked_increase_mask].head(10).iterrows():
        print(f"  - {row['Account Name']}: {row['llm_total_score_before_reeval']:.0f} -> {row['llm_total_score']:.0f}")

df["llm_score_reevaluated"] = df["llm_score_reevaluated"].astype(object)
df.loc[unbacked_increase_mask, "llm_score_reevaluated"] = False

df.to_excel(CHECKPOINT_FILE, index=False)
print()
print(f"Saved: {CHECKPOINT_FILE}")
print()
print("Next: re-run reevaluate_middle_band_scores.py. It will now")
print("naturally re-process only these flagged accounts fresh -")
print("everyone else's re-evaluation is untouched.")
