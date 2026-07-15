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
from pipeline.scoring_pipeline import score_accounts

from modules.llm_candidate_selector import select_llm_candidate
from modules.sales_brief_generator import generate_sales_brief



print("Starting Couchbase Sales Intelligence Engine")
print("-------------------------------------------")


INPUT_FILE = "input/Enterprise_East_Account_List.xlsx"

OUTPUT_FILE = (
    "output/"
    "Enterprise_East_Scored.xlsx"
)



# =====================================================
# LOAD
# =====================================================

accounts = load_accounts(
    INPUT_FILE
)


print("Columns found:")

for col in accounts.columns:
    print(f"- {col}")



# =====================================================
# NORMALIZATION
# =====================================================

print("\nRunning normalization...")

accounts = normalize_accounts(
    accounts
)



# =====================================================
# INDUSTRY CLASSIFICATION
# =====================================================

print("\nRunning industry classification...")

accounts = classify_industries(
    accounts
)



# =====================================================
# COMPANY INTELLIGENCE
# =====================================================

print("\nRunning company intelligence...")

accounts = enrich_company_intelligence(
    accounts
)


print("\nCompany intelligence sample:")

print(
    accounts[
        [
            "Account Name",
            "industry",
            "business_model",
            "workloads",
            "company_signal_score"
        ]
    ].head(25)
)



# =====================================================
# TECHNOLOGY ENRICHMENT
# =====================================================

print("\nRunning technology enrichment...")

accounts = enrich_technology(
    accounts
)



# =====================================================
# ACCOUNT INTELLIGENCE
# =====================================================

print("\nRunning account intelligence...")

accounts = enrich_account_intelligence(
    accounts
)



# =====================================================
# ACCOUNT ENRICHMENT
# =====================================================

print("\nRunning account enrichment...")

accounts = enrich_accounts(
    accounts
)



# =====================================================
# CLEAN DUPLICATES
# =====================================================

accounts = accounts.loc[
    :,
    ~accounts.columns.duplicated()
]


print("\nDuplicate columns cleaned")



# =====================================================
# COUCHBASE OPPORTUNITY INDEX
# =====================================================

print("\nCalculating Couchbase Opportunity Index...")

accounts = score_accounts(
    accounts
)



# =====================================================
# LLM CANDIDATES
# =====================================================

print("\nSelecting LLM enrichment candidates...")


llm_results = accounts.apply(
    select_llm_candidate,
    axis=1
)


llm_results = pd.DataFrame(
    llm_results.tolist()
)


accounts = pd.concat(
    [
        accounts.reset_index(drop=True),
        llm_results.reset_index(drop=True)
    ],
    axis=1
)



# =====================================================
# SALES BRIEFS
# =====================================================

print("\nGenerating sales account briefs...")


brief_results = accounts.apply(
    generate_sales_brief,
    axis=1
)


brief_results = pd.DataFrame(
    brief_results.tolist()
)


accounts = pd.concat(
    [
        accounts.reset_index(drop=True),
        brief_results.reset_index(drop=True)
    ],
    axis=1
)



# =====================================================
# FINAL CLEAN
# =====================================================

accounts = accounts.loc[
    :,
    ~accounts.columns.duplicated()
]



# =====================================================
# EXPORT
# =====================================================

accounts.to_excel(
    OUTPUT_FILE,
    index=False
)



print("\n-------------------------------------------")
print("Completed")


print(
    f"Accounts processed: {len(accounts)}"
)


print(
    f"Full output: {OUTPUT_FILE}"
)