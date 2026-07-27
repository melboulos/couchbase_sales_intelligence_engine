# =====================================================
# QUERY: DEFUNCT-DETECTED ACCOUNTS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Shows every account currently flagged by
# detect_defunct_company() - the fact that triggered it, the
# resulting (capped) score, and whether the visible caveat is
# set. Safe to run WHILE rerun_qualified_with_search.py is still
# going, since it just reads the checkpoint file, which updates
# every 25 completions.
#
# Usage:
#     python3 query_defunct_accounts.py
# =====================================================

import pandas as pd

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
df = pd.read_excel(CHECKPOINT_FILE)
print(f"Total rows in checkpoint so far: {len(df)}")

validated = df[df["llm_validation"].apply(is_true)]
print(f"Validated (LLM-processed) so far: {len(validated)}")

defunct = validated[validated["llm_defunct_detected"].apply(is_true)]
print(f"Flagged as defunct: {len(defunct)}")

print()
print("=========================================================")
print("DEFUNCT-DETECTED ACCOUNTS")
print("=========================================================")

if len(defunct) == 0:
    print("None found so far in the processed accounts.")
else:
    for _, row in defunct.iterrows():
        print()
        print(f"--- {row['Account Name']} ---")
        print(f"  Total score: {row.get('llm_total_score')}")
        print(f"  Caveated: {row.get('llm_narrative_caveated')}")
        print(f"  Fact: {row.get('llm_specific_fact')}")

print()
print("=========================================================")
defunct_rate = 100 * len(defunct) / len(validated) if len(validated) > 0 else 0
print(f"Defunct rate so far: {len(defunct)} / {len(validated)} ({defunct_rate:.2f}%)")
