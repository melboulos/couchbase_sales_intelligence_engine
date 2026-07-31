import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

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
from pipeline.llm_validation_pipeline import validate_accounts
from modules.deterministic_gate import deterministic_gate
from modules.opportunity_explainer import generate_opportunity_explanation
from modules.ownership_signal_detector import detect_ownership_signal
from pipeline.intelligence_export_pipeline import export_account_intelligence


print("Starting Couchbase Sales Intelligence Engine")
print("-------------------------------------------")

import argparse

def _parse_args():
    parser = argparse.ArgumentParser(description="Run the full Couchbase Sales Intelligence pipeline.")
    parser.add_argument("--input", default="input/Enterprise_East_Account_List.xlsx", help="Path to the raw account list to process")
    return parser.parse_args()

_args = _parse_args()
INPUT_FILE = _args.input
_input_stem = os.path.splitext(os.path.basename(INPUT_FILE))[0]
OUTPUT_FILE = f"output/{_input_stem}_Scored.xlsx"


# =====================================================
# LOAD
# =====================================================

accounts = load_accounts(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts")

print("\nColumns found:")
for col in accounts.columns:
    print(f"- {col}")


# =====================================================
# WEB SEARCH GROUNDING MERGE
#
# Merges in cached search snippets from
# serper_enrichment_pass.py's output (if it has been run)
# BEFORE classification/company-intelligence matching runs, so
# an account with no name-based signal at all still gets a real
# shot at a genuine match via industry_classifier.py's and
# company_intelligence.py's web-search fallback passes.
#
# Gracefully degrades to an empty column if the cache does not
# exist yet - running main.py without ever having run
# serper_enrichment_pass.py still works exactly as before, just
# without the fallback benefit.
#
# Same drop_duplicates(keep="first") pattern already used
# elsewhere in this codebase for the Account Name uniqueness
# limitation (duplicate names for genuinely different accounts
# share whichever cached result was fetched first).
# =====================================================

SEARCH_CACHE_FILE = "output/serper_search_cache.xlsx"

print("\nMerging cached web search grounding (if available)...")

if os.path.exists(SEARCH_CACHE_FILE):
    search_cache = pd.read_excel(SEARCH_CACHE_FILE)
    search_cache = search_cache.drop_duplicates(subset="Account Name", keep="first")
    search_cache = search_cache[["Account Name", "search_snippets"]].rename(
        columns={"search_snippets": "web_search_snippets"}
    )
    accounts = accounts.merge(search_cache, on="Account Name", how="left")
    has_snippets = accounts["web_search_snippets"].notna().sum()
    print(f"  Cache found: {SEARCH_CACHE_FILE}")
    print(f"  Accounts with real web search grounding available: {has_snippets} / {len(accounts)}")
else:
    accounts["web_search_snippets"] = ""
    print(f"  No cache found at {SEARCH_CACHE_FILE} - run serper_enrichment_pass.py first")
    print("  to enable the web-search fallback in classification. Continuing without it.")


# =====================================================
# OWNERSHIP SIGNAL DETECTION
#
# Free, deterministic scan of the already-cached search data for
# ownership-change/rebrand signals (Cardtronics/NCR Atleos,
# PrimePay/CoAd, GroupM/WPP Media confirmed as real, found examples
# this session - see modules/ownership_signal_detector.py for the
# full rationale). No new search cost, no new LLM cost - runs on
# data already merged in above.
# =====================================================

print("\nScanning for ownership/rebrand signals (free, no new cost)...")
ownership_results = accounts.apply(detect_ownership_signal, axis=1)
ownership_results = pd.DataFrame(ownership_results.tolist())
accounts = pd.concat(
    [accounts.reset_index(drop=True), ownership_results.reset_index(drop=True)],
    axis=1
)
flagged_count = accounts["ownership_signal_detected"].sum()
print(f"  Accounts with a detected ownership/rebrand signal: {flagged_count} / {len(accounts)}")


# =====================================================
# NORMALIZATION
# =====================================================

print("\nRunning normalization...")
accounts = normalize_accounts(accounts)


# =====================================================
# INDUSTRY CLASSIFICATION
# =====================================================

print("\nRunning industry classification...")
accounts = classify_industries(accounts)


# =====================================================
# COMPANY INTELLIGENCE
# =====================================================

print("\nRunning company intelligence...")
accounts = enrich_company_intelligence(accounts)


# =====================================================
# TECHNOLOGY ENRICHMENT
# =====================================================

print("\nRunning technology enrichment...")
accounts = enrich_technology(accounts)


# =====================================================
# ACCOUNT INTELLIGENCE
# =====================================================

print("\nRunning account intelligence...")
accounts = enrich_account_intelligence(accounts)


# =====================================================
# ACCOUNT ENRICHMENT
# =====================================================

print("\nRunning account enrichment...")
accounts = enrich_accounts(accounts)


# =====================================================
# CLEAN DUPLICATES
# =====================================================

accounts = accounts.loc[:, ~accounts.columns.duplicated()]
print("\nDuplicate columns cleaned")


# =====================================================
# COMPANY ARCHETYPE
# =====================================================

print("\nClassifying company archetypes...")
accounts = enrich_company_archetypes(accounts)


# =====================================================
# SCORE
# =====================================================

print("\nCalculating Couchbase Opportunity Index...")
accounts = score_accounts(accounts)


# =====================================================
# OPPORTUNITY EXPLANATION
# =====================================================

print("\nGenerating opportunity explanations...")

opportunity_results = accounts.apply(
    generate_opportunity_explanation, axis=1
)
opportunity_results = pd.DataFrame(opportunity_results.tolist())

accounts = pd.concat(
    [
        accounts.reset_index(drop=True),
        opportunity_results.reset_index(drop=True)
    ],
    axis=1
)


# =====================================================
# LLM CANDIDATE SELECTION
#
# Uses the deterministic gate directly, across the full
# account set, rather than an arbitrary top-N cap. The
# gate's run_llm decision is based on overall_coi plus
# database technology / modernization / cloud / negative
# signal adjustments (see modules/deterministic_gate.py).
# =====================================================

print("\nRunning deterministic gate...")

gate_results = accounts.apply(deterministic_gate, axis=1)
gate_results = pd.DataFrame(gate_results.tolist())

accounts = pd.concat(
    [
        accounts.reset_index(drop=True),
        gate_results.reset_index(drop=True)
    ],
    axis=1
)

llm_candidates = accounts[accounts["run_llm"] == True]

print(f"Selected {len(llm_candidates)} accounts for LLM validation")


# =====================================================
# LLM VALIDATION
# =====================================================

print("\nRunning LLM validation...")
llm_accounts = validate_accounts(llm_candidates)


# =====================================================
# MERGE LLM INTELLIGENCE BACK
#
# Only merge rows that passed validation. Accounts where
# llm_validation == False (e.g. hallucination detected,
# forbidden evidence language, empty required content,
# inconsistent independent score) should not have their
# content flow into the dashboard or scored output — they
# fall back to no LLM data, the same as a gate-skipped
# account, rather than displaying unvalidated content as
# if it were trustworthy.
#
# llm_workload_score / llm_realtime_score /
# llm_complexity_score / llm_total_score /
# llm_score_reasoning are the LLM's own INDEPENDENT score,
# generated without ever seeing overall_coi, priority_tier,
# or the deterministic database_intensity /
# operational_complexity / realtime_requirement values.
# They exist side-by-side with overall_coi in the output
# purely so the two can be compared to find gaps in
# data/company_patterns.json — they are never merged,
# blended, or used to adjust overall_coi.
#
# Column list matches the current sales_intelligence_pipeline.py /
# llm_prompt_builder.py contract. Old schema fields
# (llm_opportunity_score, coi_assessment, coi_delta_reason,
# opportunity_summary, couchbase_trigger, evidence_found,
# missing_evidence, database_replacement_probability,
# seller_action, discovery_questions, llm_reasoning,
# conversation_strategy, why_this_workload_matters) have
# been retired and removed from this list.
# =====================================================

print("\nMerging LLM intelligence back into full dataset...")

validated_llm_accounts = llm_accounts[llm_accounts["llm_validation"] == True]

print(
    f"Validated: {len(validated_llm_accounts)} / {len(llm_accounts)} "
    f"LLM-processed accounts"
)

# =====================================================
# WEB SEARCH GROUNDING VISIBILITY
#
# Added 2026-07-30 after a real production run silently failed
# search grounding for 1,524/1,524 LLM-processed accounts (a
# transient Serper rate-limit hit during a heavy concurrent burst,
# swallowed by search_company()'s soft-fail design with zero
# visible error) - this went undiscovered until a manual, multi-
# step investigation well after the run finished and money had
# already been spent. This summary makes that kind of silent,
# systemic failure visible immediately, every run, right where the
# rest of the LLM summary already prints - not something you have
# to think to go looking for.
# =====================================================

if len(validated_llm_accounts) > 0:
    used_search_count = (validated_llm_accounts["llm_used_web_search"] == True).sum()
    print(
        f"Web search grounding: {used_search_count} / {len(validated_llm_accounts)} "
        f"validated accounts used a real search result"
    )
    search_rate = used_search_count / len(validated_llm_accounts)
    if search_rate < 0.10:
        print(
            "  WARNING: less than 10% of accounts got web search grounding. "
            "If most of these accounts have a real Account State/Province, "
            "this may indicate a Serper rate-limit or outage during this run, "
            "not a data gap - check modules/web_search_client.py directly "
            "before assuming this is expected."
        )

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
    "llm_score_ungrounded",
    "llm_magnitude_bucket",
    "llm_distributed_solution_defaulted",
    "llm_score_reasoning"
]

llm_merge_columns = [
    c for c in llm_merge_columns
    if c in validated_llm_accounts.columns
]

print("\nLLM merge columns:")
for c in llm_merge_columns:
    print("-", c)

# KNOWN LIMITATION: Account Name is not a unique key in this
# file (confirmed: duplicate names exist for genuinely
# different accounts, e.g. two different "United Community
# Bank" entries). A plain merge(how="left", on="Account Name")
# is a many-to-many join when a name repeats on BOTH sides,
# which silently INFLATES row count (2 accounts named "X" x 2
# LLM-result rows named "X" = 4 output rows instead of 2) -
# this is very likely the cause of a real row-count mismatch
# found in production (9758 accounts loaded -> 9760 in final
# output). Deduping the right side first guarantees the merge
# can only add columns, never rows - at the same known cost as
# elsewhere in this codebase: duplicate-named accounts share
# whichever LLM result was processed/kept first.
validated_llm_accounts_deduped = validated_llm_accounts.drop_duplicates(
    subset="Account Name", keep="first"
)

accounts = accounts.merge(
    validated_llm_accounts_deduped[llm_merge_columns],
    on="Account Name",
    how="left"
)


# =====================================================
# FINAL CLEAN
# =====================================================

accounts = accounts.loc[:, ~accounts.columns.duplicated()]


# =====================================================
# EXPORT EXCEL
# =====================================================

accounts.to_excel(OUTPUT_FILE, index=False)


# =====================================================
# EXPORT LLM TEST OUTPUT
# =====================================================

llm_accounts.to_excel("output/LLM_Validated_Accounts.xlsx", index=False)


# =====================================================
# EXPORT STREAMLIT JSON
# =====================================================

export_account_intelligence(accounts)


print("\n-------------------------------------------")
print("Completed")
print(f"Accounts processed: {len(accounts)}")
print(f"Full output: {OUTPUT_FILE}")
