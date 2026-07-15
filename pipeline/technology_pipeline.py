import pandas as pd

from modules.technology_enrichment import analyze_technology



def enrich_technology(accounts):


    technology_results = accounts.apply(
        analyze_technology,
        axis=1
    )


    technology_results = pd.DataFrame(
        technology_results.tolist()
    )


    accounts = pd.concat(
        [
            accounts.reset_index(drop=True),
            technology_results.reset_index(drop=True)
        ],
        axis=1
    )


    return accounts
