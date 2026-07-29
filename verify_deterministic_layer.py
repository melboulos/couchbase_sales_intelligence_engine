# =====================================================
# VERIFY DETERMINISTIC LAYER (main.py's actual dependencies)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# verify_all_fixes.py only ever checked the LLM/scoring-pipeline
# files (sales_intelligence_pipeline.py, llm_prompt_builder.py,
# web_search_client.py). It never checked company_intelligence.py,
# scoring_engine.py, or the pattern file itself - exactly where the
# real problem lived (the insurance/pharma rating fix and the three
# keyword-collision fixes, all in the deterministic layer main.py
# actually runs). This checks THAT layer specifically.
#
# Read-only, safe to run any time.
#
# Usage:
#     python3 verify_deterministic_layer.py
# =====================================================

results = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, label, detail))
    print(f"[{status}] {label}" + (f" - {detail}" if detail and status == "FAIL" else ""))


print("=" * 60)
print("PATTERN FILE - the actual source data")
print("=" * 60)

import json
with open("data/company_patterns.json") as f:
    patterns = json.load(f)

workload_profiles = patterns.get("workload_profiles", {})
insurance = workload_profiles.get("insurance_platform", {})
pharma = workload_profiles.get("pharma_device_platform", {})

check(
    "insurance_platform has the fixed rating (3, 3), not the old (2, 2)",
    insurance.get("database_intensity") == 3 and insurance.get("operational_complexity") == 3,
    f"actual values: database_intensity={insurance.get('database_intensity')}, operational_complexity={insurance.get('operational_complexity')}"
)
check(
    "pharma_device_platform has the fixed rating (3, 3), not the old (2, 2)",
    pharma.get("database_intensity") == 3 and pharma.get("operational_complexity") == 3,
    f"actual values: database_intensity={pharma.get('database_intensity')}, operational_complexity={pharma.get('operational_complexity')}"
)

print()
print("=" * 60)
print("KEYWORD-COLLISION EXCLUSIONS (company_intelligence.py)")
print("=" * 60)

from modules.company_intelligence import KEYWORD_FALSE_POSITIVE_EXCLUSIONS, is_false_positive_match

check(
    "api/capital exclusion present",
    "capital" in KEYWORD_FALSE_POSITIVE_EXCLUSIONS.get("api", [])
)
check(
    "power/empower exclusion present",
    "empower" in KEYWORD_FALSE_POSITIVE_EXCLUSIONS.get("power", [])
)
check(
    "card/cardiology exclusion present",
    "cardiology" in KEYWORD_FALSE_POSITIVE_EXCLUSIONS.get("card", [])
)
check(
    "Real behavior check: 'KPS Capital Partners, LP' actually triggers the api exclusion",
    is_false_positive_match("api", "kps capital partners, lp")
)
check(
    "Real behavior check: 'Empower Retirement' actually triggers the power exclusion",
    is_false_positive_match("power", "empower retirement")
)
check(
    "Regression check: 'TrialCard' (a real payments company) is NOT excluded",
    not is_false_positive_match("card", "trialcard")
)

print()
print("=" * 60)
print("SCORING ENGINE - reads the fixed values correctly")
print("=" * 60)

from modules.scoring_engine import calculate_coi

test_row = {
    "Account Name": "Test Insurance Co",
    "industry": "Insurance",
    "workload_profile": "insurance_platform",
    "database_intensity": 3,
    "operational_complexity": 3,
    "realtime_requirement": 2,
    "company_size": "Unknown",
}
breakdown = calculate_coi(test_row)
check(
    "database_opportunity_points reflects the fixed (3,3) rating, not the old (2,2)",
    breakdown.get("database_opportunity_points", 0) >= 18,
    f"actual value: {breakdown.get('database_opportunity_points')} (expect >= 18 for 3*3+3*3)"
)

print()
print("=" * 60)
print("PIPELINE WIRING - main.py's actual dependency chain")
print("=" * 60)

import inspect
from pipeline import enrichment_pipeline
enrichment_src = inspect.getsource(enrichment_pipeline)
check(
    "enrichment_pipeline.py actually calls analyze_company",
    "analyze_company" in enrichment_src
)

main_src = open("main.py").read()
check(
    "main.py actually calls score_accounts (the deterministic COI step)",
    "score_accounts(" in main_src
)
check(
    "main.py actually imports from enrichment_pipeline (the classification step)",
    "from pipeline.enrichment_pipeline import" in main_src
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
