# =====================================================
# FULL BATCH DIAGNOSTICS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# One script covering everything we've been checking by eye each
# time a new sample comes in: defunct-detection catches, score
# convergence rate, web search usage (confirms the resume-bug fix
# is tracking correctly), and a random fact sample for manual
# quality review. Safe to run WHILE rerun_qualified_with_search.py
# is still going, since it just reads the checkpoint file.
#
# Usage:
#     python3 full_batch_diagnostics.py
# =====================================================

import pandas as pd

CHECKPOINT_FILE = "output/llm_validation_results.xlsx"
FACT_SAMPLE_SIZE = 15
RANDOM_SEED = 7


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
print(f"Total rows: {len(df)}")

validated = df[df["llm_validation"].apply(is_true)].copy()
print(f"Validated (LLM-processed): {len(validated)}")

if len(validated) == 0:
    print("Nothing validated yet - nothing to analyze.")
    raise SystemExit()

print()
print("=========================================================")
print("1. DEFUNCT DETECTION")
print("=========================================================")
if "llm_defunct_detected" in validated.columns:
    defunct = validated[validated["llm_defunct_detected"].apply(is_true)]
    print(f"Flagged as defunct: {len(defunct)} / {len(validated)} ({100*len(defunct)/len(validated):.1f}%)")
    for _, row in defunct.iterrows():
        print(f"  - {row['Account Name']}: score={row.get('llm_total_score')} | {str(row.get('llm_specific_fact'))[:100]}")
else:
    print("Column not present in this checkpoint (predates the defunct-detection fix).")

print()
print("=========================================================")
print("2. SCORE CONVERGENCE")
print("=========================================================")
if "llm_total_score" in validated.columns:
    score_counts = validated["llm_total_score"].value_counts().sort_values(ascending=False)
    print("Most common total scores:")
    for score, count in score_counts.head(10).items():
        pct = 100 * count / len(validated)
        print(f"  {score:>5}: {count:>4} accounts ({pct:>5.1f}%)")

    # Specifically check the known 25/20/20=65 convergence pattern
    if all(c in validated.columns for c in ["llm_workload_score", "llm_realtime_score", "llm_complexity_score"]):
        pattern_251515 = validated[
            (validated["llm_workload_score"] == 25) &
            (validated["llm_realtime_score"] == 20) &
            (validated["llm_complexity_score"] == 20)
        ]
        pct = 100 * len(pattern_251515) / len(validated)
        print(f"\nExact 25/20/20=65 pattern: {len(pattern_251515)} / {len(validated)} ({pct:.1f}%)")

print()
print("=========================================================")
print("3. WEB SEARCH USAGE (confirms resume-fix is tracking correctly)")
print("=========================================================")
if "llm_used_web_search" in validated.columns:
    used_search = validated["llm_used_web_search"].apply(is_true).sum()
    never_touched = validated["llm_used_web_search"].isna().sum()
    skipped_or_failed = len(validated) - used_search - never_touched
    print(f"Used real search results:              {used_search}")
    print(f"Skipped/failed (no location, or error): {skipped_or_failed}")
    print(f"Never touched by new pipeline (old data): {never_touched}")
else:
    print("Column not present in this checkpoint.")

print()
print("=========================================================")
print(f"4. RANDOM FACT SAMPLE ({FACT_SAMPLE_SIZE} accounts, for manual quality review)")
print("=========================================================")
sample_size = min(FACT_SAMPLE_SIZE, len(validated))
sample = validated.sample(n=sample_size, random_state=RANDOM_SEED)
for _, row in sample.iterrows():
    print()
    print(f"--- {row['Account Name']} (score={row.get('llm_total_score')}) ---")
    print(f"  Fact: {row.get('llm_specific_fact')}")
