import pandas as pd


df = pd.read_excel(
    "output/Enterprise_East_Scored.xlsx"
)


df = df[
    df["overall_coi"] >= 60
].copy()



def buyer_signal(row):

    name = str(row["Account Name"]).lower()
    industry = str(row["industry"]).lower()


    score = 0


    # Strong application companies

    if industry in [
        "Technology / SaaS"
    ]:
        score += 20



    # Healthcare technology indicators

    if any(x in name for x in [
        "redox",
        "patient",
        "healthtech",
        "health data",
        "health solutions",
        "digital health",
        "analytics",
        "care",
        "health"
    ]):
        score += 10



    # Traditional providers

    if any(x in name for x in [
        "hospital",
        "medical center",
        "health system"
    ]):
        score -= 10



    # Banks

    if any(x in name for x in [
        "bank",
        "credit union"
    ]):
        score -= 10



    return score



df["buyer_signal"] = df.apply(
    buyer_signal,
    axis=1
)



df["new_rank"] = (
    df["overall_coi"]
    +
    df["technology_score"]
    +
    df["buyer_signal"]
)



ranked = df.sort_values(
    "new_rank",
    ascending=False
)



print("\nTOP 50 WITH BUYER SIGNAL")

print(
    ranked[
        [
            "Account Name",
            "industry",
            "overall_coi",
            "buyer_signal",
            "new_rank"
        ]
    ]
    .head(50)
    .to_string()
)


print("\n250 CUTOFF")

print(
    ranked.iloc[249]["new_rank"]
)

