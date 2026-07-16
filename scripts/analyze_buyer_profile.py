import pandas as pd


df = pd.read_excel(
    "output/Enterprise_East_Scored.xlsx"
)


df = df[
    df["overall_coi"] >= 60
].copy()



def classify_buyer(name, industry):

    text = (
        str(name) + " " + str(industry)
    ).lower()


    # ==========================================
    # Technology / Software / Platform
    # ==========================================

    software_signals = [
        "software",
        "systems",
        "solutions",
        "platform",
        "saas",
        "technology",
        "technologies",
        "digital",
        "cloud",
        "api",
        "network"
    ]


    for signal in software_signals:

        if signal in text:

            return "Software / Platform"



    # ==========================================
    # Healthcare Technology
    # ==========================================

    healthcare_tech = [
        "healthtech",
        "health technology",
        "healthcare technology",
        "medical software",
        "patient engagement",
        "health data",
        "analytics"
    ]


    for signal in healthcare_tech:

        if signal in text:

            return "Healthcare Technology"



    # ==========================================
    # Healthcare Provider
    # ==========================================

    healthcare_provider = [
        "hospital",
        "health system",
        "medical center",
        "clinic",
        "healthcare center",
        "health center",
        "health care"
    ]


    for signal in healthcare_provider:

        if signal in text:

            return "Healthcare Provider"



    # ==========================================
    # Financial Technology
    # ==========================================

    fintech = [
        "payment",
        "payments",
        "fintech",
        "financial technology",
        "wallet",
        "lending",
        "loan",
        "fraud"
    ]


    for signal in fintech:

        if signal in text:

            return "FinTech / Payments"



    # ==========================================
    # Traditional Financial Institution
    # ==========================================

    finance = [
        "bank",
        "credit union",
        "savings",
        "financial institution"
    ]


    for signal in finance:

        if signal in text:

            return "Bank / Financial Institution"



    return "Other"



df["buyer_profile"] = df.apply(
    lambda x: classify_buyer(
        x["Account Name"],
        x["industry"]
    ),
    axis=1
)



print("\n================ PROFILE COUNTS ================")

print(
    df["buyer_profile"]
    .value_counts()
)



print("\n================ TOP SCORES BY PROFILE ================")

print(

    df.groupby(
        "buyer_profile"
    )["overall_coi"]
    .agg(
        [
            "count",
            "mean",
            "max"
        ]
    )
    .sort_values(
        "max",
        ascending=False
    )

)



print("\n================ TOP 50 SAMPLE ================")

print(

    df.sort_values(
        "overall_coi",
        ascending=False
    )
    [
        [
            "Account Name",
            "industry",
            "buyer_profile",
            "overall_coi"
        ]
    ]
    .head(50)
    .to_string()

)

