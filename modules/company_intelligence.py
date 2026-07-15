import json


PATTERN_FILE = "data/company_patterns.json"


with open(PATTERN_FILE, "r") as f:
    COMPANY_PATTERNS = json.load(f)



def analyze_company(row):

    name = str(
        row.get(
            "normalized_account_name",
            row.get("Account Name", "")
        )
    ).lower()


    industry = "Unknown"
    business_model = "Unknown"

    workloads = []

    reason = ""

    score = 0


    database_pressure = "Unknown"

    modernization_signal = "Unknown"

    couchbase_use_cases = []

    buyer_personas = []



    # =========================================
    # Known Company Match
    # =========================================

    for company, profile in COMPANY_PATTERNS.get(
        "known_companies",
        {}
    ).items():

        if company in name:

            industry = profile.get(
                "industry",
                "Unknown"
            )

            business_model = profile.get(
                "business_model",
                "Unknown"
            )

            workloads = profile.get(
                "workloads",
                []
            )

            reason = profile.get(
                "reason",
                ""
            )

            score += profile.get(
                "score_boost",
                0
            )

            break



    # =========================================
    # Business Pattern Match
    # =========================================

    if industry == "Unknown":

        for pattern, profile in COMPANY_PATTERNS.get(
            "business_patterns",
            {}
        ).items():

            keywords = profile.get(
                "keywords",
                []
            )


            if any(
                keyword in name
                for keyword in keywords
            ):

                industry = profile.get(
                    "industry",
                    "Unknown"
                )

                business_model = pattern

                workloads = profile.get(
                    "workloads",
                    []
                )

                score += profile.get(
                    "score_boost",
                    0
                )

                break



    # =========================================
    # Couchbase Workload Intelligence
    # =========================================

    if industry == "Financial Services":

        database_pressure = (
            "High transactional data volume"
        )

        modernization_signal = (
            "Legacy database modernization"
        )

        couchbase_use_cases = [
            "Customer 360",
            "Transaction processing",
            "Fraud detection",
            "Real-time account services"
        ]

        buyer_personas = [
            "VP Engineering",
            "Database Architect",
            "Digital Banking Technology"
        ]



    elif industry == "Healthcare":

        database_pressure = (
            "Patient data complexity"
        )

        modernization_signal = (
            "Healthcare application modernization"
        )

        couchbase_use_cases = [
            "Patient profiles",
            "Healthcare applications",
            "Provider data"
        ]

        buyer_personas = [
            "Healthcare Technology Leader",
            "Enterprise Architect",
            "Data Platform Team"
        ]



    elif industry == "Technology / SaaS":

        database_pressure = (
            "Application scalability"
        )

        modernization_signal = (
            "Cloud-native modernization"
        )

        couchbase_use_cases = [
            "Application database",
            "Customer profiles",
            "Real-time applications"
        ]

        buyer_personas = [
            "CTO",
            "VP Engineering",
            "Software Architecture"
        ]



    elif industry == "Retail":

        database_pressure = (
            "Customer experience and personalization"
        )

        modernization_signal = (
            "Digital commerce modernization"
        )

        couchbase_use_cases = [
            "Customer 360",
            "Product catalog",
            "Personalization"
        ]

        buyer_personas = [
            "Digital Commerce Leader",
            "VP Engineering",
            "Enterprise Architect"
        ]



    # =========================================
    # Return
    # =========================================

    return {

        "industry": industry,

        "business_model": business_model,

        "workloads": workloads,

        "company_reason": reason,

        "database_pressure": database_pressure,

        "modernization_signal": modernization_signal,

        "couchbase_use_cases": couchbase_use_cases,

        "buyer_personas": buyer_personas,

        "company_signal_score": score

    }
