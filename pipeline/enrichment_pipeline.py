import pandas as pd
import json

from modules.company_normalizer import normalize_account_name
from modules.industry_classifier import classify_industry
from modules.company_intelligence import analyze_company

from schemas.account_intelligence_schema import build_account_intelligence


# =====================================================
# CONFIGURATION
# =====================================================

# Safety limit while testing LLM workflow
LLM_TEST_LIMIT = 10



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


    return accounts



# =====================================================
# SELECT LLM CANDIDATES
# =====================================================

def select_llm_candidates(accounts, limit=LLM_TEST_LIMIT):

    """
    Select only prioritized accounts for LLM validation.

    During testing:
        Top 10 accounts only

    Production:
        Increase limit or remove restriction.
    """

    if "overall_coi" not in accounts.columns:

        raise Exception(
            "overall_coi missing. Run scoring engine before LLM selection."
        )


    candidates = (
        accounts
        .sort_values(
            "overall_coi",
            ascending=False
        )
        .head(limit)
    )


    return candidates



# =====================================================
# STREAMLIT OUTPUT CONTRACT
# =====================================================

def generate_account_intelligence_json(accounts):

    account_intelligence = [
        build_account_intelligence(row)
        for _, row in accounts.iterrows()
    ]


    with open(
        "output/account_intelligence.json",
        "w"
    ) as f:

        json.dump(
            account_intelligence,
            f,
            indent=2
        )


    return account_intelligence
