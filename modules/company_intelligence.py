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
# KNOWN, OPEN LIMITATIONS (2026-07-29 stratified audit)
#
# Found via a real audit of the population that only qualified
# for LLM enrichment via the web-search fallback below. Neither
# is fixed in this pass - both need more real examples before a
# safe rule can be written, or are fundamentally not fixable via
# keyword rules at all.
#
# 1. "VENDOR SERVES AN INDUSTRY" MISMATCH (general case) -
#    ParkOps ("outsourced hospitality services -- Automotive
#    Retail, Hotels") tagged Retail; Affinity Solutions ("loyalty
#    programs for financial institutions, insurance companies")
#    tagged Insurance. Both SELL TO the tagged industry, they
#    aren't IN it. A specific "utility's"/"utilities'" possessive
#    exclusion below closes the Utilities-pattern instance of this
#    (GE Smallworld) - but the SAME GE Smallworld sentence also
#    lists "telecom networks" among what its software monitors,
#    which still incorrectly matches the separate Telecom pattern.
#    Confirmed this is genuinely the same general problem
#    resurfacing through a different pattern, not a new bug - a
#    vendor whose product spans multiple industries will keep
#    leaking into whichever pattern doesn't yet have the same
#    narrow fix. Chasing this pattern-by-pattern has diminishing
#    returns; a general rule risks blocking genuine matches
#    (EqualizeRCM genuinely says "community health providers" and
#    must keep matching Healthcare) - not generalized here until
#    more real examples are gathered.
#
# 2. AMBIGUOUS-NAME SEARCH COLLISIONS (not a code bug) - Zapata
#    AI/Quantum's cached snippet blended in an unrelated real
#    estate developer who happens to share the surname "Zapata"
#    ("Zapata is an active developer... retail mixed-use...
#    redevelopment"), producing a genuine but wrong "Retail"
#    match. This is a search-content ambiguity for a common name,
#    not a keyword-matching bug - no exclusion list fixes this;
#    accepted as a residual risk of using web-search grounding.
# =====================================================

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


# NOTE: an earlier version of this fix also applied
# PROVIDER_EXCLUDE_KEYWORDS to web-search snippet text directly
# (not just the account name). Reverted after real testing showed
# it broke EqualizeRCM Services, a genuine healthcare-technology
# match whose snippet legitimately says "community health
# providers, hospitals" (its CLIENTS, not itself) - the same
# vendor-serves-an-industry ambiguity already documented as an
# open limitation above, just recreated for care-delivery terms.
# The narrower "not-for-profit"/"charity" additions to
# NON_FIT_INSTITUTION_KEYWORDS below already catch CARTI
# Foundation safely without this broader, riskier check.



# =====================================================
# NON-FIT INSTITUTION TYPES (web-search fallback only)
#
# Ported from modules/sales_intelligence_pipeline.py's
# NON_FIT_INSTITUTION_KEYWORDS - that list was built from real
# production misses (Strayer University -> saas_platform,
# Marfrig meatpacking -> retail_platform, PageGroup recruitment
# consultancy -> saas_platform, etc.): the FACT extracted was
# correct, but the institution TYPE doesn't fit any tracked
# business pattern regardless of which keyword matched.
#
# Same failure mode confirmed directly in this session's own
# search-cache spot check: Epstein Becker & Green (a law firm)
# has "health care" right in its own real search snippet
# ("national law firm focused on health care..."), which would
# incorrectly match the healthcare business pattern via the web-
# search fallback if this guard weren't in place. Account NAMES
# essentially never contain this kind of institution-type noise,
# which is why this guard is only needed for the web-search
# fallback path, not the existing name-only matching.
# =====================================================

NON_FIT_INSTITUTION_KEYWORDS = [
    "university", "college", "school district", "law firm",
    "accounting firm", "staffing agency", "meatpacking",
    "meat packing", "engineering firm", "architecture firm",
    "religious organization", "government agency",
    "consulting firm", "consultancy", "consulting services",
    "recruitment consultancy", "recruitment agency",
    "department of defense", "u.s. department", "federal agency",
    "federal government",
    "think tank", "public policy organization",
    "symphony orchestra", "orchestra",
    "performing arts", "design agency", "construction company",
    "real estate investment trust", "landscaping company",
    "landscaping", "mortgage lender", "rating agency",
    "credit rating",
    # "city of" / "county of" catches municipal government
    # entities (City of Austin, TX, matched Utilities) - the
    # existing federal-government entries never covered local
    # government at all.
    "city of", "county of", "municipal government",
]


def is_non_fit_institution(text):
    return any(keyword in text for keyword in NON_FIT_INSTITUTION_KEYWORDS)


# =====================================================
# NONPROFIT / CHARITY ROUTING (web-search fallback only)
#
# Previously, nonprofit/charity signals just fed into the
# generic block above and left the account as blank "Unknown" -
# same label as "we found genuinely no signal at all", which
# loses real information. A rep can't tell "nothing was found"
# apart from "we found a nonprofit and correctly deprioritized
# it" if both look identical. This routes explicitly to a real
# category instead, and uses a broader phrase list than the
# original nonprofit/charity/not-for-profit set - added "legal
# aid", "501(c)(3)", and a few common variants after a real
# stratified audit found KIND (Kids in Need of Defense, a
# children's immigration legal-aid nonprofit) slipping through
# with none of the original phrases present, but "National
# Immigration Legal Aid" in its own search result title.
# =====================================================

NONPROFIT_SIGNAL_KEYWORDS = [
    "nonprofit", "non-profit", "non profit", "charity",
    "charity organization", "not-for-profit", "501(c)(3)", "501c3",
    "nonprofit organization", "non-governmental organization",
    "humanitarian organization", "humanitarian", "relief organization",
    "legal aid", "advocacy organization",
]


def detect_nonprofit_signal(text):
    return any(phrase in text for phrase in NONPROFIT_SIGNAL_KEYWORDS)


# =====================================================
# KEYWORD FALSE-POSITIVE EXCLUSIONS
#
# Some business-pattern keywords are short, common
# substrings that also appear inside unrelated proper
# nouns (e.g. "card" inside "Cardinal", "Wildcard"). An
# explicit exclusion list is more precise than word-boundary
# regex, since most genuine matches are compound words with
# no separator (Cardtronics, Datacard, Cardcash, Trialcard).
#
# Structure: keyword -> list of text substrings that should
# NOT count as a match for that keyword, even though the
# keyword text is technically present.
#
# Expanded 2026-07-29 with entries found specifically via web-
# search snippet text (noisier than account names, so new
# collision types show up that name-only matching never hit):
# "cardiac"/"piccard" for card, "contextmedia" for media,
# "directed energy" for energy - see comments below each.
# =====================================================

KEYWORD_FALSE_POSITIVE_EXCLUSIONS = {
    # "cardiology" was already here (found via account-name
    # matching: American College of Cardiology). "cardiac" and
    # "piccard" added after web-search snippet spot check found
    # real hospital snippets mentioning "Cardiac & Pulmonary
    # Rehab" and an address fragment "1300 Piccard Dr."
    "card": ["cardinal", "wildcard", "cardiology", "cardiac", "piccard"],

    # "media" is a substring of several common, unrelated words
    # and corporate-structuring terms (remedial, mediation,
    # intermediate). "contextmedia" added after web-search
    # snippet spot check found Outcome Health's actual
    # registered legal name is "ContextMedia Health LLC" - a
    # health-tech company, not a media company, purely because
    # its OWN legal name happens to contain "media". "media@"
    # added after a stratified audit found Food For The Poor (a
    # hunger-relief charity) matched purely via its own press-
    # contact email address "media@foodforthepoor.org" - a press-
    # contact email prefix that's common boilerplate across many
    # organizations' sites, same danger class as "careers" below.
    "media": ["remedial", "mediation", "intermediate", "immedia", "contextmedia", "media@"],

    # "utility"/"utilities" third-person-possessive phrasing
    # ("a utility's electric, gas, water networks") is a reliable
    # vendor-describing-their-customer signal, confirmed via GE
    # Smallworld: sells GIS software TO utilities, is not itself
    # one. Genuine utility self-descriptions use first-person
    # framing ("we are an electric utility"), not this possessive
    # third-person form, so this exclusion is narrow and unlikely
    # to block real matches.
    # "utility"/"utilities" third-person-possessive phrasing
    # ("a utility's electric, gas, water networks") is a reliable
    # vendor-describing-their-customer signal, confirmed via GE
    # Smallworld: sells GIS software TO utilities, is not itself
    # one. Genuine utility self-descriptions use first-person
    # framing ("we are an electric utility"), not this possessive
    # third-person form, so this exclusion is narrow and unlikely
    # to block real matches.
    #
    # Applied to ALL keywords in the Utilities pattern
    # (power/energy/electric/utility/utilities), not just
    # "utility" itself - the GE Smallworld sentence matched via
    # "electric" (checked earlier in the pattern's keyword list),
    # not "utility", so excluding only the literal word "utility"
    # was not enough on its own to block this specific sentence.
    "power": ["a utility's", "utilities'"],
    "energy": [
        "department of energy", "national lab", "national laboratory",
        "directed energy", "a utility's", "utilities'",
    ],
    "electric": ["a utility's", "utilities'"],
    "utility": ["a utility's", "utilities'"],
    "utilities": ["a utility's", "utilities'"],

    # "retail" is a substring of "retail banking" - a standard finance
    # term for consumer/personal banking, unrelated to the retail
    # (commerce/stores) industry. Found via a second dataset audit
    # (2026-07-31): GFNorte ("Grupo Financiero Banorte... universal
    # banking products, retail banking products") is a real Mexican
    # bank, not a retailer.
    "retail": ["retail banking"],

    # "merchant" is a substring of "merchant bar" - a real structural-
    # steel product category (a bar shape used in construction),
    # unrelated to FinTech's payment-processing sense of "merchant".
    # Found via the same audit: Gerdau S.A. ("Gerdau manufactures
    # merchant bar, structural steel...") is a real global steel
    # producer, not a payments company.
    "merchant": ["merchant bar"],

    # "api" is a substring of "Capital" - found via real
    # production data (KPS Capital Partners, H.I.G. Capital
    # Management both incorrectly tagged via this collision).
    "api": ["capital"],

    # "health & wellness" is generic corporate-program boilerplate
    # (Positive Promotions, a promotional-products company, listed
    # it as just one of many program categories: "promotional,
    # educational, health & wellness, safety, recognition").
    "health": ["health & wellness", "health and wellness"],

    # "medical, dental" is near-universal employee-benefits
    # boilerplate (ECCO Select, an IT staffing/consulting company,
    # matched purely via "Medical, Dental & Vision Coverage" on
    # its own careers/benefits page) - same danger class as
    # "career" above, arguably worse since "Medical/Dental/Vision"
    # benefits listings appear on nearly every company's site
    # regardless of industry.
    "medical": ["medical, dental", "medical/dental"],

    # "care" is a substring of "career"/"careers" - confirmed via
    # a real 20-account audit of the population that only
    # qualified for the LLM via the web-search fallback: RISD (an
    # art school), IMC (a logistics/drayage company), and JW
    # Player (a video-tech company) were all incorrectly tagged
    # Healthcare Technology purely because their search snippets
    # contained a "Careers" section/page reference (LinkedIn,
    # Built In, and similar company-profile aggregators almost
    # universally have one). This is a more dangerous collision
    # than the others above precisely because "Careers" boilerplate
    # is so common across company snippets generally, not specific
    # to any one industry.
    "care": ["career"],

    # NOTE: "power" is NOT handled via this simple substring-
    # exclusion mechanism - see requires_power_utility_context()
    # below. A snippet spot check found "power" false-positives
    # at nearly 8x the rate of any other tracked keyword (632
    # hits across ~5,000 accounts checked), almost all generic
    # marketing usage ("AI-powered", "powering healthcare data
    # exchange") rather than the utilities industry. That kind
    # of generic-verb usage is too varied for a fixed exclusion
    # list to keep up with - it needs a co-occurrence rule
    # instead, applied only when matching web-search text.
}


def is_false_positive_match(keyword, text):
    exclusions = KEYWORD_FALSE_POSITIVE_EXCLUSIONS.get(keyword, [])
    for excluded_substring in exclusions:
        if excluded_substring in text:
            return True
    return False


# =====================================================
# "POWER" CO-OCCURRENCE RULE (web-search fallback only)
#
# Confirmed via real spot check of the search cache: generic
# marketing phrasing ("AI-powered", "-powered platform",
# "powering intelligent X") vastly outnumbers genuine utility-
# industry mentions of "power" in web-search snippet text.
# Account NAMES don't have this problem (a company literally
# named "X Power Company" is a real signal), which is why this
# rule is scoped to the web-search fallback path only, not the
# existing name-only matching.
#
# Rather than trying to exclude every generic phrasing (an
# unbounded list, unlike the compact substring exclusions
# above), this requires "power" to co-occur with a real,
# specific utility-industry term before it counts as a match.
# =====================================================

POWER_UTILITY_CONTEXT_TERMS = [
    "electric", "utility", "utilities", "grid", "power plant",
    "power company", "power & light", "power and light",
    "transmission", "generation capacity", "power generation",
]


def requires_power_utility_context(keyword, text):
    """
    Returns True if this keyword match should be REJECTED for
    lack of real utility context. Only applies to "power" -
    every other keyword passes through unaffected.
    """
    if keyword != "power":
        return False
    return not any(term in text for term in POWER_UTILITY_CONTEXT_TERMS)


# =====================================================
# "CARE" SIBLING-KEYWORD RULE (web-search fallback only)
#
# Same underlying problem as "power" above: confirmed via a SECOND
# dataset audit (2026-07-31, not just the earlier Enterprise East
# one) that "care" alone keeps colliding with unrelated "___care"
# compounds across totally different industries - "lawn care"
# (Massey Services, pest control), "Client Care" (Cambridge Air
# Solutions, HVAC), "NovaCare Way" (Philadelphia Eagles' own
# facility address, a proper noun). An ever-growing exclusion
# list has the same diminishing-returns problem already
# identified for "power" - English has too many "___care"
# phrases to enumerate them all.
#
# Rather than inventing a new confirming-term list from scratch
# (like POWER_UTILITY_CONTEXT_TERMS), this reuses something
# already available: "health", "medical", "patient", and "care"
# are ALL keywords in the SAME Healthcare Technology pattern.
# Every genuine healthcare match already seen matches "health" or
# "medical" independently and directly - it's specifically the
# false positives that have "care" completely isolated with none
# of its sibling keywords anywhere in the text. Requiring "care"
# to co-occur with one of its own pattern siblings is a more
# targeted, lower-risk signal than an invented term list, and
# needs no separate list to maintain.
# =====================================================

CARE_SIBLING_KEYWORDS = ["health", "medical", "patient"]


def requires_care_sibling_context(keyword, text):
    """
    Returns True if this keyword match should be REJECTED for
    lack of supporting context. Only applies to "care" - every
    other keyword passes through unaffected.
    """
    if keyword != "care":
        return False
    return not any(term in text for term in CARE_SIBLING_KEYWORDS)


# =====================================================
# WORKLOAD STRENGTH LABEL
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
# =====================================================

def apply_workload_profile(result, data):
    profile_key = data.get("workload_profile", "")
    result["workload_profile"] = profile_key

    profile = WORKLOAD_PROFILES.get(profile_key, {})

    result["database_intensity"] = data.get(
        "database_intensity", profile.get("database_intensity", 0)
    )
    result["operational_complexity"] = data.get(
        "operational_complexity", profile.get("operational_complexity", 0)
    )
    result["realtime_requirement"] = data.get(
        "realtime_requirement", profile.get("realtime_requirement", 0)
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

    apply_workload_profile(result, data)

    result["company_signal_score"] = data.get("company_signal_score", 0)
    result["company_signal_reason"] = reason

    return result


def _default_result():
    return {
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
        "company_signal_reason": "",
    }


def _match_business_pattern(text, source_label):
    """
    Pass 3 only - business-pattern keyword matching against
    whatever text is passed in (either account name alone, or
    name + web-search snippet). Returns a fully-populated result
    dict if a pattern matches, or None if nothing matches - the
    caller decides what to do with None (try the next fallback,
    or give up and return Unknown).

    source_label ("account_name" or "web_search") gets tagged
    into company_signal_reason so a match can always be traced
    back to whether it came from the reliable name-only pass or
    the noisier web-search fallback - important for auditing
    newly-elevated accounts, since web-search matching is
    confirmed noisier than name matching.
    """
    for model, data in BUSINESS_PATTERNS.items():
        for keyword in data.get("keywords", []):
            keyword = keyword.lower().strip()

            if keyword not in text:
                continue
            if is_false_positive_match(keyword, text):
                continue
            if requires_power_utility_context(keyword, text):
                continue
            if requires_care_sibling_context(keyword, text):
                continue

            result = _default_result()
            return apply_intelligence(
                result, data,
                f"Business pattern match ({source_label}): {model}"
            )

    return None


# =====================================================
# COMPANY INTELLIGENCE
# =====================================================

def analyze_company(row):
    account_name = str(
        row.get("normalized_account_name", row.get("Account Name", ""))
    ).lower().strip()

    result = _default_result()

    # =====================================================
    # PASS 1 - EXACT COMPANY MATCH
    # PASS 2 - SAFE PARTIAL MATCH
    #
    # Untouched by this restructure - identity matching on the
    # account's own name is a fundamentally different, more
    # reliable signal than business-pattern keyword matching,
    # and web-search snippet text was never a candidate input
    # here. A snippet can mention other companies in passing;
    # the account's own name can't.
    # =====================================================

    for company, data in KNOWN_COMPANIES.items():
        company_key = company.lower().strip()
        if account_name == company_key:
            return apply_intelligence(result, data, "Exact company match")

    for company, data in KNOWN_COMPANIES.items():
        company_key = company.lower().strip()
        if len(company_key) >= 6 and company_key in account_name:
            return apply_intelligence(result, data, "Partial company match")

    # =====================================================
    # PROVIDER EXCLUSION
    #
    # Only reached if no known_companies match was found.
    # =====================================================

    if is_excluded_provider(account_name):
        return result

    # =====================================================
    # PASS 3a - BUSINESS PATTERN MATCH, NAME ALONE
    #
    # Unchanged behavior for every account that already
    # matches today.
    # =====================================================

    match = _match_business_pattern(account_name, "account_name")
    if match is not None:
        return match

    # =====================================================
    # PASS 3b - BUSINESS PATTERN MATCH, NAME + WEB SEARCH
    # FALLBACK
    #
    # Only reached when name-alone found nothing. Free (search
    # already happened and was cached by serper_enrichment_pass.py
    # into "web_search_snippets") - no new LLM cost, no new
    # search cost. Three extra guards apply here that DON'T apply
    # to the name-only pass, all added after real spot checks of
    # cached snippet text surfaced real failure modes:
    #   - is_excluded_provider_in_text(): the ORIGINAL provider
    #     exclusion above only ever checked the account name.
    #     CARTI Foundation ("a not-for-profit cancer center") has
    #     a name that gives no hint of being a care-delivery
    #     organization, but its snippet does - this closes that gap.
    #   - is_non_fit_institution(): blocks law firms, universities,
    #     consultancies, charities, municipal governments, etc.
    #     from matching via incidental keyword mentions in their
    #     own description (Epstein Becker & Green mentioning
    #     "health care" as their legal practice area)
    #   - requires_power_utility_context(): "power" specifically
    #     needs real utility context, not just the bare word,
    #     since generic marketing phrasing ("AI-powered") swamped
    #     genuine utility signal in real snippet data
    # =====================================================

    snippet_text = row.get("web_search_snippets", "")
    if snippet_text and str(snippet_text).strip():
        combined_text = account_name + " " + str(snippet_text).lower()

        if detect_nonprofit_signal(combined_text):
            result["industry"] = "Non-Profit / Charity"
            result["business_model"] = "Non-Profit / Charity"
            result["company_signal_reason"] = "Non-profit/charity organization detected (web_search)"
            return result

        if is_non_fit_institution(combined_text):
            return result

        match = _match_business_pattern(combined_text, "web_search")
        if match is not None:
            return match

    # =====================================================
    # NO MATCH
    # =====================================================

    return result
