# =====================================================
# COI SCORING ENGINE
# Couchbase Sales Intelligence Agent
#
# Purpose:
# Determine likelihood that an account has a
# Couchbase-relevant operational workload opportunity.
#
# Philosophy:
#
# Operational Workload Fit
#        >
# Database Opportunity
#        >
# Real-Time Requirements
#        >
# Technical Capability
#        >
# Company Context
#
# Goal:
# Help sellers identify accounts worth calling,
# create better discovery conversations,
# and shorten sales cycles.
# =====================================================


def calculate_coi(row):

    score = 0

    breakdown = {}

    signals_found = []

    missing_signals = []



    # =====================================================
    # INPUT NORMALIZATION
    # =====================================================

    industry = str(
        row.get(
            "industry",
            "Unknown"
        )
    )


    workload_profile = str(
        row.get(
            "workload_profile",
            ""
        )
    )


    workloads = row.get(
        "workloads",
        []
    )


    if isinstance(workloads, str):

        workloads = [
            workloads
        ]


    workload_text = " ".join(
        [
            str(x).lower()
            for x in workloads
        ]
    )


    database_intensity = int(
        row.get(
            "database_intensity",
            0
        )
    )


    operational_complexity = int(
        row.get(
            "operational_complexity",
            0
        )
    )


    realtime_requirement = int(
        row.get(
            "realtime_requirement",
            0
        )
    )


    technology_score = int(
        row.get(
            "technology_score",
            0
        )
    )


    engineering = str(
        row.get(
            "engineering_signal",
            "Unknown"
        )
    )


    company_size = str(
        row.get(
            "company_size",
            "Unknown"
        )
    )



    # =====================================================
    # 1. OPERATIONAL WORKLOAD FIT
    #
    # Maximum 40 points
    #
    # Primary Couchbase indicator
    # =====================================================

    workload_points = 0


    WORKLOAD_WEIGHTS = {

        "transaction": 10,

        "payment": 10,

        "customer": 10,

        "profile": 10,

        "identity": 8,

        "api": 8,

        "application": 8,

        "real-time": 10,

        "real time": 10,

        "mobile": 8,

        "integration": 8,

        "operational": 10,

        "data exchange": 8

    }



    for signal, points in WORKLOAD_WEIGHTS.items():

        if signal in workload_text:

            workload_points += points

            signals_found.append(
                "Workload: " + signal
            )



    # Structured workload profile bonus

    if workload_profile:

        workload_points += 10

        signals_found.append(
            "Workload profile: "
            + workload_profile
        )



    workload_points = min(
        workload_points,
        40
    )


    if workload_points == 0:

        missing_signals.append(
            "Operational workload evidence"
        )


    breakdown["workload_fit_points"] = workload_points


    score += workload_points



    # =====================================================
    # 2. DATABASE OPPORTUNITY
    #
    # Maximum 30 points
    #
    # Replaces keyword guessing
    # =====================================================

    database_points = 0


    database_points += database_intensity * 3


    database_points += operational_complexity * 3



    database_points = min(
        database_points,
        30
    )


    if database_points > 0:

        signals_found.append(
            "Database intensity: "
            + str(database_intensity)
        )

        signals_found.append(
            "Operational complexity: "
            + str(operational_complexity)
        )


    else:

        missing_signals.append(
            "Database opportunity evidence"
        )



    breakdown["database_opportunity_points"] = database_points


    score += database_points



    # =====================================================
    # 3. REAL-TIME REQUIREMENT
    #
    # Maximum 15 points
    # =====================================================

    realtime_points = realtime_requirement * 3


    realtime_points = min(
        realtime_points,
        15
    )


    if realtime_points > 0:

        signals_found.append(
            "Real-time requirement"
        )


    else:

        missing_signals.append(
            "Real-time workload evidence"
        )



    breakdown["realtime_points"] = realtime_points


    score += realtime_points



    # =====================================================
    # 4. TECHNICAL ENVIRONMENT
    #
    # Maximum 10 points
    # =====================================================

    technical_points = 0


    if engineering == "High":

        technical_points += 5

        signals_found.append(
            "High engineering capability"
        )


    elif engineering == "Medium":

        technical_points += 3



    if technology_score >= 40:

        technical_points += 5

        signals_found.append(
            "Technology maturity"
        )


    elif technology_score >= 20:

        technical_points += 3



    technical_points = min(
        technical_points,
        10
    )


    breakdown["technical_environment_points"] = technical_points


    score += technical_points



    # =====================================================
    # 5. COMPANY CONTEXT
    #
    # Maximum 5 points
    #
    # Supporting only
    # =====================================================

    company_points = 0


    if company_size == "Enterprise":

        company_points = 5

        signals_found.append(
            "Enterprise company"
        )


    breakdown["company_context_points"] = company_points


    score += company_points



    # =====================================================
    # INDUSTRY CONTEXT
    #
    # Does not drive score
    # =====================================================

    breakdown["industry_context"] = (
        "Industry is supporting context only: "
        + industry
    )



    # =====================================================
    # FINAL SCORE
    # =====================================================

    final_score = min(
        score,
        100
    )


    breakdown["raw_coi_score"] = score

    breakdown["overall_coi"] = final_score


    breakdown["signals_found"] = signals_found

    breakdown["missing_signals"] = missing_signals



    # =====================================================
    # PRIORITY
    # =====================================================

    if final_score >= 80:

        tier = "Tier 1 Strategic"


    elif final_score >= 60:

        tier = "Tier 2 Strong Target"


    elif final_score >= 40:

        tier = "Tier 3 Nurture"


    else:

        tier = "Tier 4 Monitor"



    breakdown["priority_tier"] = tier



    # =====================================================
    # EXPLANATION
    # =====================================================

    if workload_points >= 30:

        why_score = (
            "Strong Couchbase alignment based on "
            "operational workload evidence."
        )


    elif workload_points >= 15:

        why_score = (
            "Potential Couchbase opportunity. "
            "Validate workload and database challenges."
        )


    else:

        why_score = (
            "Limited operational workload evidence."
        )


    breakdown["why_score"] = why_score



    # =====================================================
    # SALES MOTION
    # =====================================================

    if tier == "Tier 1 Strategic":

        motion = (
            "Technical discovery with application "
            "architecture, engineering, and data leaders."
        )


    elif tier == "Tier 2 Strong Target":

        motion = (
            "Discovery conversation focused on "
            "applications, scalability, and database challenges."
        )


    else:

        motion = (
            "Continue enrichment before seller outreach."
        )



    breakdown["sales_motion"] = motion



    return breakdown
