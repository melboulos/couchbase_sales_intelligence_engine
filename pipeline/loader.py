import pandas as pd


def load_accounts(input_file):

    print(f"Reading file: {input_file}")

    accounts = pd.read_excel(
        input_file
    )

    print(
        f"Loaded {len(accounts)} accounts\n"
    )

    return accounts
