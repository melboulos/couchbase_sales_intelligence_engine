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

from pipeline.llm_validation_pipeline import validate_accounts

from modules.llm_candidate_selector import select_llm_candidate
from modules.sales_brief_generator import generate_sales_brief
from modules.opportunity_explainer import generate_opportunity_explanation

from pipeline.intelligence_export_pipeline import export_account_intelligence



print("Starting Couchbase Sales Intelligence Engine")
print("-------------------------------------------")


INPUT_FILE = "input/Enterprise_East_Account_List.xlsx"

OUTPUT_FILE = "output/Enterprise_East_Scored.xlsx"



# =====================================================
# LOAD
# =====================================================

accounts = load_accounts(INPUT_FILE)

print(
    f"Loaded {len(accounts)} accounts"
)


print("\nColumns found:")

for col in accounts.columns:
    print(f"- {col}")



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

accounts = accounts.loc[
    :,
    ~accounts.columns.duplicated()
]


print(
    "\nDuplicate columns cleaned"
)



# =====================================================
# COMPANY ARCHETYPE
# =====================================================

print(
    "\nClassifying company archetypes..."
)

accounts = enrich_company_archetypes(accounts)



# =====================================================
# SCORE
# =====================================================

print(
    "\nCalculating Couchbase Opportunity Index..."
)

accounts = score_accounts(accounts)



# =====================================================
# OPPORTUNITY EXPLANATION
# =====================================================

print(
    "\nGenerating opportunity explanations..."
)


opportunity_results = accounts.apply(
    generate_opportunity_explanation,
    axis=1
)


opportunity_results = pd.DataFrame(
    opportunity_results.tolist()
)


accounts = pd.concat(
    [
        accounts.reset_index(drop=True),
        opportunity_results.reset_index(drop=True)
    ],
    axis=1
)



# =====================================================
# LLM CANDIDATE SELECTION
# =====================================================

print(
    "\nSelecting LLM enrichment candidates..."
)


LLM_TEST_LIMIT = 10


llm_candidates = (
    accounts
    .sort_values(
        "overall_coi",
        ascending=False
    )
    .head(
        LLM_TEST_LIMIT
    )
)


print(
    f"Selected {len(llm_candidates)} accounts for LLM validation"
)



# =====================================================
# ADD LLM METADATA
# =====================================================

llm_results = llm_candidates.apply(
    select_llm_candidate,
    axis=1
)


llm_results = pd.DataFrame(
    llm_results.tolist()
)


llm_candidates = pd.concat(
    [
        llm_candidates.reset_index(drop=True),
        llm_results.reset_index(drop=True)
    ],
    axis=1
)



# =====================================================
# LLM VALIDATION
# =====================================================

print(
    "\nRunning LLM validation..."
)


llm_accounts = validate_accounts(
    llm_candidates
)



# =====================================================
# SALES BRIEFS
# =====================================================

print(
    "\nGenerating sales account briefs..."
)


brief_results = llm_accounts.apply(
    generate_sales_brief,
    axis=1
)


brief_results = pd.DataFrame(
    brief_results.tolist()
)


llm_accounts = pd.concat(
    [
        llm_accounts.reset_index(drop=True),
        brief_results.reset_index(drop=True)
    ],
    axis=1
)



# =====================================================
# MERGE LLM INTELLIGENCE BACK
# =====================================================

print(
    "\nMerging LLM intelligence back into full dataset..."
)


llm_merge_columns = [

    "Account Name",

    "llm_run_id",

    "llm_validation",

    "llm_opportunity_score",

    "coi_assessment",

    "coi_delta_reason",

    "opportunity_summary",

    "couchbase_trigger",

    "evidence_found",

    "missing_evidence",

    "database_replacement_probability",

    "technical_risk",

    "seller_action",

    "discovery_questions",

    "llm_reasoning"

]


llm_merge_columns = [
    c
    for c in llm_merge_columns
    if c in llm_accounts.columns
]


print(
    "\nLLM merge columns:"
)

for c in llm_merge_columns:
    print(
        "-",
        c
    )



accounts = accounts.merge(
    llm_accounts[
        llm_merge_columns
    ],
    on="Account Name",
    how="left"
)



# =====================================================
# FINAL CLEAN
# =====================================================

accounts = accounts.loc[
    :,
    ~accounts.columns.duplicated()
]



# =====================================================
# EXPORT EXCEL
# =====================================================

accounts.to_excel(
    OUTPUT_FILE,
    index=False
)



# =====================================================
# EXPORT LLM TEST OUTPUT
# =====================================================

llm_accounts.to_excel(
    "output/LLM_Validated_Accounts.xlsx",
    index=False
)



# =====================================================
# EXPORT STREAMLIT JSON
# =====================================================

export_account_intelligence(
    accounts
)



print(
    "\n-------------------------------------------"
)

print(
    "Completed"
)


print(
    f"Accounts processed: {len(accounts)}"
)


print(
    f"Full output: {OUTPUT_FILE}"
)