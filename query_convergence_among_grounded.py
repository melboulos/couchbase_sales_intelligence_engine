# =====================================================
# QUERY: CONVERGENCE AMONG GENUINELY GROUNDED ACCOUNTS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# detect_ungrounded_score() confirmed 24.2% of verified accounts
# had ZERO evidence in their reasoning and correctly capped them.
# This checks the harder, more important question: among the
# accounts that DID cite a real number (llm_score_ungrounded ==
# False, genuinely grounded, untouched by the cap), how many STILL
# land on the exact same 25/20/20=65 combination anyway? If that
# number is high, it means citing evidence doesn't actually change
# the outcome - the same "letter not spirit" pattern already
# confirmed for the narrative fix, just on the scoring side.
#
# Usage:
#     python3 query_convergence_among_grounded.py
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

grounded = verified[~verified["llm_score_ungrounded"].apply(is_true)].copy()
print(f"Genuinely grounded accounts (cited a real number, not capped): {len(grounded)}")

exact_match = grounded[
    (grounded["llm_workload_score"] == 25) &
    (grounded["llm_realtime_score"] == 20) &
    (grounded["llm_complexity_score"] == 20)
]

pct = 100 * len(exact_match) / len(grounded) if len(grounded) > 0 else 0
print()
print("=========================================================")
print(f"Exact 25/20/20=65 among GROUNDED accounts: {len(exact_match)} / {len(grounded)} ({pct:.1f}%)")
print("=========================================================")

if len(exact_match) > 0:
    print()
    print("Sample of grounded-but-still-25/20/20 accounts (up to 10):")
    for _, row in exact_match.head(10).iterrows():
        print()
        print(f"--- {row['Account Name']} ---")
        print(f"  Fact: {row.get('llm_specific_fact')}")
        print(f"  Reasoning: {str(row.get('llm_score_reasoning'))[:200]}")

print()
print("If this percentage is still high, citing a real number isn't")
print("actually changing the scoring OUTCOME - the number is present")
print("but not influencing the decision. That would mean this fix")
print("caught the worst cases (zero evidence) but not the subtler,")
print("more common one (evidence present but ignored).")
