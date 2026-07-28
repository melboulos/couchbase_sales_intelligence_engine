# =====================================================
# INSPECT ONE ACCOUNT - RAW VALUES
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Shows exactly what's stored for one specific account, with the
# real Python type of each value - not an interpreted True/False,
# the actual raw thing sitting in the file. Used to check whether
# the magnitude-bucket-disappearing issue is a real data problem or
# another Excel-type quirk like the ones found earlier this session.
#
# Usage:
#     python3 inspect_one_account.py "Account Name Here"
# =====================================================

import sys
import pandas as pd

if len(sys.argv) < 2:
    print('Usage: python3 inspect_one_account.py "Account Name"')
    raise SystemExit(1)

account_name = sys.argv[1]
CHECKPOINT_FILE = "output/llm_validation_results.xlsx"

print(f"Loading: {CHECKPOINT_FILE}")
df = pd.read_excel(CHECKPOINT_FILE)

matches = df[df["Account Name"].astype(str).str.contains(account_name, case=False, na=False)]
print(f"Found {len(matches)} matching row(s) for '{account_name}'")

FIELDS_TO_SHOW = [
    "Account Name", "llm_specific_fact", "llm_score_reasoning",
    "llm_recognition_verified", "llm_magnitude_bucket",
    "llm_score_is_default", "llm_workload_score", "llm_realtime_score",
    "llm_complexity_score", "llm_total_score", "llm_score_reevaluated",
    "llm_total_score_before_reeval", "llm_increase_reverted",
]

for idx, row in matches.iterrows():
    print()
    print("=" * 60)
    print(f"ROW INDEX {idx}")
    print("=" * 60)
    for field in FIELDS_TO_SHOW:
        if field in row.index:
            value = row[field]
            print(f"  {field}: {value!r}  (type: {type(value).__name__})")
        else:
            print(f"  {field}: <column not present>")
