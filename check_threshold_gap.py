# =====================================================
# CHECK THE TIER3-VS-LLM_THRESHOLD GAP
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# deterministic_gate.py requires gate_score >= 50 (LLM_THRESHOLD)
# to send an account to the LLM, but Tier 3 only requires
# overall_coi >= 40 (scoring_engine.py). check_new_llm_candidates.py
# found that classification-pre-pass-upgraded accounts almost never
# clear the gate despite landing in Tier 2/3, because their gate
# score has no keyword-match bonus and lacks technical_environment/
# company_context points entirely.
#
# This checks how many accounts ACROSS THE WHOLE FILE - not just
# classification-upgraded ones - sit in the 40-49 gap: correctly
# Tier 3 by COI, but excluded from the LLM by the higher gate
# threshold. This is a pre-existing gap (the LLM_THRESHOLD = 50
# comment already flagged it as "NEEDS RECALIBRATION" before this
# session touched anything), not something the classification
# pre-pass created - it just made the gap visible at scale.
#
# Usage:
#     python3 check_threshold_gap.py
# =====================================================

import pandas as pd

from modules.deterministic_gate import deterministic_gate, LLM_THRESHOLD

SCORED_FILE = "output/report1784905185024_Scored_with_classification.xlsx"

AVG_TOKENS_PER_CALL = 2663
COST_PER_1K_TOKENS = 0.00072

print(f"Loading: {SCORED_FILE}")
accounts = pd.read_excel(SCORED_FILE)
print(f"Total accounts: {len(accounts)}")
print(f"Current LLM_THRESHOLD: {LLM_THRESHOLD}")

TEXT_FIELDS_TO_SANITIZE = [
    "workload_profile", "business_model", "database_signal",
    "cloud_signal", "engineering_signal", "industry",
]
for col in TEXT_FIELDS_TO_SANITIZE:
    if col in accounts.columns:
        accounts[col] = accounts[col].fillna("")

gate_results = accounts.apply(deterministic_gate, axis=1)
gate_df = pd.DataFrame(gate_results.tolist())

# Same bug/fix as check_new_llm_candidates.py: the file already has
# gate-result columns from the ORIGINAL main.py run. Drop them before
# merging in the fresh computation, since pandas' duplicate-column
# dedup keeps the FIRST occurrence (the stale value) by default.
stale_gate_cols = [c for c in gate_df.columns if c in accounts.columns]
if stale_gate_cols:
    accounts = accounts.drop(columns=stale_gate_cols)

accounts = pd.concat(
    [accounts.reset_index(drop=True), gate_df.reset_index(drop=True)], axis=1
)
accounts = accounts.loc[:, ~accounts.columns.duplicated()]

# The gap: Tier 3+ by COI, but gate_score below LLM_THRESHOLD
tier3_plus = accounts[accounts["overall_coi"] >= 40]
gap_accounts = tier3_plus[
    (tier3_plus["gate_score"] < LLM_THRESHOLD) & (tier3_plus["run_llm"] == False)
]

print()
print("=========================================================")
print(f"Accounts with overall_coi >= 40 (Tier 3+): {len(tier3_plus)}")
print(f"Of those, currently excluded by gate_score < {LLM_THRESHOLD}: {len(gap_accounts)}")
print("=========================================================")

came_from_classification = gap_accounts["company_signal_reason"].astype(str).str.contains(
    "LLM classification", na=False
)
print(f"  ...from the classification pre-pass: {came_from_classification.sum()}")
print(f"  ...pre-existing (not from classification pre-pass): {(~came_from_classification).sum()}")

print()
print("gate_score distribution for the gap accounts:")
print(gap_accounts["gate_score"].describe().to_string())

estimated_tokens = len(gap_accounts) * AVG_TOKENS_PER_CALL
estimated_cost = (estimated_tokens / 1000) * COST_PER_1K_TOKENS
print()
print(f"If LLM_THRESHOLD were lowered to 40 (matching Tier 3), "
      f"estimated cost for these {len(gap_accounts)} accounts: "
      f"${estimated_cost:.4f}")

gap_accounts.to_excel("output/tier3_below_llm_threshold_gap.xlsx", index=False)
print()
print("Saved: output/tier3_below_llm_threshold_gap.xlsx")
