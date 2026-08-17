import pandas as pd


def _looks_like_html(input_file):
    try:
        with open(input_file, "rb") as f:
            head = f.read(2000).lower()
        return b"<html" in head or b"<table" in head
    except Exception:
        return False


def load_accounts(input_file):

    print(f"Reading file: {input_file}")

    try:
        accounts = pd.read_excel(
            input_file
        )

    except Exception as e:

        # Common Salesforce/reporting-tool export quirk: files
        # named report<timestamp>.xls or similar that are NOT
        # real Excel binary at all - they're HTML tables saved
        # with an .xls extension. Real Excel readers (openpyxl,
        # xlrd) correctly fail on these. Detect and re-read as
        # HTML instead of assuming a genuine file-corruption
        # error.
        if _looks_like_html(input_file):

            print(
                f"pd.read_excel failed ({e}). File content looks "
                f"like HTML rather than real Excel binary (a common "
                f"export quirk) - re-reading as HTML table instead."
            )

            tables = pd.read_html(input_file)

            if not tables:
                raise ValueError(
                    f"File looked like HTML but pd.read_html found "
                    f"no tables in it: {input_file}"
                )

            accounts = tables[0]

        else:
            raise

    print(
        f"Loaded {len(accounts)} accounts\n"
    )

    # Account ID (CB Account Number) is required by a downstream
    # application that joins against this pipeline's output - not
    # every historical export has included it (confirmed: the
    # original report1784905185024.xls file has no ID column at
    # all), so this warns loudly rather than failing the load
    # outright, to avoid breaking existing workflows for files that
    # predate this requirement.
    if "CB Account Number" not in accounts.columns:
        print(
            "Note: no 'CB Account Number' column found in this file "
            "- expected for prospect lists that don't have an "
            "assigned account ID yet. The Account ID column in the "
            "final report will be blank for every account in this "
            "run. If this WAS meant to be an existing-account list, "
            "check that the export includes the ID column."
        )

    # Separate from CB Account Number, deliberately - confirmed
    # (2026-08-17) these are NOT the same kind of identifier.
    # CB Account Number could not be found anywhere in the actual
    # Salesforce UI, meaning it's likely a different system's number,
    # not a real SFDC join key. "ID (Long)" is Salesforce's own
    # 18-character record ID - the format Salesforce itself
    # recommends for any external system integration, specifically
    # because the 15-character "Account ID" alone is case-sensitive
    # and can cause mismatches in case-insensitive external systems.
    if "ID (Long)" not in accounts.columns:
        print(
            "Note: no 'ID (Long)' column found in this file - this "
            "is the safe, 18-character Salesforce record ID needed "
            "if a downstream system will join back to Salesforce. "
            "The Salesforce ID column in the final report will be "
            "blank for every account in this run."
        )

    return accounts
