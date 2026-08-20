import pandas as pd
from modules.company_normalizer import normalize_account_name
from modules.industry_classifier import classify_industry
from modules.company_intelligence import analyze_company, _match_business_pattern, BUSINESS_PATTERNS


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

    # =================================================
    # SIC CODE FALLBACK
    #
    # A standardized US government industry classification code -
    # independent of both the keyword-based guess above AND the real
    # Salesforce Industry field below. Used here as a fallback when
    # Industry is blank but SIC Code is present - a real, recorded
    # code beats a keyword guess. Only covers codes actually observed
    # in real data so far, not an exhaustive SIC reference - returns
    # None (no change) for anything not in the map, rather than
    # guessing.
    # =================================================
    SIC_TO_INDUSTRY = {
        "602": "Banking", "603": "Banking",
        "609": "Financial Services", "631": "Insurance",
        # "679" deliberately excluded - it's the generic "Offices of
        # Holding Companies, Not Elsewhere Classified" SIC code, not
        # a real indicator of insurance or any specific industry.
        # Mistakenly mapped to "Insurance" originally; caught before
        # it could cause a real misclassification.
        "421": "Trucking & Logistics", "422": "Trucking & Logistics",
        "541": "Grocery Retail", "531": "Retail", "596": "Retail",
        "737": "Software / IT Services", "738": "Business Services",
        "873": "Professional Services",
        "801": "Healthcare", "806": "Healthcare",
        "283": "Pharmaceuticals", "384": "Medical Devices",
        "481": "Telecommunications", "482": "Telecommunications",
        "491": "Utilities", "492": "Utilities",
        "731": "Advertising", "781": "Media & Entertainment",
    }

    if "SIC Code" in accounts.columns:
        def _sic_lookup(code):
            if pd.isna(code):
                return None
            try:
                code_str = str(int(code))
            except (ValueError, TypeError):
                code_str = str(code).strip()
            return SIC_TO_INDUSTRY.get(code_str)

        sic_industry = accounts["SIC Code"].apply(_sic_lookup)
        has_sic_match = sic_industry.notna()
        current_is_unknown = accounts["industry"] == "Unknown"
        accounts["industry"] = accounts["industry"].where(
            ~(has_sic_match & current_is_unknown), sic_industry
        )

    # =================================================
    # REAL SALESFORCE INDUSTRY OVERRIDE
    #
    # A human-set Salesforce field beats any text-based guess from
    # either classification stage above (and beats SIC Code too).
    # Confirmed real false positives this fixes (2026-08-18): Wegmans
    # Food Markets was misclassified as "Healthcare" via a
    # "healthier" substring collision in marketing copy (real SF
    # Industry: "Retail"); Envestnet and Interactive Brokers Group
    # were also misclassified as "Healthcare" via a second,
    # unexplained mechanism (real SF Industry: "Financial Software" /
    # "Finance"). Only applies when this file actually has a real,
    # non-blank Industry column - files without it are completely
    # unaffected.
    # =================================================
    if "Industry" in accounts.columns:
        real_industry = accounts["Industry"].astype(str).str.strip()
        has_real_industry = (
            real_industry.notna()
            & (real_industry != "")
            & (real_industry.str.lower() != "nan")
        )
        accounts["industry"] = accounts["industry"].where(
            ~has_real_industry, real_industry
        )

    # Shorten verbose real Salesforce industry labels for display -
    # the account manager's own detailed categorization is still
    # useful, but "Customer Relationship Management (CRM) Software"
    # is too long to read comfortably in a table column.
    INDUSTRY_SHORTEN_MAP = {
        "Customer Relationship Management (CRM) Software": "CRM Software",
        "Credit Cards & Transaction Processing": "Payment Processing",
        "Hospitals & Physicians Clinics": "Healthcare",
        "Advertising & Marketing": "Advertising",
        "Freight & Logistics Services": "Freight",
        "Logistics & Transportation": "Logistics",
    }
    accounts["industry"] = accounts["industry"].replace(INDUSTRY_SHORTEN_MAP)

    # =================================================
    # WORKLOAD PROFILE RE-DERIVATION
    #
    # Confirmed real, major finding (2026-08-19): workload_profile is
    # only ever set once via keyword-matching, BEFORE the real
    # Salesforce Industry override above runs - and nothing ever
    # re-derives it afterward. When the real Industry corrects a
    # wrong keyword guess (confirmed happening for the majority of
    # accounts with both fields set - 2,871 of 3,850 in a real
    # 9,589-account file), the industry LABEL gets fixed but the
    # actual technical SCORING keeps running on the original, wrong
    # profile (confirmed real case: Regis Corporation, a hair salon
    # chain, correctly relabeled "Barber Shops & Beauty Salons" but
    # still scored as if it were "media_platform").
    #
    # Deliberately NOT a rigid Industry->workload_profile map (a
    # Software company can legitimately have a payment_platform
    # workload if there's real evidence for it - Industry is a
    # contextual signal, workload_profile is a technical hypothesis,
    # not the same thing). Instead, re-runs the SAME keyword-matching
    # logic already used elsewhere, with the corrected industry
    # added as additional matching text alongside the account name -
    # preserving legitimate exceptions where the account's own name
    # still supports the original workload, while correcting cases
    # where nothing about the real industry supports it.
    #
    # Verified via a controlled before/after analysis before
    # shipping: of 2,871 real mismatched accounts, 1,184 (41%) showed
    # material COI inflation (10+ points) from the wrong profile, 63
    # showed the workload had been suppressing a legitimate score,
    # and 12 accounts had already gone through real LLM validation
    # under a qualification that would not have qualified under
    # corrected scoring.
    # =================================================
    if "workload_profile" in accounts.columns:
        profile_to_industries = {}
        for _pattern_name, _pattern_data in BUSINESS_PATTERNS.items():
            _profile = _pattern_data.get("workload_profile")
            _industry = _pattern_data.get("industry")
            profile_to_industries.setdefault(_profile, set()).add(_industry)

        for idx, row in accounts.iterrows():
            current_profile = row.get("workload_profile")
            current_industry = row.get("industry")
            if pd.isna(current_profile) or current_profile == "" or pd.isna(current_industry):
                continue

            expected_industries = profile_to_industries.get(current_profile, set())
            if current_industry in expected_industries:
                continue

            account_name = str(row.get("Account Name", "")).lower()
            combined_text = account_name + " " + str(current_industry).lower()
            match_result = _match_business_pattern(combined_text, "industry-re-derivation")

            if match_result is not None:
                accounts.at[idx, "workload_profile"] = match_result.get("workload_profile")
                accounts.at[idx, "database_intensity"] = match_result.get("database_intensity")
                accounts.at[idx, "operational_complexity"] = match_result.get("operational_complexity")
                accounts.at[idx, "realtime_requirement"] = match_result.get("realtime_requirement")
                accounts.at[idx, "workloads"] = match_result.get("workloads", [])
            else:
                accounts.at[idx, "workload_profile"] = ""
                accounts.at[idx, "workloads"] = []

    return accounts
