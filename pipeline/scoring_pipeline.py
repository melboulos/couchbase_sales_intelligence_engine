import pandas as pd

from modules.scoring_engine import calculate_coi



def score_accounts(accounts):


    coi_results = accounts.apply(
        calculate_coi,
        axis=1
    )


    coi_results = pd.DataFrame(
        coi_results.tolist()
    )


    accounts = pd.concat(
        [
            accounts.reset_index(drop=True),
            coi_results.reset_index(drop=True)
        ],
        axis=1
    )


    return accounts
