# =====================================================
# CLASSIFICATION ACCURACY SPOT CHECK
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# The classification pre-pass upgraded 3,761 accounts from
# Unknown to a real category, and 2,963 of those cleared into
# Tier 2/3. The fact-verification check only catches GENERIC
# phrasing ("as a fintech company, typically...") - it cannot
# catch a confident, specific-sounding, but FABRICATED fact
# (the BayMark Health Services lesson from the earlier
# production run: "a healthcare technology company providing
# patient engagement and data analytics solutions" - completely
# wrong, but passed every check because it wasn't generic).
#
# This pulls a random sample of upgraded accounts with their
# llm_specific_fact and assigned category, so you can manually
# verify a sample against reality before trusting the file.
#
# Usage:
#     python3 spot_check_classifications.py
# =====================================================

import pandas as pd

INPUT_FILE = "output/report1784905185024_Scored_with_classification.xlsx"
CHECKPOINT_FILE = "output/classification_prepass_results.xlsx"
OUTPUT_FILE = "output/classification_spot_check_sample.xlsx"

SAMPLE_SIZE = 60
RANDOM_SEED = 99

print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)

print(f"Loading: {CHECKPOINT_FILE} (for llm_specific_fact)")
classifications = pd.read_excel(CHECKPOINT_FILE)
classifications = classifications.drop_duplicates(subset="Account Name", keep="first")
fact_by_name = classifications.set_index("Account Name")["llm_specific_fact"].to_dict()

upgraded = accounts[
    accounts["company_signal_reason"].astype(str).str.contains("LLM classification", na=False)
].copy()

print(f"Total upgraded accounts: {len(upgraded)}")

upgraded["llm_specific_fact"] = upgraded["Account Name"].map(fact_by_name)

# Stratify the sample across tiers, not just random overall, so we
# check both the Tier 2/3 population (higher stakes - these will
# actually reach a seller) and the still-Tier-4 population.
sample_frames = []
for tier in ["Tier 2 Strong Target", "Tier 3 Nurture", "Tier 4 Monitor"]:
    tier_pool = upgraded[upgraded["priority_tier"] == tier]
    n = min(25 if tier != "Tier 4 Monitor" else 10, len(tier_pool))
    if n > 0:
        sample_frames.append(tier_pool.sample(n=n, random_state=RANDOM_SEED))

sample = pd.concat(sample_frames).sort_values(["priority_tier", "overall_coi"], ascending=[True, False])

display_cols = [
    "Account Name", "priority_tier", "overall_coi", "industry",
    "workload_profile", "llm_specific_fact"
]
display_cols = [c for c in display_cols if c in sample.columns]
sample = sample[display_cols].reset_index(drop=True)

sample.to_excel(OUTPUT_FILE, index=False)

print()
print("=========================================================")
print(f"SPOT-CHECK SAMPLE ({len(sample)} accounts, stratified by tier)")
print("=========================================================")
print(sample.to_string(index=False))
print()
print(f"Saved to: {OUTPUT_FILE}")
print()
print("FOR EACH ROW: does the llm_specific_fact match what this")
print("company actually does? Pay closest attention to Tier 2/3")
print("rows - those are the ones that will actually reach a seller.")
print("If you spot 2+ clearly fabricated facts (like BayMark being")
print("called a healthcare tech company when it's an addiction")
print("treatment provider), that's a real accuracy concern worth")
print("addressing before treating this file as canonical.")
