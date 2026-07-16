import pandas as pd
import ast


df = pd.read_excel(
    "output/Enterprise_East_Scored.xlsx"
)


df = df[
    df["overall_coi"] >= 60
].copy()



def parse_workloads(x):

    try:
        values = ast.literal_eval(x)

        if isinstance(values, list):
            return values

    except:
        pass

    return []



df["workload_list"] = df["workloads"].apply(
    parse_workloads
)



def workload_tier_score(workloads):

    score = 0


    # =====================================================
    # TIER 1
    # Strong Couchbase application signals
    # =====================================================

    tier1 = [
        "API",
        "Integration",
        "Platform",
        "Real-Time",
        "Real Time",
        "Mobile Applications",
        "Payments",
        "Identity",
        "Digital",
        "Marketplace",
        "Customer Portal"
    ]


    # =====================================================
    # TIER 2
    # Useful operational workload signals
    # =====================================================

    tier2 = [
        "Customer 360",
        "Transaction Processing",
        "Fraud Detection",
        "Customer Accounts",
        "Workflow Applications"
    ]



    for workload in workloads:

        value = workload.lower()


        matched = False


        for signal in tier1:

            if signal.lower() in value:

                score += 15
                matched = True
                break



        if matched:
            continue



        for signal in tier2:

            if signal.lower() in value:

                score += 5
                break



    return score



df["workload_signal_score"] = df[
    "workload_list"
].apply(
    workload_tier_score
)



def database_score(x):

    x = str(x)

    if "Transactional" in x:

        return 15


    elif "Application" in x:

        return 10


    return 0



df["database_signal_score"] = df[
    "database_signal"
].apply(
    database_score
)



# =====================================================
# RANKING EXPERIMENT
# =====================================================

df["rank_score"] = (

    df["overall_coi"]

    +

    df["technology_score"]

    +

    df["company_signal_score"]

    +

    df["database_signal_score"]

    +

    df["workload_signal_score"]

)



ranked = df.sort_values(
    "rank_score",
    ascending=False
)



print("\n================ TOP 50 ================")

print(

    ranked[

        [

            "Account Name",

            "overall_coi",

            "technology_score",

            "company_signal_score",

            "database_signal",

            "workload_list",

            "workload_signal_score",

            "rank_score"

        ]

    ].head(50).to_string()

)



print("\n================ DISTRIBUTION ================")

print(

    ranked["rank_score"].describe()

)



print("\n================ 250 CUTOFF ================")

print(

    ranked.iloc[249]["rank_score"]

)



print("\n================ BOUNDARY ================")

print(

    ranked.iloc[240:260]

    [

        [

            "Account Name",

            "rank_score",

            "workload_list",

            "workload_signal_score"

        ]

    ]

    .to_string()

)

