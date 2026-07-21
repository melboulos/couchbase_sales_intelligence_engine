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
# LLM does NOT qualify accounts.
#
# LLM creates:
# - seller value hypothesis
# - Couchbase conversation angle
# - technical discovery strategy
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
    "why_this_workload_matters",
    "engineering_implications",
    "couchbase_point_of_view",
    "technical_risks_to_validate",
    "conversation_strategy",
    "discovery_progression",
    "missing_information"
]

LIST_FIELDS = [
    "engineering_implications",
    "technical_risks_to_validate",
    "missing_information"
]


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
    returned = normalize_text(result.get("account_name", ""))
    expected = normalize_text(account_name)

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
        "enterprise",
        "large company",
        "market leader",
        "industry leader",
        "company size",
        "revenue",
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

        result["llm_validation"] = True
        result["llm_stage"] = "SINGLE_INTELLIGENCE"

    except Exception as e:
        result.update({
            "llm_validation": False,
            "llm_error": str(e)
        })

    return result
