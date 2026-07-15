import pandas as pd

from modules.account_intelligence import analyze_account_intelligence



def enrich_account_intelligence(accounts):


    account_intelligence_results = accounts.apply(
        analyze_account_intelligence,
        axis=1
    )


    account_intelligence_results = pd.DataFrame(
        account_intelligence_results.tolist()
    )


    accounts = pd.concat(
        [
            accounts.reset_index(drop=True),
            account_intelligence_results.reset_index(drop=True)
        ],
        axis=1
    )


    return accounts
