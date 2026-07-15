def enrich_account(row):

    account = str(
        row.get(
            "normalized_account_name",
            row.get("Account Name", "")
        )
    ).lower()


    industry = str(
        row.get(
            "industry",
            "Unknown"
        )
    )


    business_model = str(
        row.get(
            "business_model",
            "Unknown"
        )
    )


    company_signal = int(
        row.get(
            "company_signal_score",
            0
        )
    )


    technology_score = int(
        row.get(
            "technology_score",
            0
        )
    )


    workloads = row.get(
        "workloads",
        []
    )


    company_size = "Unknown"
    revenue_signal = "Unknown"
    engineering_signal = "Unknown"
    ai_initiatives = "Unknown"


    # =====================================================
    # COMPANY SIZE
    # =====================================================


    enterprise_industries = [
        "Financial Services",
        "Healthcare",
        "Energy and Utilities",
        "Transportation and Logistics"
    ]


    if industry in enterprise_industries:
        company_size = "Enterprise"


    enterprise_terms = [
        "bank",
        "capital",
        "insurance",
        "corporation",
        "company",
        "group",
        "international",
        "holdings"
    ]


    if any(
        term in account
        for term in enterprise_terms
    ):
        company_size = "Enterprise"



    # =====================================================
    # REVENUE SIGNAL
    # =====================================================


    if company_signal >= 20:
        revenue_signal = "High"

    elif company_signal >= 10:
        revenue_signal = "Medium"



    # =====================================================
    # ENGINEERING SIGNAL
    # =====================================================


    if (
        industry in [
            "Technology / SaaS",
            "Financial Services",
            "Healthcare"
        ]
        or technology_score >= 10
        or len(workloads) > 0
    ):
        engineering_signal = "High"



    # =====================================================
    # AI OPPORTUNITY
    # =====================================================


    if business_model == "FinTech":
        ai_initiatives = (
            "Fraud detection, "
            "risk analytics, "
            "customer intelligence AI"
        )


    elif business_model == "Healthcare Technology":

        ai_initiatives = (
            "Patient analytics, "
            "clinical intelligence, "
            "healthcare AI"
        )


    elif business_model == "Integration Platform":

        ai_initiatives = (
            "Automation, "
            "API intelligence, "
            "real-time data processing"
        )


    elif business_model == "HR SaaS":

        ai_initiatives = (
            "Workforce analytics, "
            "employee intelligence AI"
        )


    elif business_model == "Travel Technology":

        ai_initiatives = (
            "Personalization, "
            "recommendation engines"
        )


    return {

        "company_size": company_size,

        "revenue_signal": revenue_signal,

        "engineering_signal": engineering_signal,

        "ai_initiatives": ai_initiatives

    }
