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
    "couchbase_point_of_view",
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
    "couchbase_point_of_view",
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
DEFUNCT_FACT_PATTERNS = [
    "was a ", "was an ", "used to be", "no longer exists",
    "no longer operates", "ceased operations", "was acquired by",
    "was later acquired", "was subsequently acquired",
    "is now part of", "was renamed", "was rebranded",
    "was dissolved", "went out of business", "filed for bankruptcy",
    "was merged into", "prior to its acquisition",
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

    is_defunct = any(pattern in fact for pattern in DEFUNCT_FACT_PATTERNS)
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

def validate_llm_output(result, raw_text, account_name):
    validate_required_fields(result)
    validate_non_empty_fields(result)
    validate_independent_score(result)
    validate_recognition_evidence(result)
    enforce_company_recognition_cap(result)

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

        prompt = build_intelligence_prompt(row)
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
