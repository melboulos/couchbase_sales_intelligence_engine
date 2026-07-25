# =====================================================
# CHECK NEW LLM CANDIDATES POST-CLASSIFICATION
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# The classification pre-pass upgraded 3,417 accounts from
# Unknown to a real category and recomputed their COI - but it
# does NOT automatically send them through the full LLM
# intelligence call. This checks how many of them now clear
# the SAME deterministic gate everything else goes through,
# beyond the original 513 already in llm_validation_results.xlsx,
# so we know the real, incremental scope (and cost) before
# running anything.
#
# Usage:
#     python3 check_new_llm_candidates.py
# =====================================================

import pandas as pd

from modules.deterministic_gate import deterministic_gate

SCORED_FILE = "output/report1784905185024_Scored_with_classification.xlsx"
EXISTING_LLM_RESULTS = "output/llm_validation_results.xlsx"

AVG_TOKENS_PER_CALL = 2663  # measured from the real 513-account intelligence run
COST_PER_1K_TOKENS = 0.00072

print(f"Loading: {SCORED_FILE}")
accounts = pd.read_excel(SCORED_FILE)
print(f"Total accounts: {len(accounts)}")

# Blank cells round-trip through Excel as NaN, not empty string.
# deterministic_gate does string concatenation on workload_profile
# (and reads several other text fields), which crashes on NaN -
# this never happens inside the live main.py pipeline (which never
# round-trips through Excel mid-flow), but does happen here since
# this script re-loads an already-saved file. Sanitize before
# calling the gate.
TEXT_FIELDS_TO_SANITIZE = [
    "workload_profile", "business_model", "database_signal",
    "cloud_signal", "engineering_signal", "industry",
]
for col in TEXT_FIELDS_TO_SANITIZE:
    if col in accounts.columns:
        accounts[col] = accounts[col].fillna("")

print(f"Loading existing LLM results: {EXISTING_LLM_RESULTS}")
existing_results = pd.read_excel(EXISTING_LLM_RESULTS)
already_validated_names = set(
    existing_results[existing_results["llm_validation"] == True]["Account Name"]
)
print(f"Already validated via the full intelligence call: {len(already_validated_names)}")

gate_results = accounts.apply(deterministic_gate, axis=1)
gate_df = pd.DataFrame(gate_results.tolist())

# The file already has gate-result columns from the ORIGINAL main.py
# run, computed before classification/scale-tier changes. Drop them
# before merging in the fresh computation - otherwise pandas'
# duplicate-column dedup keeps the FIRST occurrence (the stale
# value), silently discarding the fresh one and corrupting every
# result below.
stale_gate_cols = [c for c in gate_df.columns if c in accounts.columns]
if stale_gate_cols:
    accounts = accounts.drop(columns=stale_gate_cols)

accounts = pd.concat(
    [accounts.reset_index(drop=True), gate_df.reset_index(drop=True)], axis=1
)
accounts = accounts.loc[:, ~accounts.columns.duplicated()]

all_llm_candidates = accounts[accounts["run_llm"] == True]

print(f"Total accounts now clearing the gate: {len(all_llm_candidates)}")

new_candidates = all_llm_candidates[
    ~all_llm_candidates["Account Name"].isin(already_validated_names)
]

# Also flag which of the new candidates came specifically from the
# classification pre-pass, vs. any that might have crossed the gate
# some other way (e.g. the insurance/pharma base-rating fix).
came_from_classification = new_candidates["company_signal_reason"].astype(str).str.contains(
    "LLM classification", na=False
)

print()
print("=========================================================")
print("NEW LLM CANDIDATES (not already in llm_validation_results.xlsx)")
print("=========================================================")
print(f"New candidates total: {len(new_candidates)}")
print(f"  ...from the classification pre-pass specifically: {came_from_classification.sum()}")
print(f"  ...from other causes (e.g. insurance/pharma rating fix): {(~came_from_classification).sum()}")

if len(new_candidates) > 0:
    print()
    print("Breakdown by priority_tier:")
    print(new_candidates["priority_tier"].value_counts().to_string())

estimated_tokens = len(new_candidates) * AVG_TOKENS_PER_CALL
estimated_cost = (estimated_tokens / 1000) * COST_PER_1K_TOKENS

print()
print(f"Estimated cost to run the full intelligence call for these "
      f"{len(new_candidates)} new accounts: ${estimated_cost:.4f}")
print("(Ballpark using the average from the real 513-account run -")
print("actual cost will vary with how much enrichment data each")
print("account has.)")

new_candidates.to_excel("output/new_llm_candidates_post_classification.xlsx", index=False)
print()
print("Saved: output/new_llm_candidates_post_classification.xlsx")
print("(review this list before deciding whether to run it)")
