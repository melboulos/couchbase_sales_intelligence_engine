# =====================================================
# LLM VALIDATOR
# Couchbase Sales Intelligence Agent
#
# Architecture:
#
# Deterministic Gate
#        |
#        v
# Single LLM Intelligence Generation
#
# Purpose:
#
# LLM does NOT qualify accounts via the deterministic
# pipeline's COI/Tier — those remain fully separate.
#
# LLM creates:
# - seller value hypothesis
# - Couchbase conversation angle
# - technical discovery strategy
# - its OWN independent score (llm_total_score), derived
#   without ever seeing COI/Tier/Database Intensity/
#   Operational Complexity/Real-Time Requirement — used
#   to compare against COI and find gaps in
#   company_patterns.json, not to override or blend with
#   the deterministic score.
#
# =====================================================

import re
import json
import datetime


# =====================================================
# VALIDATION CONTRACT
# =====================================================

REQUIRED_FIELDS = [
    "account_name",
    "engineering_implications",
    "specific_constraint",
    "distributed_solution",
    "technical_risks_to_validate",
    "discovery_progression",
    "missing_information",
    "llm_company_recognized",
    "llm_specific_fact",
    "llm_workload_score",
    "llm_realtime_score",
    "llm_complexity_score",
    "llm_total_score",
    "llm_score_reasoning"
]

LIST_FIELDS = [
    "engineering_implications",
    "technical_risks_to_validate",
    "missing_information"
]

# Fields whose CONTENT must be non-empty, not just present.
# Guards against the field existing as "" or [] and silently
# passing validate_required_fields, which only checks that
# the key exists.
NON_EMPTY_FIELDS = [
    "engineering_implications",
    "specific_constraint",
    "distributed_solution",
    "discovery_progression",
    "llm_score_reasoning",
    "llm_specific_fact"
]

# Sub-score fields and their valid ranges, per the rubric
# in llm_prompt_builder.py's INDEPENDENT SCORE section.
SCORE_RANGES = {
    "llm_workload_score": (0, 40),
    "llm_realtime_score": (0, 30),
    "llm_complexity_score": (0, 30)
}

# Conservative ceilings applied IN CODE when the model sets
# llm_company_recognized to false. The prompt already
# instructs the model to self-limit in this situation, but
# testing showed it doesn't reliably comply (e.g. Trumid
# Financial: llm_company_recognized=false, reasoning said
# "I score conservatively", yet returned 60/100 - well above
# the mandated <30 ceiling). This is a known model-reliability
# limit (Llama 3 70B), not a prompt-wording problem, so it is
# now enforced structurally rather than trusted from the
# model's own arithmetic.
CONSERVATIVE_CEILINGS = {
    "llm_workload_score": 15,
    "llm_realtime_score": 10,
    "llm_complexity_score": 10
}

# A SEPARATE, less restrictive cap from CONSERVATIVE_CEILINGS above.
# CONSERVATIVE_CEILINGS fires when recognition itself isn't verified
# (no real fact at all). This one fires for a different, newly
# confirmed problem: the company IS verified (a real fact exists),
# but the model's own scoring reasoning never actually cites any
# concrete number or scale detail from that fact - it just defaults
# to the same industry-typical-sounding numbers regardless. Confirmed
# via real production sampling across hundreds of accounts: roughly
# half of all verified accounts land on the EXACT SAME combination
# (workload=25, realtime=20, complexity=20, total=65), spanning
# completely unrelated industries - the same underlying disease as
# the narrative genericness problem, just never checked on the
# scoring side until now.
UNGROUNDED_SCORE_CEILINGS = {
    "llm_workload_score": 20,
    "llm_realtime_score": 15,
    "llm_complexity_score": 15
}

# A digit anywhere, or one of these scale-magnitude words, is treated
# as evidence the reasoning is actually grounded in something
# concrete rather than generic industry-typical language. Deliberately
# broad and simple (same discipline as the narrative fix: checking
# for the ACTUAL confirmed pattern, not an exhaustive taxonomy).
SCALE_EVIDENCE_KEYWORDS = [
    "million", "billion", "thousand", "employees", "locations",
    "branches", "offices", "customers", "users", "transactions",
    "founded", "assets", "market cap", "headquartered", "revenue",
]


# Extracts a real, comparable magnitude from dollar figures and
# employee counts found in llm_specific_fact/llm_score_reasoning -
# confirmed working against real production facts: UCB's "$28.2
# billion in assets", Staywell's "501-1,000 employees", Wireless
# Environment's "$24 million revenue" all correctly extracted;
# Cleo's founding year and Comenity's street address correctly
# extract nothing (no false positives from unrelated numbers).
import re

SCALE_DOLLAR_PATTERN = re.compile(r'\$?\s*([\d,]+\.?\d*)\s*(trillion|billion|million|thousand)\b', re.IGNORECASE)
# Catches "a trillion dollars", "over a billion users" - phrasing
# with NO digit before the magnitude word at all. Found via testing:
# Trumid's real fact ("processed over a trillion dollars in trade
# volume") extracted NOTHING under the digit-only pattern above,
# since "a" isn't a digit - this phrasing is common enough that
# missing it meant one of the richest, most obviously "large" facts
# found all session was silently treated as having no magnitude.
SCALE_DOLLAR_BARE_PATTERN = re.compile(r'\b(?:a|an)\s+(trillion|billion|million|thousand)\b', re.IGNORECASE)
SCALE_EMPLOYEE_RANGE_PATTERN = re.compile(r'([\d,]+)\s*-\s*([\d,]+)\+?\s*employees', re.IGNORECASE)
SCALE_EMPLOYEE_SINGLE_PATTERN = re.compile(r'([\d,]+)\+?\s*employees', re.IGNORECASE)

DOLLAR_MULTIPLIERS = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9, 'trillion': 1e12}

# Employee counts are scaled by this factor to make them roughly
# comparable to dollar-figure magnitudes for a single bucketing
# threshold - a deliberately rough heuristic (not a precise
# equivalence), documented as such rather than presented as exact.
EMPLOYEE_TO_DOLLAR_SCALE_FACTOR = 100_000

LARGE_SCALE_THRESHOLD = 1_000_000_000   # ~$1B or equivalent
SMALL_SCALE_THRESHOLD = 10_000_000      # ~$10M or equivalent

LARGE_SCALE_FLOORS = {
    "llm_workload_score": 35,
    "llm_realtime_score": 27,
    "llm_complexity_score": 25,
}
SMALL_SCALE_CEILINGS = {
    "llm_workload_score": 15,
    "llm_realtime_score": 10,
    "llm_complexity_score": 10,
}


# Confirmed real bug (2026-08-11): both dollar-magnitude patterns
# above have an OPTIONAL dollar sign ("\$?"), or in the bare
# pattern's case no dollar signal at all - meaning ANY large number
# followed by "billion"/"million"/etc. was accepted as a dollar
# figure, regardless of what it actually measured. Confirmed via
# real production data: TuneCore's fact ("distributed over 10
# billion TRACKS") triggered the LARGE_SCALE_FLOORS override despite
# containing no dollar figure at all - and the bare pattern's own
# original justifying comment cited "over a billion users" as an
# example to catch, which is the exact same class of error, just
# never noticed at the time. Five unrelated real companies (PVH,
# TuneCore, Hess Midstream, PowerReviews, Tradeweb) were found to
# share an identical llm_total_score of 87 as a direct, confirmed
# result of this bug - not independent model reasoning, a fixed
# code override (35+27+25=87) triggering on non-dollar evidence.
#
# Fix: require a literal "$" OR a real dollar-context word within a
# nearby window, for BOTH patterns - preserves every documented
# genuine case (UCB's "$28.2 billion in assets", Trumid's "a
# trillion dollars in trade volume") while rejecting bare,
# contextless large numbers.
DOLLAR_CONTEXT_WORDS = [
    "dollar", "dollars", "usd", "revenue", "valuation", "valued",
    "assets", "funding", "raised", "market cap", "worth", "sales",
    "trade volume", "trading volume", "aum",
]


def _has_dollar_context(text, start, end, window=40):
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    context = text[context_start:context_end].lower()
    if '$' in context:
        return True
    return any(word in context for word in DOLLAR_CONTEXT_WORDS)


def extract_dollar_magnitude(text):
    """
    Only dollar-figure based magnitude - the ONLY evidence type
    allowed to trigger the LARGE floor, since dollar figures
    (revenue, assets, transaction volume) directly measure the
    thing we're actually estimating (money moving through systems,
    which correlates with real data processing). Employee count
    does not reliably correlate with this - see
    extract_employee_count below.

    Requires a real dollar-sign or dollar-context word near the
    match (see _has_dollar_context) - a bare "10 billion" with no
    dollar signal anywhere nearby is NOT treated as a dollar figure,
    since it could just as easily be a track count, a user count, or
    anything else (confirmed real false positive: TuneCore's "10
    billion tracks").
    """
    if not isinstance(text, str):
        return None

    magnitudes = []
    for match in SCALE_DOLLAR_PATTERN.finditer(text):
        number_str, unit = match.group(1), match.group(2)
        if not _has_dollar_context(text, match.start(), match.end()):
            continue
        try:
            magnitudes.append(float(number_str.replace(',', '')) * DOLLAR_MULTIPLIERS[unit.lower()])
        except ValueError:
            continue

    for match in SCALE_DOLLAR_BARE_PATTERN.finditer(text):
        unit = match.group(1)
        if not _has_dollar_context(text, match.start(), match.end()):
            continue
        magnitudes.append(1.0 * DOLLAR_MULTIPLIERS[unit.lower()])

    return max(magnitudes) if magnitudes else None


def extract_employee_count(text):
    """
    Raw employee count - can ONLY trigger the SMALL ceiling, never
    the LARGE floor. Confirmed via real testing: the US Air Force
    Life Cycle Management Center's fact ("over 26,000 dedicated
    professionals") got floored UP to a high score based on
    headcount alone - but headcount is a poor proxy for database/
    transaction workload outside businesses where headcount
    directly correlates with operational volume (a distributor's
    2,300 employees genuinely does suggest real logistics
    complexity; a military command's 26,000 personnel says nothing
    reliable about its technical footprint). A LOW headcount
    plausibly does suggest a genuinely small operation regardless of
    industry, which is why it's kept for the small-side check only.

    Uses the MAX count found (not the first or an average) so a
    company mentioned with multiple different headcount figures
    isn't mistakenly called "small" based on a partial/team-level
    number when the overall organization is larger.
    """
    if not isinstance(text, str):
        return None

    counts = []
    has_range = bool(SCALE_EMPLOYEE_RANGE_PATTERN.search(text))
    for low, high in SCALE_EMPLOYEE_RANGE_PATTERN.findall(text):
        try:
            counts.append((float(low.replace(',', '')) + float(high.replace(',', ''))) / 2)
        except ValueError:
            continue

    if not has_range:
        for count in SCALE_EMPLOYEE_SINGLE_PATTERN.findall(text):
            try:
                counts.append(float(count.replace(',', '')))
            except ValueError:
                continue

    return max(counts) if counts else None


def determine_if_default_score(result):
    """
    Final, authoritative call on whether this score reflects real
    differentiation or is an honest default - so a rep sees a clear
    label rather than every score looking equally confident. Per the
    user's own framing: if there isn't enough data to genuinely
    score an account, that should be a visible, honest label, not a
    silently-defaulted number indistinguishable from a real one.

    Called LAST in the chain, after enforce_company_recognition_cap,
    detect_ungrounded_score, and apply_magnitude_based_score_adjustment
    have all had a chance to run, so it reflects the final state of
    all three checks.
    """
    verified = result.get("llm_recognition_verified") is True
    magnitude_found = result.get("llm_magnitude_bucket") in ("large", "small", "medium")
    ungrounded = result.get("llm_score_ungrounded") is True

    if not verified:
        result["llm_score_is_default"] = True
    elif magnitude_found:
        result["llm_score_is_default"] = False
    elif ungrounded:
        result["llm_score_is_default"] = True
    else:
        result["llm_score_is_default"] = False

    return result


SMALL_EMPLOYEE_THRESHOLD = 100  # a rough heuristic, documented as such


def apply_magnitude_based_score_adjustment(result):
    """
    Goes further than detect_ungrounded_score (which only checks
    whether ANY evidence is present). This extracts the ACTUAL
    magnitude from real, search-derived facts and FORCES the score
    to reflect it - a floor for confirmed large scale (dollar
    figures only), a ceiling for confirmed small scale (dollar
    figures OR a low employee count) - regardless of what number the
    model itself reported. Only applies to verified accounts; if no
    magnitude can be extracted, this is a no-op (the ungrounded-
    score check above already handles the zero-evidence case).
    """
    if result.get("llm_recognition_verified") is not True:
        result["llm_magnitude_bucket"] = None
        return result

    combined_text = (
        str(result.get("llm_specific_fact", "")) + " " +
        str(result.get("llm_score_reasoning", ""))
    )
    dollar_magnitude = extract_dollar_magnitude(combined_text)
    employee_count = extract_employee_count(combined_text)

    if dollar_magnitude is not None and dollar_magnitude >= LARGE_SCALE_THRESHOLD:
        result["llm_magnitude_bucket"] = "large"
        for field, floor in LARGE_SCALE_FLOORS.items():
            if result.get(field, 0) < floor:
                result[field] = floor
    elif dollar_magnitude is not None and dollar_magnitude < SMALL_SCALE_THRESHOLD:
        result["llm_magnitude_bucket"] = "small"
        for field, ceiling in SMALL_SCALE_CEILINGS.items():
            if result.get(field, 0) > ceiling:
                result[field] = ceiling
    elif employee_count is not None and employee_count < SMALL_EMPLOYEE_THRESHOLD:
        result["llm_magnitude_bucket"] = "small"
        for field, ceiling in SMALL_SCALE_CEILINGS.items():
            if result.get(field, 0) > ceiling:
                result[field] = ceiling
    elif dollar_magnitude is not None or employee_count is not None:
        result["llm_magnitude_bucket"] = "medium"
    else:
        result["llm_magnitude_bucket"] = None

    result["llm_total_score"] = (
        result.get("llm_workload_score", 0)
        + result.get("llm_realtime_score", 0)
        + result.get("llm_complexity_score", 0)
    )

    return result


def detect_ungrounded_score(result):
    """
    Only applies to VERIFIED companies (a real fact already passed
    validate_recognition_evidence) - enforce_company_recognition_cap
    already handles the unverified case. This catches a company that
    IS genuinely recognized, but whose scoring reasoning never
    actually cites the scale/evidence that would justify a
    mid-to-high score, landing on the same default numbers as
    everything else regardless.
    """
    if result.get("llm_recognition_verified") is not True:
        result["llm_score_ungrounded"] = False
        return result

    combined_text = normalize_text(
        str(result.get("llm_score_reasoning", "")) + " " +
        str(result.get("llm_specific_fact", ""))
    )

    has_digit = any(char.isdigit() for char in combined_text)
    has_scale_keyword = any(keyword in combined_text for keyword in SCALE_EVIDENCE_KEYWORDS)
    is_grounded = has_digit or has_scale_keyword

    result["llm_score_ungrounded"] = not is_grounded

    if is_grounded:
        return result

    capped_any = False
    for field, ceiling in UNGROUNDED_SCORE_CEILINGS.items():
        value = result.get(field, 0)
        if isinstance(value, (int, float)) and value > ceiling:
            result[field] = ceiling
            capped_any = True

    if capped_any:
        result["llm_total_score"] = (
            result.get("llm_workload_score", 0)
            + result.get("llm_realtime_score", 0)
            + result.get("llm_complexity_score", 0)
        )
        result["llm_score_reasoning"] = (
            str(result.get("llm_score_reasoning", "")) +
            " [CODE-ENFORCED CAP: recognition was verified but the "
            "scoring reasoning never cited any concrete number or "
            "scale detail (no digit, no scale-magnitude keyword) - "
            "clamped in code rather than trusted as reported, since "
            "this exact gap produced a confirmed 50%+ convergence "
            "rate onto the same default score across unrelated "
            "companies.]"
        )

    return result

# Phrases that indicate llm_specific_fact is really just the
# industry category restated, not a genuine fact about the
# named company. Testing showed even "recognized" accounts
# (e.g. Netspend, United Community Bank) produce reasoning
# that never goes beyond "as a FinTech/banking company,
# X typically has..." - this list catches that pattern so
# llm_company_recognized can't be trusted at face value.
GENERIC_FACT_PHRASES = [
    "typically",
    "generally",
    "usually",
    "commonly",
    "likely",
    "as a fintech company",
    "as a financial services company",
    "as a healthcare company",
    "as a technology company",
    "this type of business",
    "this type of company",
    "companies like this",
    "companies in this industry",
    "industry standard",
    "based on their industry",
    "based on the industry",
    "based on my knowledge of",
    "none - not specifically recognized"
]

MIN_FACT_LENGTH = 15


# =====================================================
# UNSUPPORTED CLAIMS
# =====================================================

FORBIDDEN_CLAIMS = [
    "customer uses oracle",
    "customer uses mongodb",
    "customer uses postgresql",
    "customer uses mysql",
    "confirmed migration",
    "confirmed replacement",
    "customer is migrating",
    "will replace",
    "replacing oracle",
    "replacing mongodb"
]


# =====================================================
# HELPERS
# =====================================================

def normalize_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).lower()).strip()


def normalize_for_identity_match(value):
    """
    Like normalize_text, but also strips trailing periods/commas.
    Confirmed via real production data: the model consistently
    drops the trailing period after abbreviations when restating
    an account name (e.g. "Aegis Therapies, Inc." -> "aegis
    therapies, inc", "Sandals Resorts International Limited." ->
    "sandals resorts international limited"). That's a spurious
    formatting difference, not a genuine identity mismatch, and
    was causing real, correctly-identified accounts to be
    rejected and lose their LLM intelligence entirely.
    """
    text = normalize_text(value)
    return re.sub(r"[.,]+$", "", text).strip()


# =====================================================
# HALLUCINATION CHECK
# =====================================================

def detect_hallucinations(text):
    violations = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in text:
            violations.append(claim)
    return violations


# =====================================================
# REQUIRED FIELD VALIDATION
# =====================================================

def validate_required_fields(result):
    missing = [
        field
        for field in REQUIRED_FIELDS
        if field not in result
    ]
    if missing:
        raise ValueError(f"Missing fields: {missing}")


# =====================================================
# NON-EMPTY CONTENT VALIDATION
#
# A field can be present but empty ("" or []), which
# validate_required_fields alone will not catch.
# =====================================================

def validate_non_empty_fields(result):
    empty = [
        field
        for field in NON_EMPTY_FIELDS
        if not result.get(field)
    ]
    if empty:
        raise ValueError(f"Empty required content: {empty}")


# =====================================================
# INDEPENDENT SCORE VALIDATION
#
# Checks each sub-score is a number within its rubric
# range, AND that they actually sum to llm_total_score —
# catching a model that returns internally inconsistent
# numbers (e.g. sub-scores that don't add up), not just
# fields that are merely present.
# =====================================================

def validate_independent_score(result):
    violations = []

    recognized = result.get("llm_company_recognized")
    if not isinstance(recognized, bool):
        violations.append(
            f"llm_company_recognized is not a boolean: {recognized!r}"
        )

    for field, (low, high) in SCORE_RANGES.items():
        value = result.get(field)

        if not isinstance(value, (int, float)):
            violations.append(f"{field} is not numeric: {value!r}")
            continue

        if value < low or value > high:
            violations.append(f"{field} out of range [{low}-{high}]: {value}")

    if violations:
        raise ValueError(f"Independent score validation failed: {violations}")

    workload = result.get("llm_workload_score", 0)
    realtime = result.get("llm_realtime_score", 0)
    complexity = result.get("llm_complexity_score", 0)
    total = result.get("llm_total_score", 0)

    expected_total = workload + realtime + complexity

    if not isinstance(total, (int, float)):
        raise ValueError(f"llm_total_score is not numeric: {total!r}")

    if abs(total - expected_total) > 0.5:
        raise ValueError(
            f"llm_total_score ({total}) does not match sum of sub-scores "
            f"({expected_total})"
        )


# =====================================================
# CODE-ENFORCED RECOGNITION CAP
#
# Runs AFTER validate_independent_score (so we only clamp
# values that are already structurally valid - in range and
# internally consistent). If llm_company_recognized is False,
# any sub-score above its conservative ceiling gets clamped
# down and llm_total_score is recomputed to match, since the
# model was confirmed to ignore the prompt's own instruction
# to self-limit in this case.
#
# Always sets result["llm_score_capped"] (True/False) so it's
# visible in the output which rows were code-corrected, rather
# than silently rewriting the model's number with no trace.
# =====================================================

# =====================================================
# RECOGNITION EVIDENCE CHECK
#
# llm_company_recognized is the model's own self-report,
# and testing showed it isn't trustworthy on its own -
# "recognized" accounts (Netspend, United Community Bank)
# gave reasoning that never went beyond restating the
# industry category ("as a FinTech company...", "based on
# my knowledge of banking systems..."), yet still claimed
# recognized=true. This function checks the actual evidence
# (llm_specific_fact) rather than trusting the verdict, and
# sets llm_recognition_verified - which is what the cap
# enforcement below actually keys off, NOT the raw
# llm_company_recognized field.
# =====================================================

def validate_recognition_evidence(result):
    claimed_recognized = bool(result.get("llm_company_recognized"))
    fact = normalize_text(result.get("llm_specific_fact", ""))

    too_short = len(fact) < MIN_FACT_LENGTH
    is_generic = any(phrase in fact for phrase in GENERIC_FACT_PHRASES)

    verified = claimed_recognized and fact and not too_short and not is_generic

    result["llm_recognition_verified"] = verified

    if claimed_recognized and not verified:
        result["llm_score_reasoning"] = (
            str(result.get("llm_score_reasoning", "")) +
            " [RECOGNITION NOT VERIFIED: llm_company_recognized was "
            "true but llm_specific_fact did not contain a genuine, "
            "specific, checkable claim about this named company - "
            "treated as unrecognized for scoring purposes.]"
        )

    return result


# =====================================================
# CLASSIFICATION VALIDATION (classification pre-pass)
#
# Same fact-verification discipline as
# validate_recognition_evidence above, reusing the same
# stoplist/length check (single source of truth - not
# duplicated), applied to the narrower classification-only
# prompt in classification_prompt_builder.py. Also checks the
# claimed workload_profile is one of the real, valid keys -
# a model that returns a made-up category string is treated
# the same as "none".
# =====================================================

# Facts phrased in the past tense about corporate existence mean
# the company doesn't operate independently anymore - not a live
# prospect. Found in production: "Tier 3, Inc." classified as an
# active telecom_platform account, but the model's own fact said
# "WAS a cloud computing and colocation company that WAS acquired
# by CenturyLink in 2014."
# STRONG patterns: genuinely sufficient alone to indicate the
# company is defunct/dissolved, not just acquired.
DEFUNCT_STRONG_PATTERNS = [
    "no longer exists", "no longer operates", "ceased operations",
    "was dissolved", "went out of business", "filed for bankruptcy",
    "shut down", "concluded its business operations",
    "concluded operations", "has closed",
]

# AMBIGUOUS patterns: acquisition alone does NOT mean defunct - most
# acquired companies keep operating as active subsidiaries (Alexion
# under AstraZeneca, Zup Innovation under Itau Unibanco, both
# confirmed via real testing to be legitimate live accounts, not
# defunct). Only treated as a defunct signal when it co-occurs with
# PAST_TENSE_SELF_PATTERNS below - i.e. the company describes its
# OWN nature in the past tense ("Tier 3, Inc. WAS a cloud computing
# company that was acquired by CenturyLink" - self-description in
# past tense, unlike "Alexion IS a biopharmaceutical company... that
# was acquired by AstraZeneca" - self-description in present tense).
DEFUNCT_ACQUISITION_PATTERNS = [
    "was acquired by", "was later acquired", "was subsequently acquired",
    "is now part of", "was merged into", "prior to its acquisition",
]

PAST_TENSE_SELF_PATTERNS = [
    "was a ", "was an ", "used to be", "was renamed", "was rebranded",
]

# Institution TYPES that are essentially never a fit for any of our
# tracked workload categories, regardless of which one the model
# picked. Found in production: Strayer University (a real, accurate
# fact) got forced into saas_platform; Marfrig Global Foods
# (meatpacking, accurately identified) got forced into
# retail_platform. The fact was right, the category was wrong.
# Broadened twice more this session as new phrasing patterns were
# found: CLEAResult Consulting -> utilities_platform, CRA
# International -> saas_platform, PageGroup ("recruitment
# consultancy") -> saas_platform, Defense Contract Management Agency
# -> logistics_platform; then Brookings Institution/Boston Symphony
# (nonprofit/policy/arts orgs) -> media_entertainment_platform,
# Mad*Pow (design agency) -> saas_platform, Burns & McDonnell
# (engineering/architecture/construction) -> utilities_platform,
# Segal Group (benefits/HR consulting) -> insurance_platform,
# BrightView (landscaping) / Duke Realty (REIT) -> logistics_platform.
NON_FIT_INSTITUTION_KEYWORDS = [
    "university", "college", "school district", "law firm",
    "accounting firm", "staffing agency", "meatpacking",
    "meat packing", "engineering firm", "architecture firm",
    "religious organization", "government agency",
    "consulting firm", "consultancy", "consulting services",
    "recruitment consultancy", "recruitment agency",
    "department of defense", "u.s. department", "federal agency",
    "federal government",
    "think tank", "public policy organization", "nonprofit",
    "non-profit", "symphony orchestra", "orchestra",
    "performing arts", "design agency", "construction company",
    "real estate investment trust", "landscaping company",
    "landscaping", "mortgage lender", "rating agency",
    "credit rating",
]

# Category-specific mismatches: a description clearly indicating a
# physical-goods manufacturer doesn't fit a software category (3D
# Systems, a 3D printer manufacturer, was forced into saas_platform)
# and is questionable for a pure retail category (Corsicana Mattress,
# a mattress manufacturer, was forced into retail_platform - it
# makes the product, it doesn't operate a retail storefront/platform).
# Also: Accudyne Industries (industrial valves/pressure regulators)
# forced into pharma_device_platform, despite having nothing to do
# with pharma or medical devices - "device" in the category name
# apparently pattern-matched against unrelated industrial equipment.
CATEGORY_SPECIFIC_MISMATCH_KEYWORDS = {
    "saas_platform": [
        "manufacturer", "manufactures", "produces machines",
        "hardware company", "physical product", "3d printing",
    ],
    "retail_platform": [
        "manufacturer", "manufactures",
    ],
    "pharma_device_platform": [
        "industrial equipment", "flow control", "pressure regulators",
        "valves", "industrial infrastructure",
    ],
}


def validate_classification(result, valid_profiles):
    claimed_recognized = bool(result.get("llm_company_recognized"))
    fact = normalize_text(result.get("llm_specific_fact", ""))

    too_short = len(fact) < MIN_FACT_LENGTH
    is_generic = any(phrase in fact for phrase in GENERIC_FACT_PHRASES)

    verified = claimed_recognized and fact and not too_short and not is_generic

    result["llm_recognition_verified"] = verified

    has_strong_defunct = any(pattern in fact for pattern in DEFUNCT_STRONG_PATTERNS)
    has_acquisition = any(pattern in fact for pattern in DEFUNCT_ACQUISITION_PATTERNS)
    has_past_tense_self = any(pattern in fact for pattern in PAST_TENSE_SELF_PATTERNS)
    is_defunct = has_strong_defunct or (has_acquisition and has_past_tense_self)
    result["llm_defunct_flag"] = is_defunct

    is_non_fit_institution = any(
        keyword in fact for keyword in NON_FIT_INSTITUTION_KEYWORDS
    )

    profile = result.get("llm_workload_profile", "none")

    category_mismatch_keywords = CATEGORY_SPECIFIC_MISMATCH_KEYWORDS.get(profile, [])
    is_category_mismatch = any(keyword in fact for keyword in category_mismatch_keywords)

    if not verified or profile not in valid_profiles or is_defunct or \
       is_non_fit_institution or is_category_mismatch:
        result["llm_workload_profile"] = "none"

    # Scale tier only means anything if a real category was assigned
    # and recognition is verified. Any other value (missing, typo,
    # or attached to a "none" classification) safely defaults to
    # "typical" - i.e. no adjustment, same as the category default.
    scale_tier = result.get("llm_scale_tier", "typical")
    if not verified or result["llm_workload_profile"] == "none" or \
       scale_tier not in ("above_typical", "below_typical", "typical"):
        scale_tier = "typical"
    result["llm_scale_tier"] = scale_tier

    return result


# =====================================================
# SCALE-ADJUSTED RATINGS (classification pre-pass)
#
# Applies a small, code-bounded nudge to the category's
# default database_intensity/operational_complexity/
# realtime_requirement, based on the model's llm_scale_tier
# judgment. Same discipline as enforce_company_recognition_cap
# above: the LLM makes a narrow, discrete choice
# (above/below/typical), NOT raw numbers - testing all session
# has shown the model cannot be trusted with unconstrained
# numeric scoring, but a bounded +/-1 nudge, only applied when
# recognition is verified, is a much smaller and safer trust
# surface than the full independent score ever was.
# =====================================================

SCALE_ADJUSTMENT = {
    "above_typical": 1,
    "typical": 0,
    "below_typical": -1,
}

RATING_MIN = 1
RATING_MAX = 5


def apply_scale_adjustment(base_value, scale_tier):
    adjustment = SCALE_ADJUSTMENT.get(scale_tier, 0)
    return max(RATING_MIN, min(RATING_MAX, base_value + adjustment))


# =====================================================
# CODE-ENFORCED RECOGNITION CAP
#
# Runs AFTER validate_independent_score (so we only clamp
# values that are already structurally valid - in range and
# internally consistent) AND after validate_recognition_evidence
# (so the cap keys off llm_recognition_verified - actual checked
# evidence - not the model's raw, unverified self-report). Any
# sub-score above its conservative ceiling gets clamped down and
# llm_total_score is recomputed to match.
#
# Always sets result["llm_score_capped"] (True/False) so it's
# visible in the output which rows were code-corrected, rather
# than silently rewriting the model's number with no trace.
# =====================================================

def enforce_company_recognition_cap(result):
    if result.get("llm_recognition_verified") is True:
        result["llm_score_capped"] = False
        return result

    capped_any = False

    for field, ceiling in CONSERVATIVE_CEILINGS.items():
        value = result.get(field, 0)
        if isinstance(value, (int, float)) and value > ceiling:
            result[field] = ceiling
            capped_any = True

    if capped_any:
        result["llm_total_score"] = (
            result.get("llm_workload_score", 0)
            + result.get("llm_realtime_score", 0)
            + result.get("llm_complexity_score", 0)
        )
        result["llm_score_reasoning"] = (
            str(result.get("llm_score_reasoning", "")) +
            " [CODE-ENFORCED CAP: llm_recognition_verified was false "
            "(company not genuinely recognized with specific evidence) "
            "but the model's own sub-scores exceeded the conservative "
            "ceiling (workload<=15/realtime<=10/complexity<=10); "
            "clamped in code rather than trusted as reported.]"
        )
        result["llm_score_capped"] = True
    else:
        result["llm_score_capped"] = False

    return result


# =====================================================
# LIST VALIDATION
# =====================================================

def validate_lists(result):
    for field in LIST_FIELDS:
        if not isinstance(result.get(field), list):
            raise ValueError(f"{field} must be list")


# =====================================================
# DISCOVERY VALIDATION
# =====================================================

def validate_discovery_progression(result):
    progression = result.get("discovery_progression")
    if not isinstance(progression, list):
        raise ValueError("discovery_progression must be list")

    for phase in progression:
        if not isinstance(phase, dict):
            raise ValueError("discovery_progression entries must be objects")

        required = ["phase", "objective", "questions"]
        for field in required:
            if field not in phase:
                raise ValueError(f"Missing discovery field: {field}")

        if not isinstance(phase["questions"], list):
            raise ValueError("Discovery questions must be list")


# =====================================================
# ACCOUNT IDENTITY VALIDATION
# =====================================================

def validate_account_identity(result, account_name):
    returned = normalize_for_identity_match(result.get("account_name", ""))
    expected = normalize_for_identity_match(account_name)

    if returned != expected:
        raise ValueError(
            f"Account mismatch. "
            f"Expected {account_name}, "
            f"Returned {returned}"
        )


# =====================================================
# TECHNICAL QUALITY VALIDATION
# =====================================================

def validate_evidence_quality(result):
    forbidden = [
        # "enterprise" removed - confirmed via real production
        # data that it's a single common word with legitimate
        # technical uses ("enterprise architecture", "enterprise-
        # grade consistency"), unlike the multi-word phrases
        # below which are reliable generic-filler signals. It was
        # incorrectly rejecting real, valid intelligence for
        # genuinely large accounts (NSA, Northrop Grumman).
        "large company",
        "market leader",
        "industry leader",
        "company size",
        "cloud adoption",
        "ai initiative",
        "growth opportunity"
    ]

    evidence = normalize_text(
        " ".join(result.get("engineering_implications", []))
    )

    violations = []
    for item in forbidden:
        if item in evidence:
            violations.append(item)

    if violations:
        raise ValueError(f"Invalid technical evidence: {violations}")


# =====================================================
# VALUE VALIDATION
#
# Prevent empty seller language
#
# Includes both base and gerund/variant forms of weak
# phrases, since the LLM will vary verb tense (e.g.
# "understand their needs" vs "understanding their
# needs") and a literal substring match on only one
# form allows the other to silently pass.
# =====================================================

def validate_llm_value(result):
    weak_phrases = [
        "learn more about",
        "explore opportunities",
        "understand their needs",
        "understanding their needs",
        "explore their needs",
        "exploring their needs"
    ]

    text = normalize_text(json.dumps(result))

    violations = []
    for phrase in weak_phrases:
        if phrase in text:
            violations.append(phrase)

    if violations:
        raise ValueError(f"Low-value generic output: {violations}")


# =====================================================
# COMPLETE VALIDATION
# =====================================================

def apply_narrative_caveat(result):
    """
    enforce_company_recognition_cap already gates the SCORE on
    llm_recognition_verified - but engineering_implications and
    couchbase_point_of_view are written from the upstream Industry/
    Business Model/Workloads labels regardless of whether the model
    actually recognizes the specific company. Found in production:
    Simply Self Storage was correctly marked
    llm_recognition_verified=False (score capped to 10), but its
    engineering_implications still confidently described "the
    logistics and transportation industry" - the assigned category
    was treated as fact in the narrative even though the SAME
    response admitted it doesn't know the company. This adds a
    visible, code-enforced caveat whenever recognition isn't
    verified, so a seller reading the narrative knows it's built on
    an assigned category, not confirmed knowledge of this specific
    company.
    """
    if result.get("llm_recognition_verified") is True:
        result["llm_narrative_caveated"] = False
        return result

    CAVEAT = (
        "NOTE: this account was not specifically recognized - the "
        "analysis below is based on its assigned category, not "
        "confirmed knowledge of this specific company. Verify "
        "before using in outreach."
    )

    implications = result.get("engineering_implications", [])
    if isinstance(implications, list):
        result["engineering_implications"] = [CAVEAT] + implications
    else:
        result["engineering_implications"] = [CAVEAT, str(implications)]

    couchbase_pov = result.get("couchbase_point_of_view", "")
    result["couchbase_point_of_view"] = f"{CAVEAT} {couchbase_pov}"

    result["llm_narrative_caveated"] = True

    return result


# Confirmed via direct quantification of 2,532 real, genuinely
# different verified accounts: 81.5% of all Couchbase POV openings
# share one of just 15 templates, and every single one of those 15
# starts with the literal words "a distributed database" - only the
# adjective that follows varies (availability, scalability,
# consistency, flexible data model, throughput, etc.). Banning
# individual adjective combinations is a losing game (confirmed:
# an earlier version of this check only banned 2 specific
# combinations and would have caught ~41% of the real problem,
# missing "scalability"/"consistency"/"flexible data model" variants
# entirely) - checking the actual shared opening STRUCTURE catches
# the real pattern regardless of which adjective is used.
GENERIC_NARRATIVE_PREFIX = "a distributed database"


def detect_generic_narrative(result):
    pov = normalize_text(result.get("couchbase_point_of_view", ""))
    is_generic = pov.startswith(GENERIC_NARRATIVE_PREFIX)
    result["llm_narrative_generic"] = is_generic
    return result


# Confirmed via real production output: a "GOOD example" sentence
# written INTO the prompt to demonstrate a pattern got copied
# nearly verbatim onto United Community Bank, presented as if it
# were real analysis of that specific bank - a different, more
# dangerous failure than generic templating, since it's confidently
# fabricated content that LOOKS specific. The example sentence has
# since been removed from the prompt, but this tripwire stays as a
# permanent check in case this exact text resurfaces (a cached
# prompt version, model memory, etc.) and as a template for
# catching prompt-leakage generally, not just this one instance.
LEAKED_EXAMPLE_PHRASES = [
    "sustaining sub-second fraud-check latency while a single write",
    "loyalty points, and transaction history simultaneously",
]


def detect_prompt_leakage(result):
    pov = normalize_text(result.get("couchbase_point_of_view", ""))
    is_leaked = any(phrase in pov for phrase in LEAKED_EXAMPLE_PHRASES)
    result["llm_prompt_leakage_detected"] = is_leaked
    return result


# The old prompt HARDCODED these exact phase objective phrases as
# literal text for the model to echo - this guaranteed identical
# discovery_progression output on every account regardless of
# industry. Now banned in the prompt; this checks whether the ban
# actually took effect, or whether the model still reaches for the
# same phrasing out of habit.
GENERIC_DISCOVERY_PHRASES = [
    "understand architecture",
    "understand workload characteristics",
    "understand operational constraints",
    "determine whether operational database architecture",
]


def detect_generic_discovery(result):
    progression = result.get("discovery_progression", [])

    if not isinstance(progression, list):
        result["llm_discovery_generic"] = False
        return result

    generic_phase_count = 0
    for phase in progression:
        if isinstance(phase, dict):
            objective = normalize_text(phase.get("objective", ""))
            if any(phrase in objective for phrase in GENERIC_DISCOVERY_PHRASES):
                generic_phase_count += 1

    # Flag if HALF or more of the phases still use the old generic
    # objectives - a single coincidental match isn't proof of
    # templating, but most/all of them matching is.
    result["llm_discovery_generic"] = (
        len(progression) > 0 and generic_phase_count >= len(progression) / 2
    )
    return result


# Schema-level fix, not just an instruction: the model is now
# required to return TWO separate fields instead of one free-text
# couchbase_point_of_view. This exists because two prior fixes
# (banning specific phrases, then banning the opening structure)
# were both followed literally while the model simply relocated the
# same product-first pattern a few words later - confirmed via real
# retest (Netspend/UCB: "Handling the volume...requires a
# distributed database that can scale horizontally", product name
# introduced almost immediately despite technically not being the
# first word). Splitting into two REQUIRED fields lets code check
# the ENTIRE specific_constraint sentence for product-name mentions,
# not just whether it happens to start that way - much harder to
# route around than a prefix check.
CONSTRAINT_BANNED_WORDS = [
    "database", "distributed", "couchbase", "data layer",
    "data platform",
]


def build_couchbase_pov_from_parts(result):
    constraint = normalize_text(result.get("specific_constraint", ""))
    solution = result.get("distributed_solution", "")

    # Code-level fallback, not just a prompt instruction - confirmed
    # necessary via real data: 162 real accounts (4.6% of a full
    # production run) left this field completely empty, discarding
    # the ENTIRE account's validation over one missing sentence.
    # Same lesson as everywhere else this session: don't trust an
    # instruction alone to fix a behavior - give it a real,
    # code-enforced backstop too.
    if not solution or not str(solution).strip():
        solution = (
            "Insufficient information to connect a specific "
            "distributed-database benefit to this constraint."
        )
        result["llm_distributed_solution_defaulted"] = True
    else:
        result["llm_distributed_solution_defaulted"] = False

    result["distributed_solution"] = solution

    violated = any(word in constraint for word in CONSTRAINT_BANNED_WORDS)
    result["llm_constraint_violated"] = violated

    result["couchbase_point_of_view"] = (
        f"{result.get('specific_constraint', '')} {solution}"
    ).strip()

    return result


def detect_defunct_company(result):
    """
    The classification pre-pass has had defunct-company detection
    since early this session (DEFUNCT_STRONG_PATTERNS etc., built for
    the "Tier 3, Inc." bug). This full-intelligence path had no
    equivalent check at all - an account that already has a
    workload_profile assigned skips the classification pre-pass
    entirely and goes straight here. Confirmed real gap via
    production data: Sqrrl Data LLC ("was an American company...
    acquired by Amazon", genuinely defunct, confirmed via real web
    search earlier this session) scored 65/100 and was never flagged
    as anything but a normal live prospect. Consulate Health Care
    ("officially concluded its business operations as of May 31,
    2025") got a self-corrected LOW score from the model's own
    reasoning, but still no code-level flag or visible warning -
    relying on the model to notice and self-correct every time is
    not a real safeguard.

    Same detection logic as validate_classification() - reuses the
    same constants, not a duplicate stoplist. Applies the SAME code-
    enforced discipline as enforce_company_recognition_cap(): don't
    trust the model to self-correct, force the score down and make
    the warning visible regardless of what the model's own reasoning
    happened to do this time.
    """
    fact = normalize_text(result.get("llm_specific_fact", ""))

    has_strong = any(pattern in fact for pattern in DEFUNCT_STRONG_PATTERNS)
    has_acquisition = any(pattern in fact for pattern in DEFUNCT_ACQUISITION_PATTERNS)
    has_past_tense_self = any(pattern in fact for pattern in PAST_TENSE_SELF_PATTERNS)
    is_defunct = has_strong or (has_acquisition and has_past_tense_self)

    result["llm_defunct_detected"] = is_defunct

    if not is_defunct:
        return result

    # Force the score down regardless of what the model computed -
    # a defunct company is not a live prospect, whatever scale or
    # complexity language appears in the narrative.
    result["llm_workload_score"] = min(result.get("llm_workload_score", 0), 5)
    result["llm_realtime_score"] = min(result.get("llm_realtime_score", 0), 5)
    result["llm_complexity_score"] = min(result.get("llm_complexity_score", 0), 5)
    result["llm_total_score"] = (
        result["llm_workload_score"] + result["llm_realtime_score"] + result["llm_complexity_score"]
    )

    DEFUNCT_CAVEAT = (
        "NOTE: this account's own stated fact indicates the company "
        "may no longer operate as an independent, active entity "
        "(acquired/dissolved/concluded operations). Verify current "
        "status before treating this as a live prospect."
    )
    implications = result.get("engineering_implications", [])
    if isinstance(implications, list):
        result["engineering_implications"] = [DEFUNCT_CAVEAT] + implications
    result["couchbase_point_of_view"] = f"{DEFUNCT_CAVEAT} {result.get('couchbase_point_of_view', '')}"
    result["llm_narrative_caveated"] = True

    return result


def validate_llm_output(result, raw_text, account_name):
    validate_required_fields(result)
    build_couchbase_pov_from_parts(result)
    validate_non_empty_fields(result)
    validate_independent_score(result)
    validate_recognition_evidence(result)
    enforce_company_recognition_cap(result)
    detect_ungrounded_score(result)
    apply_magnitude_based_score_adjustment(result)
    determine_if_default_score(result)
    apply_narrative_caveat(result)
    detect_generic_narrative(result)
    detect_generic_discovery(result)
    detect_prompt_leakage(result)
    detect_defunct_company(result)

    if result.get("llm_prompt_leakage_detected"):
        # Confirmed-fabricated content is worse than the
        # unverified-recognition case apply_narrative_caveat
        # already handles - force the same visible warning even if
        # recognition was otherwise verified, since UCB's case
        # showed this can happen to a genuinely recognized account.
        LEAK_CAVEAT = (
            "NOTE: this response was found to contain text copied "
            "from internal prompt instructions rather than genuine "
            "analysis of this account. Do not use as-is - request "
            "regeneration or write manually."
        )
        implications = result.get("engineering_implications", [])
        if isinstance(implications, list):
            result["engineering_implications"] = [LEAK_CAVEAT] + implications
        result["couchbase_point_of_view"] = f"{LEAK_CAVEAT} {result.get('couchbase_point_of_view', '')}"
        result["llm_narrative_caveated"] = True

    combined_text = normalize_text(
        json.dumps(result) + str(raw_text)
    )

    violations = detect_hallucinations(combined_text)
    if violations:
        raise ValueError(f"Hallucination detected: {violations}")

    validate_lists(result)
    validate_discovery_progression(result)
    validate_evidence_quality(result)
    validate_llm_value(result)
    validate_account_identity(result, account_name)

    return True


# =====================================================
# ACCOUNT PIPELINE
#
# Deterministic Gate
#        |
#        v
# Single LLM Intelligence Generation
#
# =====================================================

def validate_account(row):
    from modules.deterministic_gate import deterministic_gate
    from modules.llm_client import call_llm
    from modules.llm_prompt_builder import build_intelligence_prompt

    result = {
        "llm_run_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "llm_validation": False
    }

    # =================================================
    # DETERMINISTIC GATE
    # =================================================

    gate_result = deterministic_gate(row)
    result.update(gate_result)

    # =================================================
    # SKIP PATH
    #
    # Protect LLM cost
    #
    # =================================================

    if not gate_result.get("run_llm", False):
        result.update({
            "llm_validation": True,
            "llm_stage": "SKIP",
            "llm_input_tokens": 0,
            "llm_output_tokens": 0,
            "llm_total_tokens": 0,
            "intelligence_input_tokens": 0,
            "intelligence_output_tokens": 0,
            "intelligence_total_tokens": 0
        })
        return result

    try:
        # =================================================
        # SINGLE INTELLIGENCE GENERATION
        # =================================================

        from modules.web_search_client import search_company, format_web_context

        location = row.get("Account State/Province", "") or row.get("Account State/Province (text only)", "")

        # Without a known location, a common/generic company name has
        # no way to be disambiguated if search returns a mixed bag of
        # different companies - confirmed via real testing (United
        # Community Bank: search returned BOTH the real ~200-location
        # regional bank AND an unrelated small Louisiana bank, and the
        # model picked the wrong one). Skipping search here falls back
        # to memory-only, same as before this feature existed - safer
        # than risking a confidently-wrong grounded answer with no way
        # to catch it.
        if location:
            search_snippets = search_company(row.get("Account Name", ""), location=location)
        else:
            search_snippets = None

        web_context = format_web_context(search_snippets)

        # Tracked separately from the LLM's own output fields, since
        # this describes what WE did (called search or not), not
        # something the model reports about itself. Lets a rep or QA
        # reviewer tell "grounded in a real search result" apart from
        # "model's memory only" at a glance.
        result["llm_used_web_search"] = bool(search_snippets)

        prompt = build_intelligence_prompt(row, web_context=web_context)
        intelligence = call_llm(prompt)

        print()
        print("========== RAW INTELLIGENCE JSON ==========")
        print(json.dumps(intelligence, indent=4))
        print("============================================")

        # =================================================
        # MERGE LLM OUTPUT
        # =================================================

        result.update(intelligence)

        # =================================================
        # TOKEN TRACKING
        # =================================================

        result.update({
            "llm_input_tokens": intelligence.get("llm_input_tokens", 0),
            "llm_output_tokens": intelligence.get("llm_output_tokens", 0),
            "llm_total_tokens": intelligence.get("llm_total_tokens", 0)
        })

        # =================================================
        # VALIDATE SELLER INTELLIGENCE
        # =================================================

        validate_llm_output(
            intelligence,
            intelligence.get("llm_raw_response", ""),
            row.get("Account Name", "")
        )

        # Re-merge: validate_llm_output (specifically
        # enforce_company_recognition_cap) can mutate
        # `intelligence` in place - e.g. clamping scores when
        # llm_company_recognized is false. The earlier
        # `result.update(intelligence)` above only copied the
        # pre-validation snapshot, so merge again to make sure
        # any code-enforced correction actually reaches the
        # final output.
        result.update(intelligence)

        result["llm_validation"] = True
        result["llm_stage"] = "SINGLE_INTELLIGENCE"

    except Exception as e:
        result.update({
            "llm_validation": False,
            "llm_error": str(e)
        })

    return result
