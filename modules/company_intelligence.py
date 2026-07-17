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
# APPLY INTELLIGENCE DATA
# =====================================================

def apply_intelligence(
    result,
    data,
    reason
):


    result["business_model"] = data.get(
        "business_model",
        "Unknown"
    )


    result["industry"] = data.get(
        "industry",
        "Unknown"
    )


    result["financial_segment"] = data.get(
        "financial_segment",
        "Unknown"
    )


    result["company_archetype"] = data.get(
        "company_archetype",
        "Unknown"
    )


    result["workloads"] = data.get(
        "workloads",
        []
    )


    # New COI intelligence signals

    result["workload_strength"] = data.get(
        "workload_strength",
        "Unknown"
    )


    result["database_intensity"] = data.get(
        "database_intensity",
        0
    )


    result["operational_complexity"] = data.get(
        "operational_complexity",
        0
    )


    result["realtime_requirement"] = data.get(
        "realtime_requirement",
        0
    )


    result["couchbase_fit_reason"] = data.get(
        "couchbase_fit_reason",
        ""
    )


    # Keep existing compatibility

    result["company_signal_score"] = data.get(
        "company_signal_score",
        0
    )


    result["company_signal_reason"] = reason


    return result



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

        "company_archetype": "Unknown",

        "workloads": [],

        "workload_strength": "Unknown",

        "database_intensity": 0,

        "operational_complexity": 0,

        "realtime_requirement": 0,

        "couchbase_fit_reason": "",

        "company_signal_score": 0,

        "company_signal_reason": ""

    }



    # =====================================================
    # PASS 1
    # EXACT COMPANY MATCH
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():

        company_key = company.lower().strip()


        if account_name == company_key:


            return apply_intelligence(
                result,
                data,
                "Exact company match"
            )



    # =====================================================
    # PASS 2
    # SAFE PARTIAL MATCH
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():

        company_key = company.lower().strip()


        if (
            len(company_key) >= 6
            and company_key in account_name
        ):


            return apply_intelligence(
                result,
                data,
                "Partial company match"
            )



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


                return apply_intelligence(
                    result,
                    data,
                    "Business pattern match: " + model
                )



    # =====================================================
    # NO MATCH
    # =====================================================

    return result
