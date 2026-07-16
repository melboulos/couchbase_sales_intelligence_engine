import pandas as pd

from modules.company_archetype import (
    classify_company_archetype
)


def enrich_company_archetypes(accounts):

    accounts = accounts.copy()


    accounts["company_archetype"] = accounts.apply(
        classify_company_archetype,
        axis=1
    )


    return accounts
