import json
import os


PATTERN_FILE = "data/company_patterns.json"



# =====================================================
# LOAD PATTERNS
# =====================================================

def load_patterns():

    if not os.path.exists(PATTERN_FILE):
        return {}

    with open(
        PATTERN_FILE,
        "r"
    ) as file:
        return json.load(file)



PATTERNS = load_patterns()


KNOWN_COMPANIES = PATTERNS.get(
    "known_companies",
    {}
)


BUSINESS_PATTERNS = PATTERNS.get(
    "business_patterns",
    {}
)



# =====================================================
# COMPANY INTELLIGENCE
# =====================================================

def analyze_company(row):


    account_name = str(
        row.get(
            "normalized_account_name",
            row.get(
                "Account Name",
                ""
            )
        )
    ).lower().strip()



    result = {

        "business_model": "Unknown",

        "industry": "Unknown",

        "financial_segment": "Unknown",

        "workloads": [],

        "company_signal_score": 0,

        "company_signal_reason": ""

    }



    # =====================================================
    # KNOWN COMPANY OVERRIDE
    #
    # Pass 1:
    # Exact company match
    #
    # Prevents:
    # Cleo -> McLeod
    # AI -> AIM
    # Pay -> unrelated companies
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():

        company_key = company.lower().strip()


        if account_name == company_key:


            result["business_model"] = data.get(
                "business_model",
                "Unknown"
            )


            result["industry"] = data.get(
                "industry",
                "Unknown"
            )


            result["workloads"] = data.get(
                "workloads",
                []
            )


            result["company_signal_score"] = data.get(
                "score_boost",
                0
            )


            result["company_signal_reason"] = data.get(
                "reason",
                ""
            )


            return result



    # =====================================================
    # KNOWN COMPANY OVERRIDE
    #
    # Pass 2:
    # Safe partial matching
    #
    # Only allow longer names
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():

        company_key = company.lower().strip()


        if (
            len(company_key) >= 6
            and company_key in account_name
        ):


            result["business_model"] = data.get(
                "business_model",
                "Unknown"
            )


            result["industry"] = data.get(
                "industry",
                "Unknown"
            )


            result["workloads"] = data.get(
                "workloads",
                []
            )


            result["company_signal_score"] = data.get(
                "score_boost",
                0
            )


            result["company_signal_reason"] = data.get(
                "reason",
                ""
            )


            return result



    # =====================================================
    # BUSINESS PATTERN MATCH
    # =====================================================

    for model, data in BUSINESS_PATTERNS.items():


        for keyword in data.get(
            "keywords",
            []
        ):


            keyword = keyword.lower().strip()


            if keyword in account_name:


                result["business_model"] = model


                result["industry"] = data.get(
                    "industry",
                    "Unknown"
                )


                result["workloads"] = data.get(
                    "workloads",
                    []
                )


                result["company_signal_score"] = data.get(
                    "score_boost",
                    0
                )


                result["company_signal_reason"] = (
                    "Matched business pattern: "
                    + model
                )


                return result



    return result
