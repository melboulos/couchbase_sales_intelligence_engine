# modules/industry_classifier.py

def classify_industry(row):

    name = str(
        row.get(
            "normalized_account_name",
            row.get("Account Name", "")
        )
    ).lower()


    industry = "Unknown"
    financial_segment = "Unknown"



    # =====================================================
    # Healthcare
    # =====================================================

    healthcare_keywords = [

        "health",
        "hospital",
        "medical",
        "healthcare",
        "clinic",
        "care",
        "patient",
        "behavioral",
        "pharmacy",
        "specialty health",
        "mcleod",
        "kaia",
        "aim specialty",
        "staywell",
        "mosaic life",
        "stormont",
        "sinai",
        "mount sinai",
        "saint luke",
        "saint francis",
        "saint vincent",
        "ascension"

    ]


    if any(
        keyword in name
        for keyword in healthcare_keywords
    ):

        industry = "Healthcare"

        return {
            "industry": industry,
            "financial_segment": financial_segment
        }



    # =====================================================
    # Financial Services
    # =====================================================

    financial_keywords = [

        "bank",
        "financial",
        "capital",
        "credit",
        "payment",
        "pay",
        "payments",
        "lending",
        "mortgage",
        "loan",
        "fund",
        "investment",
        "insurance",
        "wealth",
        "asset",
        "trevi",
        "netspend",
        "paya",
        "onpay",
        "paytronix",
        "payhub",
        "payroc",
        "paylink",
        "transcard",
        "evo",
        "crane payment",
        "priority payment",
        "payment alliance"

    ]


    if any(
        keyword in name
        for keyword in financial_keywords
    ):

        industry = "Financial Services"



        # -----------------------------
        # Payments
        # -----------------------------

        payment_keywords = [

            "payment",
            "pay",
            "payments",
            "card",
            "merchant",
            "transaction",
            "evo",
            "netspend",
            "paya",
            "paytronix",
            "payhub",
            "payroc",
            "paylink",
            "transcard"

        ]


        if any(
            keyword in name
            for keyword in payment_keywords
        ):

            financial_segment = "Payments"



        # -----------------------------
        # Lending
        # -----------------------------

        elif any(
            keyword in name
            for keyword in [
                "loan",
                "mortgage",
                "credit acceptance",
                "lending"
            ]
        ):

            financial_segment = "Lending"



        # -----------------------------
        # Investment
        # -----------------------------

        elif any(
            keyword in name
            for keyword in [
                "capital",
                "investment",
                "asset",
                "fund",
                "management"
            ]
        ):

            financial_segment = "Investment"



        elif "insurance" in name:

            financial_segment = "Insurance"



        return {
            "industry": industry,
            "financial_segment": financial_segment
        }



    # =====================================================
    # Technology / SaaS
    # =====================================================

    technology_keywords = [

        "saas",
        "software",
        "platform",
        "technology",
        "cloud",
        "api",
        "digital",
        "cleo",
        "peopleadmin",
        "banyan",
        "databank"

    ]


    if any(
        keyword in name
        for keyword in technology_keywords
    ):

        industry = "Technology / SaaS"


        return {
            "industry": industry,
            "financial_segment": financial_segment
        }



    # =====================================================
    # Retail
    # =====================================================

    retail_keywords = [

        "retail",
        "store",
        "commerce",
        "shopping",
        "marketplace"

    ]


    if any(
        keyword in name
        for keyword in retail_keywords
    ):

        industry = "Retail"


        return {
            "industry": industry,
            "financial_segment": financial_segment
        }



    # =====================================================
    # Energy
    # =====================================================

    energy_keywords = [

        "energy",
        "power",
        "electric",
        "utility"

    ]


    if any(
        keyword in name
        for keyword in energy_keywords
    ):

        industry = "Energy and Utilities"


        return {
            "industry": industry,
            "financial_segment": financial_segment
        }



    # =====================================================
    # Transportation
    # =====================================================

    transportation_keywords = [

        "logistics",
        "transport",
        "fleet",
        "shipping"

    ]


    if any(
        keyword in name
        for keyword in transportation_keywords
    ):

        industry = "Transportation and Logistics"


        return {
            "industry": industry,
            "financial_segment": financial_segment
        }



    # =====================================================
    # Default
    # =====================================================

    return {

        "industry": industry,

        "financial_segment": financial_segment

    }
