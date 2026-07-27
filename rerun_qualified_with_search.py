# =====================================================
# RERUN ALL QUALIFIED ACCOUNTS WITH WEB SEARCH GROUNDING
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# All 3,523 currently-qualified accounts already show
# llm_validation == True in the checkpoint, from the run BEFORE
# web search grounding and the specific_constraint/
# distributed_solution schema split existed. Simply re-running
# main.py or run_new_llm_candidates.py would SKIP all of them -
# that's the whole point of the resume logic, so a normal run
# doesn't waste money re-processing already-done accounts.
#
# This script deliberately does the opposite: it resets these
# specific accounts back to "needs processing" in the checkpoint,
# then reuses the SAME proven threaded/checkpointed
# validate_accounts() function everything else uses, so they get
# genuinely fresh output - real search-grounded facts, the new
# specific_constraint/distributed_solution fields, all of it -
# instead of the older, un-grounded version.
#
# REAL COST WARNING - this is not a small test:
#   ~3,523 accounts, ~586 without a known location will skip
#   search automatically (same rule as the live pipeline) but
#   still make the Bedrock call.
#   Bedrock: ~$6-7 (consistent with the earlier real run's rate)
#   Serper: ~2,900-3,000 queries (well within a 52,479 balance)
#   Time: several hours, threaded 5 at a time - this is the same
#   order of magnitude as the original 3,018-account run, plus
#   the added network round-trip per account for search.
#
# Usage:
#     python3 rerun_qualified_with_search.py
# =====================================================

import pandas as pd

from pipeline.llm_validation_pipeline import validate_accounts
from modules.deterministic_gate import deterministic_gate

SCORED_FILE = "output/report1784905185024_Scored_FINAL.xlsx"
CHECKPOINT_FILE = "output/llm_validation_results.xlsx"
FINAL_OUTPUT_FILE = "output/report1784905185024_Scored_RESEARCHED.xlsx"

TEXT_FIELDS_TO_SANITIZE = [
    "workload_profile", "business_model", "database_signal",
    "cloud_signal", "engineering_signal", "industry",
]

print(f"Loading: {SCORED_FILE}")
accounts = pd.read_excel(SCORED_FILE)
print(f"Total accounts: {len(accounts)}")

for col in TEXT_FIELDS_TO_SANITIZE:
    if col in accounts.columns:
        accounts[col] = accounts[col].fillna("")

gate_results = accounts.apply(deterministic_gate, axis=1)
gate_df = pd.DataFrame(gate_results.tolist())
stale_gate_cols = [c for c in gate_df.columns if c in accounts.columns]
if stale_gate_cols:
    accounts = accounts.drop(columns=stale_gate_cols)
accounts = pd.concat(
    [accounts.reset_index(drop=True), gate_df.reset_index(drop=True)], axis=1
)
accounts = accounts.loc[:, ~accounts.columns.duplicated()]

qualified = accounts[accounts["run_llm"] == True].copy()
print(f"Currently-qualified accounts to force-rerun: {len(qualified)}")

print(f"Loading checkpoint: {CHECKPOINT_FILE}")
checkpoint = pd.read_excel(CHECKPOINT_FILE)
print(f"Checkpoint rows before reset: {len(checkpoint)}")

qualified_names = set(qualified["Account Name"])

# BUG FIX, found via real cost impact: the original version of this
# reset unconditionally reset EVERY qualified account back to
# "needs processing" on EVERY invocation of this script - including
# accounts that had ALREADY been successfully redone with the new
# pipeline (web search grounding, schema-split fields) in a PRIOR
# run of this same script. Since validate_accounts() determines
# "already done" purely from the llm_validation flag in this same
# checkpoint, resetting it wiped out that status every time,
# silently discarding real completed work and real spent Bedrock/
# Serper cost on every resume - confirmed via real numbers: 250
# validated accounts (after a retroactive fix) dropped to 149 after
# a single resume, which should be mathematically impossible if
# resuming worked correctly.
#
# Fix: only reset an account if it does NOT already show
# llm_used_web_search - a field that only exists on rows already
# processed by the CURRENT (post-search-integration) pipeline. Old,
# pre-search rows never have this field at all (NaN), so they still
# get correctly reset and reprocessed. Already-redone rows are left
# alone, making this script genuinely safe to stop and resume any
# number of times.
if "llm_used_web_search" in checkpoint.columns:
    already_redone_mask = checkpoint["llm_used_web_search"].notna()
else:
    already_redone_mask = pd.Series(False, index=checkpoint.index)

reset_mask = checkpoint["Account Name"].isin(qualified_names) & ~already_redone_mask
reset_count = reset_mask.sum()
already_redone_count = (
    checkpoint["Account Name"].isin(qualified_names) & already_redone_mask
).sum()

# Force these specific rows back to "needs processing" - this is
# the deliberate override that makes validate_accounts() actually
# re-call the LLM for them, instead of skipping them as already done.
checkpoint["llm_validation"] = checkpoint["llm_validation"].astype(object)
checkpoint.loc[reset_mask, "llm_validation"] = False

print(f"Reset {reset_count} accounts back to 'needs processing'")
print(f"Left alone (already redone under the new pipeline): {already_redone_count}")
checkpoint.to_excel(CHECKPOINT_FILE, index=False)
print(f"Saved reset checkpoint: {CHECKPOINT_FILE}")

print()
print("Starting full re-run with web search grounding + schema-split fields...")
print("This will take several hours. Checkpoints save every 25 completions,")
print("so it's safe to interrupt and resume by re-running this same script.")
print()

llm_results = validate_accounts(qualified)

validated_llm_accounts = llm_results[llm_results["llm_validation"] == True]
print(f"\nValidated: {len(validated_llm_accounts)} / {len(llm_results)}")

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
print()
print("This is the new, search-grounded final file. Once you've reviewed it,")
print("update build_ae_call_list.py's INPUT_FILE to point here and rebuild")
print("the call list.")
