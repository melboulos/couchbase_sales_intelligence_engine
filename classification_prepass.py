# =====================================================
# CLASSIFICATION PRE-PASS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# ~79% of the real 9,758-account file (7,732 accounts) has
# industry == "Unknown" - the deterministic pattern matching
# has genuinely no signal for these at all, since this lean
# export has no raw Industry/revenue/employee-count field to
# fall back on, only the account name.
#
# This script asks the LLM a NARROW classification-only
# question for each Unknown account: do you recognize this
# specific company, and if so, which existing workload_profile
# category best fits it? It does NOT ask for a score - a
# verified classification here gets folded into the row's
# database_intensity/operational_complexity/realtime_requirement
# via the exact same workload_profiles.json join that
# company_intelligence.py already uses, then COI is recomputed
# with the SAME calculate_coi() function everything else runs
# through. No new, separate scoring logic.
#
# Same fact-verification discipline as the independent score:
# a classification is only trusted if llm_recognition_verified
# is True (validate_classification() in
# sales_intelligence_pipeline.py) - the model saying "yes I
# recognize this" is not good enough on its own, per the
# BayMark Health Services lesson from the production run.
#
# Usage:
#     python3 classification_prepass.py
# =====================================================

import concurrent.futures
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from modules.llm_client import call_llm
from modules.classification_prompt_builder import (
    build_classification_prompt,
    VALID_WORKLOAD_PROFILES,
)
from modules.sales_intelligence_pipeline import validate_classification, apply_scale_adjustment
from modules.company_intelligence import WORKLOAD_PROFILES
from modules.scoring_engine import calculate_coi


# =====================================================
# CONFIG
# =====================================================

import argparse
import os

def _parse_args():
    parser = argparse.ArgumentParser(description="LLM classification pre-pass for Unknown-industry accounts.")
    parser.add_argument("--input", default="output/report1784905185024_Scored.xlsx", help="Path to a scored file (main.py's output)")
    return parser.parse_args()

_args = _parse_args()
INPUT_FILE = _args.input
_input_stem = os.path.splitext(os.path.basename(INPUT_FILE))[0]
OUTPUT_FILE = f"output/{_input_stem}_with_classification.xlsx"
CHECKPOINT_FILE = f"output/{_input_stem}_classification_prepass_results.xlsx"

MAX_WORKERS = 5
CHECKPOINT_EVERY = 100

# Real Bedrock pricing, same as pipeline/llm_validation_pipeline.py
COST_PER_1K_TOKENS = 0.00072

# Friendly display label per workload_profile category, matching
# the industry labels already used elsewhere in this pipeline's
# output for consistency.
PROFILE_TO_INDUSTRY_LABEL = {
    "insurance_platform": "Insurance",
    "pharma_device_platform": "Pharma & Medical Device",
    "utilities_platform": "Energy and Utilities",
    "media_platform": "Media & Advertising",
    "customer_application": "Technology / SaaS",
    "logistics_platform": "Logistics & Transportation",
    "retail_platform": "Retail",
    "saas_platform": "Technology / SaaS",
    "telecom_platform": "Telecommunications",
    "media_entertainment_platform": "Media & Entertainment",
    "api_platform": "Technology / SaaS",
    "mobile_application": "Technology / SaaS",
    "payment_platform": "Financial Services",
}


def classify_one_account(account_name):
    prompt = build_classification_prompt(account_name)
    result = call_llm(prompt)
    result = validate_classification(result, VALID_WORKLOAD_PROFILES)
    result["Account Name"] = account_name
    return result


def apply_classification(row, classification):
    """
    Mirrors company_intelligence.py's apply_workload_profile()
    join, but sourced from a verified LLM classification instead
    of a business_patterns.json keyword match. Only called for
    rows where llm_recognition_verified is True and
    llm_workload_profile is a real, valid key.
    """
    profile_key = classification["llm_workload_profile"]
    profile = WORKLOAD_PROFILES.get(profile_key, {})
    scale_tier = classification.get("llm_scale_tier", "typical")

    row["workload_profile"] = profile_key
    row["database_intensity"] = apply_scale_adjustment(
        profile.get("database_intensity", 0), scale_tier
    )
    row["operational_complexity"] = apply_scale_adjustment(
        profile.get("operational_complexity", 0), scale_tier
    )
    row["realtime_requirement"] = apply_scale_adjustment(
        profile.get("realtime_requirement", 0), scale_tier
    )
    row["llm_scale_tier"] = scale_tier
    row["industry"] = PROFILE_TO_INDUSTRY_LABEL.get(profile_key, row.get("industry", "Unknown"))
    row["company_signal_reason"] = (
        f"LLM classification pre-pass (verified, scale={scale_tier}): "
        f"{classification.get('llm_specific_fact', '')}"
    )

    coi_result = calculate_coi(row)
    row.update(coi_result)

    return row


print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts")

candidates = accounts[accounts["industry"] == "Unknown"].copy()
print(f"Unknown-industry candidates for classification: {len(candidates)}")

# Skip accounts whose own name flags them as housekeeping/deletion
# candidates, not real prospects. Found in production: "TELEFONICA
# BRASIL S/A - DUPLICATED - TO BE DELETED" made it all the way
# through scoring into Tier 3 before this filter existed.
HOUSEKEEPING_MARKERS = [
    "duplicated", "to be deleted", "do not use", "obsolete",
    "duplicate", "test account", "- delete", "- inactive",
]

def is_housekeeping_name(name):
    name_lower = str(name).lower()
    return any(marker in name_lower for marker in HOUSEKEEPING_MARKERS)

before_filter = len(candidates)
housekeeping_mask = candidates["Account Name"].apply(is_housekeeping_name)
skipped_housekeeping = candidates[housekeeping_mask]
candidates = candidates[~housekeeping_mask]

if len(skipped_housekeeping) > 0:
    print(f"Skipped {len(skipped_housekeeping)} accounts flagged as "
          f"housekeeping/deletion candidates by their own name (not "
          f"sent to the LLM):")
    for name in skipped_housekeeping["Account Name"].head(10):
        print(f"  - {name}")

print(f"Remaining candidates for classification: {len(candidates)}")

if len(candidates) == 0:
    print("Nothing to classify. Exiting.")
    raise SystemExit()

names = candidates["Account Name"].tolist()

results = []
completed = 0
total = len(names)
start_time = time.time()

print(f"Running threaded classification (max {MAX_WORKERS} concurrent, "
      f"checkpoint every {CHECKPOINT_EVERY})...")

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(classify_one_account, name): name for name in names}

    for future in concurrent.futures.as_completed(futures):
        name = futures[future]
        try:
            result = future.result()
        except Exception as e:
            result = {
                "Account Name": name,
                "llm_recognition_verified": False,
                "llm_workload_profile": "none",
                "llm_error": f"Worker exception: {e}",
            }

        results.append(result)
        completed += 1

        if completed % CHECKPOINT_EVERY == 0 or completed == total:
            pd.DataFrame(results).to_excel(CHECKPOINT_FILE, index=False)
            elapsed = time.time() - start_time
            print(f"[{completed}/{total}] checkpoint saved, {elapsed:.0f}s elapsed")

print(f"Classification calls complete: {completed}/{total}")

results_df = pd.DataFrame(results)
verified_count = results_df["llm_recognition_verified"].sum() if len(results_df) else 0
print(f"Verified classifications (real, checkable fact): {verified_count} / {total}")
print(f"Unverified/none: {total - verified_count} / {total}")

# =====================================================
# COST SUMMARY
# =====================================================

total_input_tokens = results_df.get("llm_input_tokens", pd.Series(dtype=int)).fillna(0).sum()
total_output_tokens = results_df.get("llm_output_tokens", pd.Series(dtype=int)).fillna(0).sum()
total_tokens = total_input_tokens + total_output_tokens
total_cost = (total_tokens / 1000) * COST_PER_1K_TOKENS

print()
print("=========================================================")
print("CLASSIFICATION PRE-PASS COST SUMMARY")
print("=========================================================")
print(f"Total tokens: {int(total_tokens):,}")
print(f"Total cost:   ${total_cost:.4f}")
print()

# =====================================================
# APPLY VERIFIED CLASSIFICATIONS BACK TO THE FULL DATASET
# =====================================================

classification_by_name = {r["Account Name"]: r for r in results}

updated_count = 0

# Columns we're about to write strings/mixed types into. If any of
# these round-tripped through Excel as all-blank, pandas infers
# float64 dtype, and writing a string into a float64 column raises
# LossySetitemError. Force object dtype first so assignment always
# works regardless of what the column happened to look like on load.
TARGET_COLS = [
    "workload_profile", "database_intensity", "operational_complexity",
    "realtime_requirement", "industry", "company_signal_reason",
    "overall_coi", "priority_tier", "raw_coi_score", "signals_found",
    "missing_signals", "industry_context",
]
for col in TARGET_COLS:
    if col in accounts.columns:
        accounts[col] = accounts[col].astype(object)

for idx, row in accounts.iterrows():
    name = row.get("Account Name", "")
    classification = classification_by_name.get(name)

    if classification and classification.get("llm_recognition_verified") and \
       classification.get("llm_workload_profile") != "none":
        row_dict = row.to_dict()
        row_dict = apply_classification(row_dict, classification)
        for col, val in row_dict.items():
            if col not in accounts.columns:
                accounts[col] = None
            accounts.at[idx, col] = val
        updated_count += 1

print(f"Accounts upgraded from Unknown via verified classification: {updated_count}")

accounts.to_excel(OUTPUT_FILE, index=False)
print(f"Saved: {OUTPUT_FILE}")
print()
print("NOTE: this is a NEW file, separate from the original scored")
print("output - review it before treating it as the new canonical")
print("scored file. If it looks right, you can rerun")
print("build_ae_call_list.py against it (update INPUT_FILE first).")
