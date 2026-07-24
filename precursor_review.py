# =====================================================
# PRECURSOR REVIEW
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Runs the full enrichment + scoring + deterministic gate
# pipeline (same stages as main.py) on a new account file,
# WITHOUT calling the LLM at all. This lets you see exactly
# how many accounts would be sent to Bedrock - and what that
# would cost - before actually spending anything.
#
# Usage:
#     python3 precursor_review.py
#
# Edit INPUT_FILE below to point at your new 9k-account file.
# =====================================================

import pandas as pd

from pipeline.loader import load_accounts
from pipeline.enrichment_pipeline import (
    normalize_accounts,
    classify_industries,
    enrich_company_intelligence
)
from pipeline.technology_pipeline import enrich_technology
from pipeline.account_enrichment_pipeline import enrich_accounts
from pipeline.account_pipeline import enrich_account_intelligence
from pipeline.company_archetype_pipeline import enrich_company_archetypes
from pipeline.scoring_pipeline import score_accounts
from modules.deterministic_gate import deterministic_gate
from modules.opportunity_explainer import generate_opportunity_explanation


# =====================================================
# CONFIG - EDIT THIS
# =====================================================

INPUT_FILE = "input/report1784905185024.xls"   # <-- change to your actual file path
OUTPUT_FILE = "output/precursor_review.xlsx"

# Average total tokens per LLM call, measured from real
# Bedrock test runs this session (Netspend/Trumid/UCB after
# the llm_specific_fact fix): (2716+2613+2717)/3 ~= 2682.
# This is a real, observed average - not a guess - but it
# will drift as prompt content changes, so re-measure this
# periodically rather than trusting it forever.
AVG_TOKENS_PER_CALL = 2682

# Real Bedrock on-demand rate for Llama 70B-class models,
# confirmed this session (see pipeline/llm_validation_pipeline.py
# for sourcing). NOT the old $0.99/1K constant.
COST_PER_1K_TOKENS = 0.00072


# =====================================================
# LOAD + ENRICH + SCORE
#
# Same stages as main.py, in the same order. No LLM calls
# happen anywhere in this script.
# =====================================================

print("Starting precursor review (no LLM calls will be made)")
print("-------------------------------------------------------")

accounts = load_accounts(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts")

print("\nColumns found:")
for col in accounts.columns:
    print(f"- {col}")

print("\nRunning normalization...")
accounts = normalize_accounts(accounts)

print("\nRunning industry classification...")
accounts = classify_industries(accounts)

print("\nRunning company intelligence...")
accounts = enrich_company_intelligence(accounts)

print("\nRunning technology enrichment...")
accounts = enrich_technology(accounts)

print("\nRunning account intelligence...")
accounts = enrich_account_intelligence(accounts)

print("\nRunning account enrichment...")
accounts = enrich_accounts(accounts)

accounts = accounts.loc[:, ~accounts.columns.duplicated()]
print("\nDuplicate columns cleaned")

print("\nClassifying company archetypes...")
accounts = enrich_company_archetypes(accounts)

print("\nCalculating Couchbase Opportunity Index...")
accounts = score_accounts(accounts)

print("\nGenerating opportunity explanations...")
opportunity_results = accounts.apply(generate_opportunity_explanation, axis=1)
opportunity_results = pd.DataFrame(opportunity_results.tolist())
accounts = pd.concat(
    [accounts.reset_index(drop=True), opportunity_results.reset_index(drop=True)],
    axis=1
)


# =====================================================
# DETERMINISTIC GATE - THIS IS THE KEY STEP
#
# Everything above this point is local computation (no
# network calls, no cost). This step decides which accounts
# WOULD be sent to the LLM in a real run.
# =====================================================

print("\nRunning deterministic gate...")

gate_results = accounts.apply(deterministic_gate, axis=1)
gate_results = pd.DataFrame(gate_results.tolist())

accounts = pd.concat(
    [accounts.reset_index(drop=True), gate_results.reset_index(drop=True)],
    axis=1
)

accounts = accounts.loc[:, ~accounts.columns.duplicated()]


# =====================================================
# ROLL-UP SUMMARY
# =====================================================

total_accounts = len(accounts)
llm_candidates = accounts[accounts["run_llm"] == True]
llm_candidate_count = len(llm_candidates)
skip_count = total_accounts - llm_candidate_count

estimated_tokens = llm_candidate_count * AVG_TOKENS_PER_CALL
estimated_cost = (estimated_tokens / 1000) * COST_PER_1K_TOKENS

print()
print("=========================================================")
print("PRECURSOR REVIEW - ROLL-UP SUMMARY")
print("=========================================================")
print(f"Total accounts loaded:            {total_accounts}")
print(f"Would be sent to LLM (run_llm):   {llm_candidate_count}")
print(f"Would be SKIPPED (no LLM cost):   {skip_count}")
print()

if "priority_tier" in accounts.columns:
    print("Breakdown by priority_tier (ALL accounts):")
    print(accounts["priority_tier"].value_counts().to_string())
    print()

if "gate_decision" in accounts.columns:
    print("Breakdown by gate_decision:")
    print(accounts["gate_decision"].value_counts().to_string())
    print()

print("-------------------------------------------------------")
print("ESTIMATED LLM COST IF RUN NOW")
print("-------------------------------------------------------")
print(f"Assumed avg tokens/call:  {AVG_TOKENS_PER_CALL} "
      f"(measured from real test runs - re-verify periodically)")
print(f"Estimated total tokens:   {estimated_tokens:,}")
print(f"Rate:                     ${COST_PER_1K_TOKENS}/1K tokens "
      f"(~$0.72/million, real Bedrock Llama 70B pricing)")
print(f"ESTIMATED TOTAL COST:     ${estimated_cost:,.4f}")
print("-------------------------------------------------------")
print()
print("NOTE: this is an estimate based on average tokens per call")
print("from a small sample (3 accounts). Actual cost will vary with")
print("how much enrichment data each account has (more workload")
print("signals = longer prompts = more tokens). Treat this as a")
print("ballpark, not an invoice.")
print()


# =====================================================
# SAVE - full account list with gate decisions, so you can
# review/filter which specific accounts would go to the LLM
# before actually running them.
# =====================================================

accounts.to_excel(OUTPUT_FILE, index=False)
print(f"Full account list with gate decisions saved to: {OUTPUT_FILE}")
print("(filter this file by run_llm == True to see exactly which")
print("accounts would be sent to Bedrock)")
