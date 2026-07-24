# =====================================================
# LLM PROMPT TEST
# Couchbase Sales Intelligence Engine
#
# Debug Purpose:
#
# Track:
# - deterministic gate decision
# - qualification LLM execution
# - intelligence LLM execution
# - token usage
# - RAW LLM JSON returned
#
# NOTE:
# This test re-runs company_intelligence.analyze_company()
# and scoring_engine.calculate_coi() live for each test
# account, rather than trusting the values already sitting
# in Enterprise_East_Scored.xlsx. That file is a static
# snapshot from a prior pipeline run and will not reflect
# any fixes made to enrichment or scoring logic since it
# was generated. Account identity fields (Account Name,
# industry raw source data, etc.) still come from the
# snapshot; workload/COI/tier fields are recomputed fresh.
#
# THREADING NOTE:
# Each account's LLM call is an independent network round
# trip to Bedrock, so accounts are run concurrently via
# ThreadPoolExecutor rather than one at a time. Printing
# from multiple threads means the per-account debug blocks
# below can interleave in the console - each block is still
# fully self-contained and labeled with the account name, so
# it's readable, just not strictly in submission order. If
# you hit Bedrock throttling errors, lower MAX_WORKERS.
# =====================================================


import pandas as pd
import json
import concurrent.futures


from modules.sales_intelligence_pipeline import validate_account
from modules.company_intelligence import analyze_company
from modules.scoring_engine import calculate_coi


# =====================================================
# TEMPORARY TEST OVERRIDE
#
# Forces specific low-COI/excluded accounts through the LLM
# anyway, to test whether llm_total_score genuinely
# discriminates by account fit, or converges to the same
# value regardless of input (suspected after Paytronix=75,
# Cleo=75, OpenKey=75 all landed identically).
#
# This only patches the gate function inside THIS script's
# process - modules/deterministic_gate.py on disk is never
# modified. Remove this block once the test is done.
# =====================================================

import modules.deterministic_gate as gate_module

_original_gate = gate_module.deterministic_gate

FORCE_LLM_OVERRIDE = [
    "Trumid Financial",
    "United Community Bank",
    "Members 1st Federal Credit Union"
]

def _forced_gate(row):
    result = _original_gate(row)
    if row.get("Account Name") in FORCE_LLM_OVERRIDE:
        result["run_llm"] = True
        result["gate_reason"] = result.get("gate_reason", "") + " [TEST OVERRIDE: forced through]"
    return result

gate_module.deterministic_gate = _forced_gate


# =====================================================
# CONFIG
# =====================================================

INPUT_FILE = "output/Enterprise_East_Scored.xlsx"
OUTPUT_FILE = "output/llm_prompt_test.xlsx"

# Keep modest - Bedrock may throttle if too many concurrent
# requests hit it at once. 3-5 is a safe starting point.
MAX_WORKERS = 5


# =====================================================
# TEST ACCOUNTS
# =====================================================

TEST_ACCOUNTS = [
    "Netspend",
#    "Paytronix Systems",
#    "Cleo",
#    "Redox",
#    "Staywell",
#    "PeopleAdmin",
#    "OpenKey",
#    "Members 1st Federal Credit Union",
    "United Community Bank",
    "Trumid Financial"
]


# =====================================================
# LOAD
# =====================================================

print("Loading accounts...")

accounts = pd.read_excel(INPUT_FILE)

test_accounts = accounts[accounts["Account Name"].isin(TEST_ACCOUNTS)]

# Two different real Salesforce accounts can share the same
# Account Name (e.g. two "United Community Bank" entries with
# different CB Account Numbers/states) - keep one per name for
# a clean test run.
test_accounts = test_accounts.drop_duplicates(subset="Account Name", keep="first")

print(f"Testing {len(test_accounts)} accounts")


# =====================================================
# PER-ACCOUNT WORKER
#
# Everything that used to be the body of the sequential
# for-loop now lives in this function, so it can be handed
# to a thread pool. Returns the same result dict shape that
# used to get appended to `results` directly.
# =====================================================

def process_account(row):
    row = row.to_dict()
    account_name = row["Account Name"]

    # =================================================
    # RE-RUN ENRICHMENT + SCORING LIVE
    # =================================================

    enrichment = analyze_company(row)
    row.update(enrichment)

    coi_result = calculate_coi(row)
    row.update(coi_result)

    print()
    print("==========================")
    print("ACCOUNT:", account_name)
    print("COI:", row.get("overall_coi", ""))
    print("TIER:", row.get("priority_tier", ""))
    print("WORKLOAD PROFILE:", row.get("workload_profile", ""))
    print("WORKLOAD STRENGTH:", row.get("workload_strength", ""))
    print("DATABASE INTENSITY:", row.get("database_intensity", ""))
    print("OPERATIONAL COMPLEXITY:", row.get("operational_complexity", ""))
    print("REALTIME REQUIREMENT:", row.get("realtime_requirement", ""))
    print(f"[{account_name}] Calling validate_account...")

    result = validate_account(row)

    # =================================================
    # RAW RESULT
    # =================================================

    print()
    print(f"---------- RAW RETURNED JSON ({account_name}) ----------")
    print(json.dumps(result, indent=4, default=str))
    print("---------------------------------------")

    # =================================================
    # DEBUG
    # =================================================

    print()
    print(f"---------- DEBUG ({account_name}) ----------")

    debug_fields = [
        "gate_decision",
        "gate_reason",
        "gate_score",
        "qualification_result",
        "qualification_score",
        "qualification_reason",
        "llm_validation",
        "llm_error",
    ]

    for field in debug_fields:
        print(f"{field}:", result.get(field, "NOT_RETURNED"))

    print()
    print(f"[{account_name}] QUALIFICATION TOKENS")
    print("Input:", result.get("qualification_input_tokens", 0))
    print("Output:", result.get("qualification_output_tokens", 0))
    print("Total:", result.get("qualification_total_tokens", 0))

    print()
    print(f"[{account_name}] INTELLIGENCE TOKENS")
    print("Input:", result.get("intelligence_input_tokens", 0))
    print("Output:", result.get("intelligence_output_tokens", 0))
    print("Total:", result.get("intelligence_total_tokens", 0))

    print()
    print(f"[{account_name}] TOTAL TOKENS:", result.get("llm_total_tokens", 0))
    print("--------------------------")

    return {
        "Account Name": account_name,
        "overall_coi": row.get("overall_coi", ""),
        "priority_tier": row.get("priority_tier", ""),
        "workload_profile": row.get("workload_profile", ""),
        "workload_strength": row.get("workload_strength", ""),
        "database_intensity": row.get("database_intensity", ""),
        "operational_complexity": row.get("operational_complexity", ""),
        "realtime_requirement": row.get("realtime_requirement", ""),
        **result
    }


# =====================================================
# RUN (THREADED)
# =====================================================

results = []

rows = [row for _, row in test_accounts.iterrows()]

with concurrent.futures.ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(rows))) as executor:
    futures = [executor.submit(process_account, row) for row in rows]

    for future in concurrent.futures.as_completed(futures):
        try:
            results.append(future.result())
        except Exception as e:
            print(f"WORKER FAILED: {e}")


# =====================================================
# SAVE
# =====================================================

df_results = pd.DataFrame(results)

TOKEN_COLUMNS = [
    "qualification_input_tokens",
    "qualification_output_tokens",
    "qualification_total_tokens",
    "intelligence_input_tokens",
    "intelligence_output_tokens",
    "intelligence_total_tokens",
    "llm_total_tokens"
]

for col in TOKEN_COLUMNS:
    if col not in df_results.columns:
        df_results[col] = 0

df_results.to_excel(OUTPUT_FILE, index=False)


# =====================================================
# TOKEN SUMMARY
# =====================================================

print()
print("==========================")
print("TOKEN USAGE SUMMARY")
print("==========================")

for col in TOKEN_COLUMNS:
    total = df_results[col].fillna(0).sum()
    print(col, ":", int(total))

print()
print("Accounts tested:", len(df_results))
print("Completed")
print("Saved:")
print(OUTPUT_FILE)
print("==========================")
