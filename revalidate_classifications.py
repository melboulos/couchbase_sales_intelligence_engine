# =====================================================
# RE-VALIDATE CLASSIFICATIONS (free - no new LLM calls)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# classification_prepass.py's checkpoint file
# (output/classification_prepass_results.xlsx) already has the
# raw llm_specific_fact/llm_workload_profile/llm_scale_tier
# answers saved from the real Bedrock run. When the validation
# rules in sales_intelligence_pipeline.py improve (new
# stoplist entries, new category-mismatch keywords), those
# improvements would normally only apply to the NEXT run - this
# script re-applies the CURRENT rules to the EXISTING answers
# instead, so guardrail improvements benefit already-collected
# data without spending anything more on Bedrock.
#
# Usage:
#     python3 revalidate_classifications.py
# =====================================================

import pandas as pd

from modules.sales_intelligence_pipeline import validate_classification, apply_scale_adjustment
from modules.classification_prompt_builder import VALID_WORKLOAD_PROFILES
from modules.company_intelligence import WORKLOAD_PROFILES
from modules.scoring_engine import calculate_coi

SCORED_INPUT_FILE = "output/report1784905185024_Scored.xlsx"
CHECKPOINT_FILE = "output/classification_prepass_results.xlsx"
OUTPUT_FILE = "output/report1784905185024_Scored_with_classification.xlsx"

# Copied directly from classification_prepass.py rather than
# imported - importing that file would re-run its entire top-level
# script (including real threaded Bedrock calls), not just get this
# dict, since it isn't guarded by if __name__ == "__main__".
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


def apply_classification(row, classification):
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


print(f"Loading original scored file: {SCORED_INPUT_FILE}")
accounts = pd.read_excel(SCORED_INPUT_FILE)

print(f"Loading existing classification answers: {CHECKPOINT_FILE}")
raw_results = pd.read_excel(CHECKPOINT_FILE)
print(f"Existing answers: {len(raw_results)}")

# Re-run validation with the CURRENT rules against the RAW answers
# already collected. No LLM calls happen here.
before_upgraded = 0
after_upgraded = 0

revalidated = []
for _, row in raw_results.iterrows():
    result = row.to_dict()

    if result.get("llm_workload_profile") not in (None, "none") and \
       str(result.get("llm_workload_profile")) != "nan":
        before_upgraded += 1

    result = validate_classification(dict(result), VALID_WORKLOAD_PROFILES)

    if result.get("llm_workload_profile") != "none":
        after_upgraded += 1

    revalidated.append(result)

print()
print(f"Upgraded under OLD rules (as originally run): {before_upgraded}")
print(f"Upgraded under CURRENT rules (re-validated, free): {after_upgraded}")
print(f"Removed by improved guardrails: {before_upgraded - after_upgraded}")

revalidated_df = pd.DataFrame(revalidated)
revalidated_df.to_excel(CHECKPOINT_FILE, index=False)
print(f"Updated checkpoint saved: {CHECKPOINT_FILE}")

classification_by_name = {
    r["Account Name"]: r for r in revalidated
}

# Columns that will receive mixed types - force object dtype first,
# same fix as classification_prepass.py, since Excel round-tripping
# can silently turn all-blank columns into float64.
TARGET_COLS = [
    "workload_profile", "database_intensity", "operational_complexity",
    "realtime_requirement", "industry", "company_signal_reason",
    "overall_coi", "priority_tier", "raw_coi_score", "signals_found",
    "missing_signals", "industry_context", "llm_scale_tier",
]
for col in TARGET_COLS:
    if col in accounts.columns:
        accounts[col] = accounts[col].astype(object)

updated_count = 0
for idx, row in accounts.iterrows():
    name = row.get("Account Name", "")
    classification = classification_by_name.get(name)

    if classification and classification.get("llm_workload_profile") != "none":
        row_dict = row.to_dict()
        row_dict = apply_classification(row_dict, classification)
        for col, val in row_dict.items():
            if col not in accounts.columns:
                accounts[col] = None
            accounts.at[idx, col] = val
        updated_count += 1

print(f"Accounts upgraded from Unknown via re-validated classification: {updated_count}")

accounts.to_excel(OUTPUT_FILE, index=False)
print(f"Saved: {OUTPUT_FILE}")
print()
print("No new LLM calls were made - this only re-applied the current")
print("validation rules to already-collected answers.")
