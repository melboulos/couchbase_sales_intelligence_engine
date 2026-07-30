# =====================================================
# TEST WEB SEARCH
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Standalone test of the Serper.dev search client, BEFORE wiring
# it into the real pipeline. Checks a deliberate mix: a
# well-known company, a real-but-obscure one, and one the LLM
# previously could not recognize at all (from real production
# output earlier this session) - to see whether search actually
# helps in exactly the cases where the LLM's own memory failed.
#
# Requires SERPER_API_KEY to be set as an environment variable.
#
# Usage:
#     python3 test_web_search.py
# =====================================================

import os
from dotenv import load_dotenv

load_dotenv()
from modules.web_search_client import search_company, format_web_context

if not os.environ.get("SERPER_API_KEY"):
    print("SERPER_API_KEY is not set. Set it first:")
    print('  export SERPER_API_KEY="your-key-here"')
    raise SystemExit(1)

TEST_ACCOUNTS = [
    "Netspend",                # well-known, LLM already recognized this correctly
    "United Community Bank",   # real, recognized but only thinly (100 branches)
    "Sqrrl Data LLC",          # LLM said "NONE - not specifically recognized" in real output
    "ELOQUII",                 # LLM said "NONE - not specifically recognized" in real output
    "Zup IT Innovation",       # LLM said "NONE - not specifically recognized" in real output
]

for account_name in TEST_ACCOUNTS:
    print()
    print("=" * 60)
    print(f"ACCOUNT: {account_name}")
    print("=" * 60)

    snippets = search_company(account_name)

    if snippets is None:
        print("No results returned (search failed or found nothing).")
        continue

    print(f"Found {len(snippets)} snippet(s):")
    for s in snippets:
        print(f"  - {s}")

    print()
    print("Formatted for prompt insertion:")
    print(format_web_context(snippets))

print()
print("=" * 60)
print("Review the snippets above manually:")
print("- Are they actually accurate and relevant to the real company?")
print("- Do they give the LLM something concrete to work with for")
print("  Sqrrl/ELOQUII/Zup - the ones it couldn't recognize before?")
print("- Any obviously wrong-company results (name collisions)?")
print("=" * 60)
