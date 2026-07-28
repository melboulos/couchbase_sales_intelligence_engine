# =====================================================
# FULL DATA STATUS REPORT
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# One clear picture of exactly where every account currently
# stands - no proposals, no next steps, just the real state of
# the data right now. Safe to run any time, read-only.
#
# Usage:
#     python3 data_status_report.py
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
total_rows = len(df)

print()
print("=" * 60)
print("1. OVERALL")
print("=" * 60)
print(f"Total accounts in the checkpoint: {total_rows}")

validated = df[df["llm_validation"].apply(is_true)]
not_validated = total_rows - len(validated)
print(f"Have gone through the full LLM intelligence call: {len(validated)}")
print(f"Not yet processed at all: {not_validated}")

print()
print("=" * 60)
print("2. RECOGNITION STATUS (of the validated accounts)")
print("=" * 60)
verified = validated[validated["llm_recognition_verified"].apply(is_true)]
unverified = validated[~validated["llm_recognition_verified"].apply(is_true)]
print(f"Verified - real, checkable fact found:     {len(verified)}")
print(f"Unverified - no real fact, scored low:      {len(unverified)}")

print()
print("=" * 60)
print("3. DEFUNCT COMPANIES CAUGHT")
print("=" * 60)
if "llm_defunct_detected" in df.columns:
    defunct = validated[validated["llm_defunct_detected"].apply(is_true)]
    print(f"Flagged as defunct/dissolved/acquired-and-absorbed: {len(defunct)}")
else:
    print("Not tracked in this checkpoint.")

print()
print("=" * 60)
print("4. SCORE EVIDENCE BREAKDOWN (of the verified accounts)")
print("=" * 60)
if "llm_magnitude_bucket" in verified.columns:
    bucket_counts = verified["llm_magnitude_bucket"].value_counts(dropna=False)
    for bucket, count in bucket_counts.items():
        label = "no dollar/employee evidence extractable" if pd.isna(bucket) else f"'{bucket}'"
        print(f"  {label}: {count}")
else:
    print("Not tracked in this checkpoint.")

print()
print("=" * 60)
print("5. IS THIS A REAL SCORE OR AN HONEST DEFAULT?")
print("=" * 60)
if "llm_score_is_default" in df.columns:
    real_score = validated[~validated["llm_score_is_default"].apply(is_true)]
    default_score = validated[validated["llm_score_is_default"].apply(is_true)]
    print(f"Real, differentiated score:  {len(real_score)}")
    print(f"Honest default (insufficient data): {len(default_score)}")
else:
    print("Not tracked in this checkpoint.")

print()
print("=" * 60)
print("6. RE-EVALUATION PASS STATUS")
print("=" * 60)
if "llm_score_reevaluated" in df.columns:
    reevaluated = validated[validated["llm_score_reevaluated"].apply(is_true)]
    not_reevaluated = validated[~validated["llm_score_reevaluated"].apply(is_true)]
    print(f"Have been through the second-look re-evaluation: {len(reevaluated)}")
    print(f"Have NOT been through it yet:                      {len(not_reevaluated)}")

    if "llm_increase_reverted" in df.columns:
        reverted = reevaluated[reevaluated["llm_increase_reverted"].apply(is_true)]
        print(f"  ...of those, had an unbacked increase caught and reverted: {len(reverted)}")
else:
    print("Not tracked in this checkpoint.")

print()
print("=" * 60)
print("7. WEB SEARCH GROUNDING")
print("=" * 60)
if "llm_used_web_search" in df.columns:
    used_search = validated[validated["llm_used_web_search"].apply(is_true)]
    print(f"Facts grounded in a real, live search result: {len(used_search)}")
else:
    print("Not tracked in this checkpoint.")

print()
print("=" * 60)
print("PLAIN-LANGUAGE SUMMARY")
print("=" * 60)
print(f"Of {total_rows} total accounts, {len(validated)} have been fully processed.")
print(f"Of those, {len(verified)} are genuinely recognized companies and")
print(f"{len(unverified)} were honestly scored low because nothing real was found.")
if "llm_score_is_default" in df.columns:
    print(f"{len(real_score)} accounts currently show a real, evidence-backed score.")
    print(f"{len(default_score)} accounts are correctly labeled as a default,")
    print("meaning: don't trust this number as a genuine differentiation.")
if "llm_score_reevaluated" in df.columns and "llm_increase_reverted" in df.columns:
    print(f"{len(not_reevaluated)} verified accounts still have NOT been through")
    print("the second-look re-evaluation pass at all.")
