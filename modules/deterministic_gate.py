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


import re



# =====================================================
# CONFIGURATION
# =====================================================


LLM_THRESHOLD = 50


HIGH_COI_THRESHOLD = 60

MEDIUM_COI_THRESHOLD = 40



LOW_PRIORITY_TIERS = [

    "tier 4 monitor"

]



# =====================================================
# WORKLOAD CATEGORIES
# =====================================================


WORKLOAD_CATEGORIES = {


    "transaction":

    [

        "transaction",

        "transactional",

        "payments",

        "billing",

        "orders"

    ],


    "customer_application":

    [

        "customer facing",

        "customer application",

        "customer platform",

        "customer accounts",

        "customer profile",

        "customer profiles",

        "mobile application",

        "mobile applications",

        "customer identity"

    ],


    "real_time":

    [

        "real time",

        "real-time",

        "low latency",

        "real-time access"

    ],


    "operational":

    [

        "operational",

        "operational application",

        "operational applications",

        "customer 360",

        "fraud detection"

    ],


    "distributed_application":

    [

        "api",

        "microservices",

        "distributed",

        "event driven",

        "streaming",

        "integration platform"

    ]

}



# =====================================================
# DATABASE SIGNALS
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



TRANSACTIONAL_DATABASE_SIGNALS = [

    "transactional database",

    "transaction database",

    "application database"

]



# =====================================================
# CLOUD SUPPORTING SIGNALS
# =====================================================


CLOUD_SIGNALS = [

    "kubernetes",

    "container",

    "cloud native"

]



# =====================================================
# NEGATIVE SIGNALS
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


    text = re.sub(

        r"\s+",

        " ",

        text

    )


    return text.strip()



# =====================================================
# COLLECT ACCOUNT TEXT
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

        "workload_profile",

        "database_signal",

        "database_intensity",

        "operational_complexity",

        "realtime_requirement"

    ]



    values = []



    for field in fields:


        value = row.get(

            field,

            ""

        )


        if value:


            values.append(

                f"{field}: {value}"

            )



    return normalize_text(

        " ".join(values)

    )



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
# WORKLOAD CATEGORY DETECTION
# =====================================================


def detect_workload_categories(text):


    categories = []



    for category, signals in WORKLOAD_CATEGORIES.items():


        for signal in signals:


            if signal in text:


                categories.append(category)

                break



    return categories



# =====================================================
# DETERMINISTIC GATE
# =====================================================


def deterministic_gate(row):


    coi = row.get(

        "overall_coi",

        0

    )



    try:

        coi = float(coi)


    except:

        coi = 0



    tier = normalize_text(

        row.get(

            "priority_tier",

            ""

        )

    )



    account_text = collect_account_text(row)



    workload_categories = detect_workload_categories(

        account_text

    )



    database_technology_matches = find_matches(

        account_text,

        DATABASE_TECHNOLOGY_SIGNALS

    )



    database_modernization_matches = find_matches(

        account_text,

        DATABASE_MODERNIZATION_SIGNALS

    )



    transactional_database_matches = find_matches(

        account_text,

        TRANSACTIONAL_DATABASE_SIGNALS

    )



    cloud_matches = find_matches(

        account_text,

        CLOUD_SIGNALS

    )



    negative_matches = find_matches(

        account_text,

        NEGATIVE_SIGNALS

    )



    has_workload_evidence = (

        len(workload_categories) > 0

    )



    has_database_evidence = (

        len(database_technology_matches)

        +

        len(database_modernization_matches)

        +

        len(transactional_database_matches)

        >

        0

    )



    score = 0


    reasons = []



    # COI

    if coi >= HIGH_COI_THRESHOLD:


        score += 15


        reasons.append(

            "High COI"

        )


    elif coi >= MEDIUM_COI_THRESHOLD:


        score += 5


        reasons.append(

            "Medium COI"

        )



    # WORKLOAD

    if workload_categories:


        workload_score = min(

            len(workload_categories) * 15,

            45

        )


        score += workload_score


        reasons.append(

            "Operational workload"

        )



    # DATABASE TECHNOLOGY

    if database_technology_matches:


        score += 15


        reasons.append(

            "Database technology signal"

        )



    # DATABASE MODERNIZATION

    if database_modernization_matches:


        score += 10


        reasons.append(

            "Database modernization signal"

        )



    # TRANSACTIONAL DATABASE

    if transactional_database_matches:


        score += 10


        reasons.append(

            "Transactional database signal"

        )



    # CLOUD

    if cloud_matches:


        score += 5


        reasons.append(

            "Cloud native signal"

        )



    # NEGATIVE

    if negative_matches:


        score -= 30


        reasons.append(

            "Negative signal"

        )



    debug = {


        "debug_text_length":

            len(account_text),


        "debug_text_sample":

            account_text[:500],


        "debug_workload_categories":

            workload_categories,


        "debug_database_technology_matches":

            database_technology_matches,


        "debug_database_modernization_matches":

            database_modernization_matches,


        "debug_transactional_database_matches":

            transactional_database_matches,


        "debug_cloud_matches":

            cloud_matches,


        "debug_negative_matches":

            negative_matches,


        "has_workload_evidence":

            has_workload_evidence,


        "has_database_evidence":

            has_database_evidence

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

    if (

        has_workload_evidence

        and

        score >= LLM_THRESHOLD

    ):


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


        "gate_reason":

            (

                "Insufficient opportunity score"

                if has_workload_evidence

                else

                "No workload evidence"

            ),


        "gate_score": score,


        "coi_score": coi,


        "signals_found": reasons,


        **debug

    }
