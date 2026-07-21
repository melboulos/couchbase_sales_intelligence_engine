import json
import os


PATTERN_FILE = "data/company_patterns.json"


# =====================================================
# LOAD PATTERNS
# =====================================================

def load_patterns():
    if not os.path.exists(PATTERN_FILE):
        return {}
    with open(PATTERN_FILE, "r") as file:
        return json.load(file)


PATTERNS = load_patterns()

KNOWN_COMPANIES = PATTERNS.get("known_companies", {})
BUSINESS_PATTERNS = PATTERNS.get("business_patterns", {})
WORKLOAD_PROFILES = PATTERNS.get("workload_profiles", {})


# =====================================================
# PROVIDER EXCLUSION
#
# Care-delivery organizations (hospitals, health systems,
# home care, hospice, senior living, etc.) are not
# Couchbase buyers, regardless of business-pattern
# keyword overlap with health-tech vendor terms.
#
# This check ONLY applies to the business_patterns
# matching path below. It runs AFTER known_companies
# matching (Pass 1 / Pass 2), so it can never override
# an explicit known_companies entry such as Redox or
# Staywell.
# =====================================================

PROVIDER_EXCLUDE_KEYWORDS = [
    "hospital",
    "medical center",
    "health system",
    "healthcare system",
    "clinic",
    "home care",
    "hospice",
    "senior living",
    "senior care",
    "nursing home",
    "rehabilitation",
    "urgent care",
    "physicians",
    "surgery center"
]


def is_excluded_provider(account_name):
    for phrase in PROVIDER_EXCLUDE_KEYWORDS:
        if phrase in account_name:
            return True
    return False


# =====================================================
# WORKLOAD STRENGTH LABEL
#
# Converts the numeric workload_strength sub-signal
# dictionary (from workload_profiles) into a High /
# Medium / Low label for sellers and the LLM.
#
# Does not affect COI scoring. scoring_engine.py reads
# database_intensity / operational_complexity /
# realtime_requirement directly as integers.
# =====================================================

def derive_workload_strength_label(profile):
    strength_map = profile.get("workload_strength", {})

    if not strength_map:
        return "Unknown"

    values = list(strength_map.values())
    average = sum(values) / len(values)

    if average >= 4:
        return "High"
    elif average >= 2.5:
        return "Medium"
    else:
        return "Low"


# =====================================================
# WORKLOAD PROFILE JOIN
#
# known_companies and business_patterns entries store
# a "workload_profile" pointer (e.g. "payment_platform")
# rather than the full scoring values. This looks up
# that pointer in workload_profiles and merges in the
# real database_intensity / operational_complexity /
# realtime_requirement / workload_strength values.
#
# known_company inline values (if present) take
# precedence over the joined profile values, since they
# represent more specific, validated data.
# =====================================================

def apply_workload_profile(result, data):
    profile_key = data.get("workload_profile", "")
    result["workload_profile"] = profile_key

    profile = WORKLOAD_PROFILES.get(profile_key, {})

    result["database_intensity"] = data.get(
        "database_intensity",
        profile.get("database_intensity", 0)
    )

    result["operational_complexity"] = data.get(
        "operational_complexity",
        profile.get("operational_complexity", 0)
    )

    result["realtime_requirement"] = data.get(
        "realtime_requirement",
        profile.get("realtime_requirement", 0)
    )

    result["workload_strength"] = derive_workload_strength_label(profile)

    return result


# =====================================================
# APPLY INTELLIGENCE DATA
# =====================================================

def apply_intelligence(result, data, reason):
    result["business_model"] = data.get("business_model", "Unknown")
    result["industry"] = data.get("industry", "Unknown")
    result["financial_segment"] = data.get("financial_segment", "Unknown")
    result["company_archetype"] = data.get("company_archetype", "Unknown")
    result["workloads"] = data.get("workloads", [])

    # New COI intelligence signals — joined via workload_profiles
    apply_workload_profile(result, data)

    # Keep existing compatibility
    result["company_signal_score"] = data.get("company_signal_score", 0)
    result["company_signal_reason"] = reason

    return result


# =====================================================
# COMPANY INTELLIGENCE
# =====================================================

def analyze_company(row):
    account_name = str(
        row.get("normalized_account_name", row.get("Account Name", ""))
    ).lower().strip()

    result = {
        "business_model": "Unknown",
        "industry": "Unknown",
        "financial_segment": "Unknown",
        "company_archetype": "Unknown",
        "workloads": [],
        "workload_profile": "",
        "workload_strength": "Unknown",
        "database_intensity": 0,
        "operational_complexity": 0,
        "realtime_requirement": 0,
        "company_signal_score": 0,
        "company_signal_reason": ""
    }

    # =====================================================
    # PASS 1
    # EXACT COMPANY MATCH
    #
    # Known companies always match here first. The
    # provider exclusion below never runs for these —
    # this pass returns immediately.
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():
        company_key = company.lower().strip()

        if account_name == company_key:
            return apply_intelligence(result, data, "Exact company match")

    # =====================================================
    # PASS 2
    # SAFE PARTIAL MATCH
    #
    # Same guarantee as Pass 1 — known companies are
    # protected from the provider exclusion.
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():
        company_key = company.lower().strip()

        if len(company_key) >= 6 and company_key in account_name:
            return apply_intelligence(result, data, "Partial company match")

    # =====================================================
    # PROVIDER EXCLUSION
    #
    # Only reached if no known_companies match was found.
    # Blocks care-delivery organizations from matching any
    # business pattern (e.g. Healthcare Technology), since
    # they are not Couchbase buyers regardless of keyword
    # overlap.
    # =====================================================

    if is_excluded_provider(account_name):
        return result

    # =====================================================
    # BUSINESS PATTERN MATCH
    # =====================================================

    for model, data in BUSINESS_PATTERNS.items():
        for keyword in data.get("keywords", []):
            keyword = keyword.lower().strip()

            if keyword in account_name:
                return apply_intelligence(
                    result, data, "Business pattern match: " + model
                )

    # =====================================================
    # NO MATCH
    # =====================================================

    return result
