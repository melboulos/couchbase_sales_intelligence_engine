# =====================================================
# CALL BRIEF CONTENT SPOT CHECK
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Pulls real Call Brief content (engineering_implications,
# couchbase_point_of_view, llm_specific_fact) from the final
# scored file for manual quality/accuracy review - stratified
# by tier (Tier 1/2 first, since those matter most) and by
# verified vs caveated status, so the sample shows both what
# "good" output looks like and what the caveat warning
# actually looks like in context.
#
# Usage:
#     python3 spot_check_call_briefs.py
# =====================================================

import ast
import pandas as pd

INPUT_FILE = "output/report1784905185024_Scored_FINAL.xlsx"
OUTPUT_FILE = "output/call_brief_spot_check_sample.xlsx"

RANDOM_SEED = 57


def parse_field(value):
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def first_implication(value):
    parsed = parse_field(value)
    if isinstance(parsed, list) and parsed:
        return parsed[0]
    return str(parsed)


print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)
print(f"Total accounts: {len(accounts)}")

qualified = accounts[accounts["llm_validation"] == True].copy()
print(f"LLM-qualified accounts: {len(qualified)}")

qualified["is_caveated"] = qualified["llm_narrative_caveated"].isin([True, 1, 1.0])
print(f"  Verified: {(~qualified['is_caveated']).sum()}")
print(f"  Caveated: {qualified['is_caveated'].sum()}")

sample_frames = []

# Tier 1/2 first - highest stakes, smallest population, take everyone
# available up to a cap.
for tier in ["Tier 1 Strategic", "Tier 2 Strong Target"]:
    pool = qualified[qualified["priority_tier"] == tier]
    n = min(15, len(pool))
    if n > 0:
        sample_frames.append(pool.sample(n=n, random_state=RANDOM_SEED))

# Tier 3, split evenly between verified and caveated so both are
# represented, not just whichever happens to be more common.
tier3 = qualified[qualified["priority_tier"] == "Tier 3 Nurture"]
for is_caveated_flag, label in [(False, "verified"), (True, "caveated")]:
    pool = tier3[tier3["is_caveated"] == is_caveated_flag]
    n = min(15, len(pool))
    if n > 0:
        sample_frames.append(pool.sample(n=n, random_state=RANDOM_SEED))

sample = pd.concat(sample_frames).drop_duplicates(subset="Account Name")
sample = sample.sort_values(["priority_tier", "overall_coi"], ascending=[True, False])

sample["engineering_implication_sample"] = sample["engineering_implications"].apply(first_implication)

display_cols = [
    "Account Name", "priority_tier", "overall_coi", "is_caveated",
    "llm_specific_fact", "llm_total_score", "engineering_implication_sample",
    "couchbase_point_of_view",
]
display_cols = [c for c in display_cols if c in sample.columns]
sample = sample[display_cols].reset_index(drop=True)

sample.to_excel(OUTPUT_FILE, index=False)

print()
print("=========================================================")
print(f"CALL BRIEF SPOT-CHECK SAMPLE ({len(sample)} accounts)")
print("=========================================================")
for _, row in sample.iterrows():
    print()
    print(f"--- {row['Account Name']} | {row['priority_tier']} | COI {row['overall_coi']} | "
          f"{'CAVEATED' if row['is_caveated'] else 'verified'} ---")
    print(f"  Fact: {row.get('llm_specific_fact', '')}")
    print(f"  First implication: {row.get('engineering_implication_sample', '')}")
    print(f"  Couchbase POV: {str(row.get('couchbase_point_of_view', ''))[:200]}")

print()
print(f"Saved full sample to: {OUTPUT_FILE}")
