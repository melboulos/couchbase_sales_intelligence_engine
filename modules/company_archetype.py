def classify_company_archetype(row):

    name = str(
        row.get(
            "Account Name",
            ""
        )
    ).lower()


    industry = str(
        row.get(
            "industry",
            ""
        )
    ).lower()


    text = name + " " + industry



    # ==========================================
    # HEALTHCARE PROVIDER
    # ==========================================

    provider_signals = [

        "hospital",

        "medical center",

        "health system",

        "health center",

        "health network",

        "healthcare network",

        "regional medical",

        "clinic",

        "medical group",

        "care center",

        "care hospital",

        "university health",

        "health services"

    ]


    for signal in provider_signals:

        if signal in text:

            return "Healthcare Provider"



    # ==========================================
    # HEALTHCARE TECHNOLOGY
    # ==========================================

    healthcare_tech_signals = [

        "healthtech",

        "health technology",

        "health analytics",

        "health data",

        "medical software",

        "digital health",

        "health platform",

        "healthcare technology",

        "patient engagement",

        "patient data",

        "health solutions"

    ]


    for signal in healthcare_tech_signals:

        if signal in text:

            return "Healthcare Technology"



    # ==========================================
    # FINTECH / PAYMENTS
    # ==========================================

    fintech_signals = [

        "payment",

        "payments",

        "wallet",

        "lending",

        "loan",

        "fintech",

        "merchant",

        "transaction"

    ]


    for signal in fintech_signals:

        if signal in text:

            return "FinTech / Payments"



    # ==========================================
    # FINANCIAL INSTITUTION
    # ==========================================

    financial_signals = [

        "bank",

        "credit union",

        "savings bank",

        "financial institution"

    ]


    for signal in financial_signals:

        if signal in text:

            return "Financial Institution"



    # ==========================================
    # SOFTWARE / PLATFORM
    # ==========================================

    software_signals = [

        "software",

        "saas",

        "platform",

        "api",

        "cloud",

        "developer",

        "integration",

        "data platform",

        "analytics platform"

    ]


    for signal in software_signals:

        if signal in text:

            return "Software / Platform"



    # ==========================================
    # DEFAULT
    # ==========================================

    return "Other"
