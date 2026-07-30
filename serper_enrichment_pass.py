# =====================================================
# SERPER ENRICHMENT PASS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Runs a real web search (via Serper.dev) for EVERY account in
# the input file, not just the ones that already happen to match
# a name-based pattern in data/company_patterns.json. Right now,
# an account with an unrecognizable name gets ZERO deterministic
# signal at all - workload_profile stays empty, database_intensity
# stays 0, COI lands near zero - and it's buried in Tier 4 by
# default. That's not the same thing as actually being a weak
# prospect; it's the pipeline having no information, not evidence
# of a bad fit. This gives every account a fair shot at real
# signal before the deterministic gate makes its LLM-eligibility
# decision.
#
# Cost discipline: results are cached per account in CACHE_FILE
# and checked BEFORE any Serper call - re-running this script
# against the same account list costs nothing for accounts
# already in the cache. Same per-row checkpoint discipline as
# pipeline/llm_validation_pipeline.py and classification_prepass.py:
# a crash partway through does not lose already-paid-for results.
#
# Raw snippets are cached, not derived signals - if the keyword-
# matching logic that reads this cache later gets refined
# (broadened pattern, fixed false positive), that improvement
# applies retroactively to every already-cached account for free,
# rather than requiring a re-search to benefit from it.
#
# KNOWN LIMITATION: cached by Account Name, not a unique ID - the
# same limitation already accepted elsewhere in this codebase
# (duplicate names for genuinely different accounts, e.g. two
# different "United Community Bank" entries, share whichever
# result was fetched first). See main.py's llm_merge_columns
# comment for the same tradeoff made the same way.
#
# IMPORTANT: this script produces the search cache ONLY. It does
# NOT yet feed the retrieved snippets into industry/workload
# classification - company_intelligence.py and
# industry_classifier.py currently only ever scan Account Name,
# never any other text. Wiring this cache into that matching
# logic is a separate, deliberate next step, not yet built.
#
# Usage:
#     python3 serper_enrichment_pass.py
# =====================================================

import concurrent.futures
import time
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from pipeline.loader import load_accounts
from modules.web_search_client import search_company

INPUT_FILE = "input/Enterprise_East_Account_List.xlsx"
CACHE_FILE = "output/serper_search_cache.xlsx"

MAX_WORKERS = 5
CHECKPOINT_EVERY = 100


def get_location(row):
    """
    Mirrors the location parameter already used in
    sales_intelligence_pipeline.py's search_company call - same
    disambiguation benefit, confirmed necessary for common names
    like "United Community Bank" returning an unrelated real bank.
    """
    value = row.get("Account State/Province", None)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(value).strip() or None


def search_one_account(name, location):
    try:
        snippets = search_company(name, location=location)
    except Exception as e:
        return {
            "Account Name": name,
            "search_snippets": None,
            "search_error": str(e),
            "search_succeeded": False,
        }
    return {
        "Account Name": name,
        "search_snippets": " | ".join(snippets) if snippets else None,
        "search_error": None,
        "search_succeeded": snippets is not None,
    }


print(f"Loading: {INPUT_FILE}")
accounts = load_accounts(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts")

if os.path.exists(CACHE_FILE):
    print(f"Existing cache found: {CACHE_FILE}")
    cache = pd.read_excel(CACHE_FILE)
    already_cached = set(cache["Account Name"].dropna())
else:
    print("No existing cache found - starting fresh")
    cache = pd.DataFrame(
        columns=["Account Name", "search_snippets", "search_error", "search_succeeded"]
    )
    already_cached = set()

to_search = accounts[~accounts["Account Name"].isin(already_cached)]
print(f"Already cached (zero cost): {len(already_cached)}")
print(f"To search now: {len(to_search)}")

if len(to_search) == 0:
    print("Nothing new to search - cache is already complete for this account list.")
    raise SystemExit()

names_and_locations = [
    (row.get("Account Name", ""), get_location(row))
    for _, row in to_search.iterrows()
]

results = []
completed = 0
total = len(names_and_locations)
start_time = time.time()

print(
    f"Running threaded Serper search (max {MAX_WORKERS} concurrent, "
    f"checkpoint every {CHECKPOINT_EVERY})..."
)

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(search_one_account, name, location): name
        for name, location in names_and_locations
    }

    for future in concurrent.futures.as_completed(futures):
        name = futures[future]
        try:
            result = future.result()
        except Exception as e:
            result = {
                "Account Name": name,
                "search_snippets": None,
                "search_error": f"Worker exception: {e}",
                "search_succeeded": False,
            }

        results.append(result)
        completed += 1

        if completed % CHECKPOINT_EVERY == 0 or completed == total:
            new_df = pd.DataFrame(results)
            combined = pd.concat([cache, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset="Account Name", keep="first")
            combined.to_excel(CACHE_FILE, index=False)
            elapsed = time.time() - start_time
            print(f"  [{completed}/{total}] checkpoint saved, {elapsed:.0f}s elapsed")

print(f"\nSearch pass complete: {completed}/{total} attempted")

succeeded = sum(1 for r in results if r.get("search_succeeded"))
print(f"Succeeded (got real results): {succeeded} / {completed}")
print(f"Failed / no results found: {completed - succeeded} / {completed}")
print(f"\nSaved: {CACHE_FILE}")

print()
print("=========================================================")
print("NEXT STEP - NOT YET DONE")
print("=========================================================")
print("This cache does NOT yet feed into industry/workload")
print("classification anywhere. company_intelligence.py and")
print("industry_classifier.py still only ever scan Account Name.")
print(f"Wiring {CACHE_FILE}'s search_snippets into that matching")
print("logic is a separate, deliberate next step.")
