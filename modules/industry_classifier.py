# modules/industry_classifier.py


def _classify_industry_from_text(text):
    """
    The exact same keyword logic that used to live directly inside
    classify_industry(), now factored out so it can be called twice:
    once against the account name alone (unchanged behavior for
    every account that already matches), and once more against
    name + cached web search snippet text as a fallback ONLY when
    the name-alone pass finds nothing. Every keyword list below is
    identical to what was already here - no new patterns, no
    changed matching logic, just a second chance to run the SAME
    check against richer text.
    """

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

    if any(keyword in text for keyword in healthcare_keywords):
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

    if any(keyword in text for keyword in financial_keywords):
        industry = "Financial Services"

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

        if any(keyword in text for keyword in payment_keywords):
            financial_segment = "Payments"

        elif any(keyword in text for keyword in ["loan", "mortgage", "credit acceptance", "lending"]):
            financial_segment = "Lending"

        elif any(keyword in text for keyword in ["capital", "investment", "asset", "fund", "management"]):
            financial_segment = "Investment"

        elif "insurance" in text:
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

    if any(keyword in text for keyword in technology_keywords):
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

    if any(keyword in text for keyword in retail_keywords):
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

    if any(keyword in text for keyword in energy_keywords):
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

    if any(keyword in text for keyword in transportation_keywords):
        industry = "Transportation and Logistics"
        return {
            "industry": industry,
            "financial_segment": financial_segment
        }

    # =====================================================
    # Default - no match
    # =====================================================

    return {
        "industry": industry,
        "financial_segment": financial_segment
    }


def classify_industry(row):

    name = str(
        row.get(
            "normalized_account_name",
            row.get("Account Name", "")
        )
    ).lower()

    # Pass 1: name alone - unchanged behavior for every account
    # that already matches today.
    result = _classify_industry_from_text(name)
    if result["industry"] != "Unknown":
        result["industry_match_source"] = "account_name"
        return result

    # Pass 2: name-alone found nothing - fall back to name + cached
    # web search snippet text (from serper_enrichment_pass.py's
    # output/serper_search_cache.xlsx, merged into the accounts
    # DataFrame earlier in main.py as "web_search_snippets"). This
    # is a FREE fallback - reuses the exact same keyword lists
    # above, no new LLM cost, no new search cost (search already
    # happened and was cached).
    snippet_text = row.get("web_search_snippets", "")
    if snippet_text and str(snippet_text).strip():
        combined_text = name + " " + str(snippet_text).lower()
        result = _classify_industry_from_text(combined_text)
        if result["industry"] != "Unknown":
            result["industry_match_source"] = "web_search"
            return result

    return {
        "industry": "Unknown",
        "financial_segment": "Unknown",
        "industry_match_source": "none"
    }
