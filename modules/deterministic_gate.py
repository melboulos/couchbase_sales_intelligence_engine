# =====================================================
# DETERMINISTIC SALES INTELLIGENCE GATE
# Couchbase Sales Intelligence Engine
#
# Architecture:
#
# Deterministic Gate
#        |
#        |
#        v
# Single LLM Intelligence Generation
#
# Purpose:
#
# Replace LLM qualification.
#
# Responsibilities:
#
# - Determine if account deserves LLM enrichment
# - Detect Couchbase-style workload patterns
# - Prioritize seller attention
# - Prevent unnecessary LLM cost
#
# LLM ONLY receives high-value accounts.
#
# =====================================================
#
# DESIGN NOTE (updated):
#
# gate_score now starts from overall_coi (computed by
# scoring_engine.py from company_intelligence.py's
# workload_profile / database_intensity /
# operational_complexity / realtime_requirement fields),
# rather than being recomputed from an independent
# keyword system.
#
# This gate then applies +/- adjustments on top of COI
# for signals COI does NOT already capture:
#   - existing database technology mentions (Oracle, etc.)
#   - modernization language
#   - cloud-native signals
#   - negative signals (consulting, staff aug, etc.)
#
# Qualifying workload evidence is now based on whether
# company_intelligence.py actually recognized the account
# (workload_profile is set), not a second independent
# workload keyword search.
#
# =====================================================


import re


# =====================================================
# CONFIGURATION
# =====================================================


LLM_THRESHOLD = 50   # <-- NEEDS RECALIBRATION, see note below


LOW_PRIORITY_TIERS = [
    "tier 4 monitor"
]


# =====================================================
# DATABASE SIGNALS
#
# Kept as-is: these are NOT captured anywhere in
# company_intelligence.py / scoring_engine.py, so they
# remain genuinely additive signals.
# =====================================================


DATABASE_TECHNOLOGY_SIGNALS = [
    "mongodb",
    "oracle",
    "postgres",
    "postgresql",
    "mysql",
    "sql server",
    "dynamodb",
    "cassandra"
]


DATABASE_MODERNIZATION_SIGNALS = [
    "data modernization",
    "database modernization",
    "database performance",
    "database scaling",
    "operational data",
    "distributed database",
    "data store"
]


CLOUD_SIGNALS = [
    "kubernetes",
    "container",
    "cloud native"
]


# =====================================================
# NEGATIVE SIGNALS
#
# Kept as-is: excludes service-business types that COI
# has no concept of.
# =====================================================


NEGATIVE_SIGNALS = [
    "consulting",
    "professional services",
    "staff augmentation",
    "marketing agency",
    "training"
]


# =====================================================
# NORMALIZATION
# =====================================================


def normalize_text(value):
    if value is None:
        return ""
    text = str(value).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# =====================================================
# COLLECT ACCOUNT TEXT
#
# Used only for the remaining independent signals
# (database technology, modernization, cloud, negative).
# =====================================================


def collect_account_text(row):
    fields = [
        "Account Name",
        "Description",
        "Industry",
        "technologies",
        "technology",
        "technical_signals",
        "business_signals",
        "cloud_signals",
        "ai_signals",
        "notes",
        "workloads",
        "database_signal"
    ]

    values = []

    for field in fields:
        value = row.get(field, "")
        if value:
            values.append(f"{field}: {value}")

    return normalize_text(" ".join(values))


# =====================================================
# SIGNAL MATCHING
# =====================================================


def find_matches(text, signals):
    matches = []
    for signal in signals:
        if signal in text:
            matches.append(signal)
    return matches


# =====================================================
# DETERMINISTIC GATE
# =====================================================


def deterministic_gate(row):

    coi = row.get("overall_coi", 0)

    try:
        coi = float(coi)
    except:
        coi = 0

    tier = normalize_text(row.get("priority_tier", ""))

    workload_profile = row.get("workload_profile", "")

    has_workload_evidence = bool(workload_profile)

    account_text = collect_account_text(row)

    database_technology_matches = find_matches(
        account_text, DATABASE_TECHNOLOGY_SIGNALS
    )

    database_modernization_matches = find_matches(
        account_text, DATABASE_MODERNIZATION_SIGNALS
    )

    cloud_matches = find_matches(
        account_text, CLOUD_SIGNALS
    )

    negative_matches = find_matches(
        account_text, NEGATIVE_SIGNALS
    )

    has_database_evidence = (
        len(database_technology_matches)
        + len(database_modernization_matches)
        > 0
    )

    # =================================================
    # GATE SCORE
    #
    # Starts from COI (the same signal driving tier),
    # then applies additive adjustments for evidence
    # COI does not already capture.
    # =================================================

    score = coi

    reasons = []

    if coi >= 60:
        reasons.append("High COI")
    elif coi >= 40:
        reasons.append("Medium COI")

    if has_workload_evidence:
        reasons.append("Workload profile: " + workload_profile)

    if database_technology_matches:
        score += 15
        reasons.append("Database technology signal")

    if database_modernization_matches:
        score += 10
        reasons.append("Database modernization signal")

    if cloud_matches:
        score += 5
        reasons.append("Cloud native signal")

    if negative_matches:
        score -= 30
        reasons.append("Negative signal")

    debug = {
        "debug_text_length": len(account_text),
        "debug_text_sample": account_text[:500],
        "debug_database_technology_matches": database_technology_matches,
        "debug_database_modernization_matches": database_modernization_matches,
        "debug_cloud_matches": cloud_matches,
        "debug_negative_matches": negative_matches,
        "has_workload_evidence": has_workload_evidence,
        "has_database_evidence": has_database_evidence
    }

    # HARD STOP

    if tier in LOW_PRIORITY_TIERS:
        return {
            "run_llm": False,
            "llm_stage": "SKIP",
            "gate_decision": "SKIP",
            "gate_reason": "Low priority tier",
            "gate_score": score,
            "coi_score": coi,
            "signals_found": reasons,
            **debug
        }

    # LLM PATH

    if has_workload_evidence and score >= LLM_THRESHOLD:
        return {
            "run_llm": True,
            "llm_stage": "INTELLIGENCE",
            "gate_decision": "LLM",
            "gate_reason": "; ".join(reasons),
            "gate_score": score,
            "coi_score": coi,
            "signals_found": reasons,
            **debug
        }

    # SKIP

    return {
        "run_llm": False,
        "llm_stage": "SKIP",
        "gate_decision": "SKIP",
        "gate_reason": (
            "Insufficient opportunity score"
            if has_workload_evidence
            else "No workload evidence"
        ),
        "gate_score": score,
        "coi_score": coi,
        "signals_found": reasons,
        **debug
    }
