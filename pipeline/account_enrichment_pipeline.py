import pandas as pd

from modules.account_enrichment import enrich_account



def enrich_accounts(accounts):


    account_results = accounts.apply(
        enrich_account,
        axis=1
    )


    account_results = pd.DataFrame(
        account_results.tolist()
    )


    for col in account_results.columns:

        if col in accounts.columns:

            accounts[col] = account_results[col]

            account_results = account_results.drop(
                columns=[col]
            )


    accounts = pd.concat(
        [
            accounts.reset_index(drop=True),
            account_results.reset_index(drop=True)
        ],
        axis=1
    )


    return accounts
