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


    # Preserve company intelligence values

    for column in company_results.columns:

        if column == "industry":

            continue


        accounts[column] = company_results[column]



    # =====================================================
    # COMPANY INDUSTRY OVERRIDE
    # =====================================================

    accounts["industry"] = (
        company_results["industry"]
        .where(
            company_results["industry"] != "Unknown",
            accounts["industry"]
        )
    )


    return accounts
    accounts = pd.concat(
        [
            accounts.reset_index(drop=True),
            company_results.reset_index(drop=True)
        ],
        axis=1
    )


    accounts["industry"] = (
        company_industry.where(
            company_industry != "Unknown",
            accounts["industry"]
        )
    )


    return accounts
