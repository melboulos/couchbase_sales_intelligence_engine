import pandas as pd
from modules.company_normalizer import normalize_account_name
from modules.industry_classifier import classify_industry
from modules.company_intelligence import analyze_company


# =====================================================
# NORMALIZATION
# =====================================================
def normalize_accounts(accounts):
    accounts["normalized_account_name"] = (
        accounts["Account Name"]
        .fillna("")
        .apply(normalize_account_name)
    )
    return accounts


# =====================================================
# INDUSTRY CLASSIFICATION
# =====================================================
def classify_industries(accounts):
    industry_results = accounts.apply(
        classify_industry,
        axis=1
    )
    industry_results = pd.DataFrame(
        industry_results.tolist()
    )
    accounts = pd.concat(
        [
            accounts.reset_index(drop=True),
            industry_results.reset_index(drop=True)
        ],
        axis=1
    )
    return accounts


# =====================================================
# COMPANY INTELLIGENCE
# =====================================================
def enrich_company_intelligence(accounts):
    company_results = accounts.apply(
        analyze_company,
        axis=1
    )
    company_results = pd.DataFrame(
        company_results.tolist()
    )
    # Preserve company intelligence fields
    for column in company_results.columns:
        if column == "industry":
            continue
        accounts[column] = company_results[column]
    # =================================================
    # COMPANY INDUSTRY OVERRIDE
    # =================================================
    accounts["industry"] = (
        company_results["industry"]
        .where(
            company_results["industry"] != "Unknown",
            accounts["industry"]
        )
    )

    # =================================================
    # REAL SALESFORCE INDUSTRY OVERRIDE
    #
    # A human-set Salesforce field beats any text-based guess from
    # either classification stage above. Confirmed real false
    # positives this fixes (2026-08-18): Wegmans Food Markets was
    # misclassified as "Healthcare" via a "healthier" substring
    # collision in marketing copy (real SF Industry: "Retail");
    # Envestnet and Interactive Brokers Group were also
    # misclassified as "Healthcare" via a second, unexplained
    # mechanism (real SF Industry: "Financial Software" / "Finance").
    # Only applies when this file actually has a real, non-blank
    # Industry column - files without it are completely unaffected.
    # =================================================
    if "Industry" in accounts.columns:
        real_industry = accounts["Industry"].astype(str).str.strip()
        has_real_industry = (
            real_industry.notna()
            & (real_industry != "")
            & (real_industry.str.lower() != "nan")
        )
        accounts["industry"] = accounts["industry"].where(
            ~has_real_industry, real_industry
        )

    return accounts
