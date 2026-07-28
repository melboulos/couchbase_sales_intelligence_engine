# =====================================================
# QUERY: RE-EVALUATION BEFORE/AFTER REPORT
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Shows exactly what changed for every account touched by
# reevaluate_middle_band_scores.py - original score, corrected
# score, delta, and the model's stated reasoning. Safe to run any
# time after that script has processed at least some accounts.
#
# Usage:
#     python3 query_reeval_before_after.py
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

if "llm_score_reevaluated" not in df.columns:
    print("No re-evaluation data found - has reevaluate_middle_band_scores.py been run yet?")
    raise SystemExit()

reevaluated = df[df["llm_score_reevaluated"].apply(is_true)].copy()
print(f"Total accounts re-evaluated so far: {len(reevaluated)}")

if len(reevaluated) == 0:
    print("Nothing to report yet.")
    raise SystemExit()

reevaluated["delta"] = reevaluated["llm_total_score"] - reevaluated["llm_total_score_before_reeval"]

raised = reevaluated[reevaluated["delta"] > 0]
lowered = reevaluated[reevaluated["delta"] < 0]
unchanged = reevaluated[reevaluated["delta"] == 0]

print()
print("=========================================================")
print("SUMMARY")
print("=========================================================")
print(f"Raised:    {len(raised)} ({100*len(raised)/len(reevaluated):.1f}%)")
print(f"Lowered:   {len(lowered)} ({100*len(lowered)/len(reevaluated):.1f}%)")
print(f"Unchanged: {len(unchanged)} ({100*len(unchanged)/len(reevaluated):.1f}%)")
print()
print(f"Average delta (all accounts): {reevaluated['delta'].mean():+.1f}")
if len(raised) > 0:
    print(f"Average raise (when raised):   {raised['delta'].mean():+.1f}")
if len(lowered) > 0:
    print(f"Average lower (when lowered):   {lowered['delta'].mean():+.1f}")

print()
print("=========================================================")
print("BEFORE / AFTER, EVERY ACCOUNT")
print("=========================================================")
display_df = reevaluated.sort_values("delta", ascending=False)
for _, row in display_df.iterrows():
    before = row["llm_total_score_before_reeval"]
    after = row["llm_total_score"]
    delta = row["delta"]
    arrow = "no change" if delta == 0 else (f"+{delta:.0f}" if delta > 0 else f"{delta:.0f}")
    print()
    print(f"--- {row['Account Name']}: {before:.0f} -> {after:.0f} ({arrow}) ---")
    print(f"  Fact: {str(row.get('llm_specific_fact'))[:150]}")
    print(f"  Reasoning: {row.get('llm_reeval_reasoning')}")
