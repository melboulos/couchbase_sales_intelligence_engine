def classify_industry(row):

    account_name = str(
        row.get(
            "normalized_account_name",
            ""
        )
    ).lower()


    industry = "Unknown"



    # Technology / SaaS
    tech_keywords = [
        "technology",
        "software",
        "systems",
        "platform",
        "data",
        "digital",
        "cloud",
        "analytics",
        "solutions"
    ]

    if any(
        word in account_name
        for word in tech_keywords
    ):
        industry = "Technology / SaaS"



    # Financial Services
    finance_keywords = [
        "bank",
        "capital",
        "payment",
        "financial",
        "finance",
        "insurance",
        "credit"
    ]

    if any(
        word in account_name
        for word in finance_keywords
    ):
        industry = "Financial Services"



    # Healthcare
    healthcare_keywords = [
        "health",
        "medical",
        "care",
        "hospital",
        "clinical",
        "pharma"
    ]

    if any(
        word in account_name
        for word in healthcare_keywords
    ):
        industry = "Healthcare"



    # Energy
    energy_keywords = [
        "energy",
        "power",
        "electric",
        "utility"
    ]

    if any(
        word in account_name
        for word in energy_keywords
    ):
        industry = "Energy and Utilities"



    # Retail
    retail_keywords = [
        "retail",
        "store",
        "market"
    ]

    if any(
        word in account_name
        for word in retail_keywords
    ):
        industry = "Retail"



    # Transportation
    transportation_keywords = [
        "rail",
        "transport",
        "logistics"
    ]

    if any(
        word in account_name
        for word in transportation_keywords
    ):
        industry = "Transportation and Logistics"



    return {

        "industry": industry

    }
