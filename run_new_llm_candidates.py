# =====================================================
# RUN NEW LLM CANDIDATES (post-classification, post-threshold-fix)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# LLM_THRESHOLD was lowered from 50 to 40 in
# modules/deterministic_gate.py, matching Tier 3's own COI
# threshold. This script re-applies the gate under the new
# threshold to the classification-enhanced scored file, then
# runs the REAL, full intelligence call (engineering
# implications, Couchbase POV, discovery questions, independent
# score) for every account that now qualifies.
#
# Reuses validate_accounts() from
# pipeline/llm_validation_pipeline.py directly - the SAME
# threaded, checkpointed function main.py uses - so it
# automatically skips the 512/513 accounts already validated in
# output/llm_validation_results.xlsx and only spends money on
# genuinely new accounts.
#
# This is the expensive, full intelligence call - NOT the cheap
# classification-only call. Expect real time (hours, not
# minutes, for ~2,700 accounts) even though cost stays trivial.
#
# Usage:
#     python3 run_new_llm_candidates.py
# =====================================================

import pandas as pd

from modules.deterministic_gate import deterministic_gate, LLM_THRESHOLD
from pipeline.llm_validation_pipeline import validate_accounts

SCORED_FILE = "output/report1784905185024_Scored_with_classification.xlsx"
FINAL_OUTPUT_FILE = "output/report1784905185024_Scored_FINAL.xlsx"

TEXT_FIELDS_TO_SANITIZE = [
    "workload_profile", "business_model", "database_signal",
    "cloud_signal", "engineering_signal", "industry",
]

print(f"Loading: {SCORED_FILE}")
accounts = pd.read_excel(SCORED_FILE)
print(f"Total accounts: {len(accounts)}")
print(f"Current LLM_THRESHOLD: {LLM_THRESHOLD}")

for col in TEXT_FIELDS_TO_SANITIZE:
    if col in accounts.columns:
        accounts[col] = accounts[col].fillna("")

gate_results = accounts.apply(deterministic_gate, axis=1)
gate_df = pd.DataFrame(gate_results.tolist())

# Same duplicate-column fix as check_new_llm_candidates.py /
# check_threshold_gap.py - drop stale gate columns from the
# ORIGINAL main.py run before merging in the fresh computation.
stale_gate_cols = [c for c in gate_df.columns if c in accounts.columns]
if stale_gate_cols:
    accounts = accounts.drop(columns=stale_gate_cols)

accounts = pd.concat(
    [accounts.reset_index(drop=True), gate_df.reset_index(drop=True)], axis=1
)
accounts = accounts.loc[:, ~accounts.columns.duplicated()]

llm_candidates = accounts[accounts["run_llm"] == True].copy()
print(f"Total accounts qualifying for the LLM under the new threshold: {len(llm_candidates)}")
print()
print("Running the full intelligence call (threaded, checkpointed).")
print("This reuses the SAME checkpoint file as main.py - already")
print("validated accounts will be skipped automatically, only new")
print("ones will actually call Bedrock.")
print()

llm_results = validate_accounts(llm_candidates)

# =====================================================
# FINAL MERGE - same pattern as main.py, with the same
# duplicate-Account-Name-safe dedup fix.
# =====================================================

validated_llm_accounts = llm_results[llm_results["llm_validation"] == True]
print(f"\nValidated: {len(validated_llm_accounts)} / {len(llm_results)} LLM-processed accounts")

llm_merge_columns = [
    "Account Name",
    "llm_run_id",
    "llm_validation",
    "engineering_implications",
    "couchbase_point_of_view",
    "technical_risks_to_validate",
    "discovery_progression",
    "missing_information",
    "llm_specific_fact",
    "llm_company_recognized",
    "llm_recognition_verified",
    "llm_workload_score",
    "llm_realtime_score",
    "llm_complexity_score",
    "llm_total_score",
    "llm_score_capped",
    "llm_narrative_caveated",
    "llm_narrative_generic",
    "llm_discovery_generic",
    "llm_prompt_leakage_detected",
    "llm_constraint_violated",
    "llm_used_web_search",
    "llm_defunct_detected",
    "llm_score_reasoning"
]
llm_merge_columns = [c for c in llm_merge_columns if c in validated_llm_accounts.columns]

validated_llm_accounts_deduped = validated_llm_accounts.drop_duplicates(
    subset="Account Name", keep="first"
)

# The input file already has some of these columns populated from
# the ORIGINAL 513-account main.py run (engineering_implications,
# llm_total_score, etc.) - merging again with overlapping non-key
# columns makes pandas silently create _x/_y suffixed duplicates
# instead of a clean single column, since these aren't the join
# key. Same root cause and same fix as the earlier gate_score/
# run_llm duplicate-column bug: drop the stale columns first.
stale_llm_cols = [
    c for c in llm_merge_columns
    if c != "Account Name" and c in accounts.columns
]
if stale_llm_cols:
    accounts = accounts.drop(columns=stale_llm_cols)

accounts = accounts.merge(
    validated_llm_accounts_deduped[llm_merge_columns],
    on="Account Name",
    how="left"
)
accounts = accounts.loc[:, ~accounts.columns.duplicated()]

accounts.to_excel(FINAL_OUTPUT_FILE, index=False)
print(f"\nSaved: {FINAL_OUTPUT_FILE}")
print("This is the final file - update build_ae_call_list.py's")
print("INPUT_FILE to point here once you're ready to rebuild the")
print("call list.")
