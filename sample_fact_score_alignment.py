# =====================================================
# RANDOM SAMPLE: FACT-VS-SCORE ALIGNMENT CHECK
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Pulls a truly random sample of verified accounts (llm_recognition_
# verified == True) for a blind judgment: does the score actually
# match what the fact itself says, regardless of whether we
# recognize the company? Excludes unrecognized accounts entirely,
# per the user's framing - those aren't accounts we'd sell to
# anyway, and aren't part of this trust question.
#
# Usage:
#     python3 sample_fact_score_alignment.py
# =====================================================

import pandas as pd

CHECKPOINT_FILE = "output/llm_validation_results.xlsx"
OUTPUT_FILE = "output/fact_score_alignment_sample.xlsx"
SAMPLE_SIZE = 60
RANDOM_SEED = 99


def is_true(value):
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1.0:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


print(f"Loading: {CHECKPOINT_FILE}")
df = pd.read_excel(CHECKPOINT_FILE)

validated = df[df["llm_validation"].apply(is_true)]
verified = validated[validated["llm_recognition_verified"].apply(is_true)]

print(f"Total validated: {len(validated)}")
print(f"Verified (excludes unrecognized accounts): {len(verified)}")

sample_size = min(SAMPLE_SIZE, len(verified))
sample = verified.sample(n=sample_size, random_state=RANDOM_SEED).copy()

display_cols = [
    "Account Name", "llm_specific_fact", "llm_workload_score",
    "llm_realtime_score", "llm_complexity_score", "llm_total_score",
    "llm_score_reasoning",
]
display_cols = [c for c in display_cols if c in sample.columns]
sample = sample[display_cols].reset_index(drop=True)

sample.to_excel(OUTPUT_FILE, index=False)

print()
print(f"Pulled a truly random sample of {len(sample)} verified accounts.")
print(f"Saved to: {OUTPUT_FILE}")
print()
for i, row in sample.iterrows():
    print(f"--- [{i+1}] {row['Account Name']} ---")
    print(f"  Fact: {row.get('llm_specific_fact')}")
    print(f"  Scores: workload={row.get('llm_workload_score')}, realtime={row.get('llm_realtime_score')}, "
          f"complexity={row.get('llm_complexity_score')}, total={row.get('llm_total_score')}")
    print(f"  Reasoning: {row.get('llm_score_reasoning')}")
    print()
