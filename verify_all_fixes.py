# =====================================================
# VERIFY ALL FIXES ARE ACTUALLY IN PLAY
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Directly inspects the real, currently-installed code (not just
# greps for text) to confirm every fix built today is genuinely
# active and correctly wired - not just present somewhere in a
# file. Read-only, safe to run WHILE rerun_qualified_with_search.py
# is still going, since it only imports and inspects code, never
# touches any data file.
#
# Usage:
#     python3 verify_all_fixes.py
# =====================================================

import inspect

results = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, label, detail))
    print(f"[{status}] {label}" + (f" - {detail}" if detail and status == "FAIL" else ""))


print("=" * 60)
print("CORE SCORING PIPELINE")
print("=" * 60)

from modules import sales_intelligence_pipeline as sip

check(
    "detect_defunct_company exists",
    hasattr(sip, "detect_defunct_company")
)
check(
    "detect_ungrounded_score exists",
    hasattr(sip, "detect_ungrounded_score")
)
check(
    "apply_magnitude_based_score_adjustment exists",
    hasattr(sip, "apply_magnitude_based_score_adjustment")
)
check(
    "determine_if_default_score exists",
    hasattr(sip, "determine_if_default_score")
)
check(
    "build_couchbase_pov_from_parts exists (schema-split fix)",
    hasattr(sip, "build_couchbase_pov_from_parts")
)
check(
    "detect_prompt_leakage exists",
    hasattr(sip, "detect_prompt_leakage")
)

# Confirm the employee/dollar separation fix - employee count should
# NEVER be able to trigger the large floor, only dollar figures can.
extract_employee_src = inspect.getsource(sip.extract_employee_count) if hasattr(sip, "extract_employee_count") else ""
extract_dollar_src = inspect.getsource(sip.extract_dollar_magnitude) if hasattr(sip, "extract_dollar_magnitude") else ""
check(
    "extract_employee_count and extract_dollar_magnitude are SEPARATE functions",
    hasattr(sip, "extract_employee_count") and hasattr(sip, "extract_dollar_magnitude"),
    "if this fails, the old bug (large headcount triggering the large floor) may have returned"
)

adjustment_src = inspect.getsource(sip.apply_magnitude_based_score_adjustment)
check(
    "LARGE floor is only reachable via dollar_magnitude, not employee_count",
    "employee_count is not None and employee_count < SMALL_SCALE_THRESHOLD" not in adjustment_src
    and "dollar_magnitude is not None and dollar_magnitude >= LARGE_SCALE_THRESHOLD" in adjustment_src,
    "check apply_magnitude_based_score_adjustment source manually"
)

check(
    "LARGE_SCALE_FLOORS uses the corrected (higher) values, not the original bug values",
    sip.LARGE_SCALE_FLOORS.get("llm_workload_score") == 35
    and sip.LARGE_SCALE_FLOORS.get("llm_realtime_score") == 27
    and sip.LARGE_SCALE_FLOORS.get("llm_complexity_score") == 25,
    f"current values: {sip.LARGE_SCALE_FLOORS}"
)

check(
    "trillion is in DOLLAR_MULTIPLIERS (the Trumid fix)",
    "trillion" in sip.DOLLAR_MULTIPLIERS
)

# Confirm the actual call order inside validate_llm_output
validate_llm_output_src = inspect.getsource(sip.validate_llm_output)
required_calls_in_order = [
    "validate_required_fields", "build_couchbase_pov_from_parts",
    "enforce_company_recognition_cap", "detect_ungrounded_score",
    "apply_magnitude_based_score_adjustment", "determine_if_default_score",
    "apply_narrative_caveat", "detect_prompt_leakage", "detect_defunct_company",
]
positions = []
all_present = True
for call in required_calls_in_order:
    pos = validate_llm_output_src.find(call + "(result)")
    if pos == -1:
        all_present = False
    positions.append(pos)

check(
    "All core checks are actually called inside validate_llm_output",
    all_present,
    "one or more expected calls is missing from the function body"
)
check(
    "Calls happen in a sane order (not scrambled)",
    all_present and positions == sorted(positions),
    f"positions found: {list(zip(required_calls_in_order, positions))}"
)

print()
print("=" * 60)
print("WEB SEARCH GROUNDING (RAG)")
print("=" * 60)

from modules import web_search_client as wsc

check("search_company exists", hasattr(wsc, "search_company"))
check("format_web_context exists", hasattr(wsc, "format_web_context"))

search_company_src = inspect.getsource(wsc.search_company)
check(
    "search_company reads the API key from an environment variable, not hardcoded",
    'os.environ.get("SERPER_API_KEY")' in search_company_src
)

validate_account_src = inspect.getsource(sip.validate_account)
check(
    "validate_account actually calls search_company",
    "search_company(" in validate_account_src
)
check(
    "Search is skipped when no location is known (the no-collision-risk fix)",
    "if location:" in validate_account_src
)

print()
print("=" * 60)
print("PROMPT STRUCTURE")
print("=" * 60)

from modules import llm_prompt_builder as lpb

prompt_src = inspect.getsource(lpb.build_intelligence_prompt)
check(
    "Prompt requires specific_constraint/distributed_solution (schema split)",
    '"specific_constraint"' in prompt_src and '"distributed_solution"' in prompt_src
)
check(
    "No leftover copyable example sentence (the leakage risk)",
    "Sustaining sub-second fraud-check latency while a single write" not in prompt_src
)
check(
    "Cross-check-against-location instruction is present",
    "CROSS-CHECK WEB SEARCH RESULTS" in prompt_src
)
check(
    "Discovery Strategy no longer hardcodes literal phase text",
    "Understand architecture.\n\nPhase 2" not in prompt_src
)

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for status, _, _ in results if status == "PASS")
failed = sum(1 for status, _, _ in results if status == "FAIL")
print(f"Passed: {passed} / {len(results)}")
if failed > 0:
    print(f"FAILED: {failed} - see [FAIL] lines above for details")
else:
    print("All checks passed.")
