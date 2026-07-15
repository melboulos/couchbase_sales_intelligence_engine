import pandas as pd

from modules.llm_validator import validate_account


INPUT_FILE = (
    "output/"
    "Enterprise_East_Scored.xlsx"
)



accounts = pd.read_excel(
    INPUT_FILE
)



test_accounts = accounts[
    accounts["priority_tier"]
    ==
    "Tier 1 Strategic"
].head(10)



print(
    f"Testing {len(test_accounts)} accounts"
)



results = []



for _, row in test_accounts.iterrows():

    print(
        "\n=========================="
    )

    print(
        row["Account Name"]
    )


    result = validate_account(
        row
    )


    print(
        result
    )


    results.append(
        {
            "Account Name":
                row["Account Name"],

            **result
        }
    )



pd.DataFrame(
    results
).to_excel(
    "output/llm_prompt_test.xlsx",
    index=False
)


print(
    "\nSaved:"
    " output/llm_prompt_test.xlsx"
)
