import pandas as pd


def read_accounts(file_path):

    print(f"Reading file: {file_path}")

    df = pd.read_excel(file_path)

    print(f"Loaded {len(df)} accounts")

    print("\nColumns found:")
    for column in df.columns:
        print(f"- {column}")

    return df
