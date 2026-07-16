import pandas as pd


df = pd.read_excel(
    "output/Enterprise_East_Scored.xlsx"
)


df = df[
    df["overall_coi"] >= 60
].copy()



def classify_archetype(row):

    name = str(
        row["Account Name"]
    ).lower()

    industry = str(
        row.get(
            "industry",
            ""
        )
    ).lower()


    text = name + " " + industry



    # ==========================================
    # HEALTHCARE PROVIDER
    # ==========================================

    provider_signals = [

        "hospital",

        "medical center",

        "health system",

        "health center",

        "regional medical",

        "clinic",

        "healthcare system",

        "university health"

    ]


    for signal in provider_signals:

        if signal in text:

            return "Healthcare Provider"



    # ==========================================
    # HEALTHCARE TECHNOLOGY
    # ==========================================

    healthcare_tech_signals = [

        "healthtech",

        "health technology",

        "health solutions",

        "health analytics",

        "patient",

        "health data",

        "medical software",

        "digital health",

        "health platform",

        "healthcare technology"

    ]


    for signal in healthcare_tech_signals:

        if signal in text:

            return "Healthcare Technology"



    # ==========================================
    # FINTECH / PAYMENTS
    # ==========================================

    fintech_signals = [

        "payment",

        "payments",

        "pay",

        "wallet",

        "lending",

        "loan",

        "fintech"

    ]


    for signal in fintech_signals:

        if signal in text:

            return "FinTech / Payments"



    # ==========================================
    # SOFTWARE / PLATFORM
    # ==========================================

    software_signals = [

        "software",

        "systems",

        "platform",

        "solutions",

        "technology",

        "digital",

        "cloud",

        "api",

        "network"

    ]


    for signal in software_signals:

        if signal in text:

            return "Software / Platform"



    # ==========================================
    # FINANCIAL INSTITUTION
    # ==========================================

    financial_signals = [

        "bank",

        "credit union",

        "savings",

        "financial institution"

    ]


    for signal in financial_signals:

        if signal in text:

            return "Financial Institution"



    return "Other"



df["company_archetype"] = df.apply(
    classify_archetype,
    axis=1
)



print(
    "\n================ ARCHETYPE COUNTS ================"
)

print(
    df["company_archetype"]
    .value_counts()
)



print(
    "\n================ TOP ACCOUNTS BY ARCHETYPE ================"
)



print(

    df.sort_values(
        "overall_coi",
        ascending=False
    )
    [
        [
            "Account Name",
            "industry",
            "company_archetype",
            "overall_coi"
        ]
    ]
    .head(100)
    .to_string()

)



print(
    "\n================ HEALTHCARE BREAKDOWN ================"
)


print(

    df[
        df["industry"]=="Healthcare"
    ]
    [
        [
            "Account Name",
            "company_archetype",
            "overall_coi"
        ]
    ]
    .head(100)
    .to_string()

)

