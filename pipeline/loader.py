import pandas as pd


def _looks_like_html(input_file):
    try:
        with open(input_file, "rb") as f:
            head = f.read(2000).lower()
        return b"<html" in head or b"<table" in head
    except Exception:
        return False


def _find_header_row_index(raw_df, anchor_column="Account Name", max_scan_rows=30):
    """
    Some Salesforce report exports include title/timestamp/"Filtered
    By"/filter-criteria metadata rows before the real header row -
    confirmed real case (2026-08-18): 9 such rows preceded the actual
    header in a report using the same template as a previously-
    working file, so this can't be assumed to always be at row 0.
    Scans for the row containing the anchor column name (present in
    every export seen so far) rather than hardcoding a fixed number
    of rows to skip, since that count varies by report configuration.
    """
    scan_limit = min(max_scan_rows, len(raw_df))
    for r in range(scan_limit):
        row_values = [str(v).strip() for v in raw_df.iloc[r] if pd.notna(v)]
        if anchor_column in row_values:
            return r
    return None


def load_accounts(input_file):

    print(f"Reading file: {input_file}")

    used_html_fallback = False

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
            used_html_fallback = True

        else:
            raise

    # If most columns came back as "Unnamed: N", the real header
    # probably isn't at row 0 - re-scan for it and re-read correctly,
    # rather than silently proceeding with a broken, headerless load.
    unnamed_ratio = sum(
        str(c).startswith("Unnamed:") for c in accounts.columns
    ) / max(len(accounts.columns), 1)

    if unnamed_ratio > 0.5:

        print(
            "Most columns came back as 'Unnamed' - the real header "
            "row probably isn't row 1 (common when a Salesforce "
            "report export includes title/timestamp/filter metadata "
            "above the actual data). Scanning for the real header row..."
        )

        if used_html_fallback:
            raw = pd.read_html(input_file, header=None)[0]
        else:
            raw = pd.read_excel(input_file, header=None)

        header_row = _find_header_row_index(raw)

        if header_row is None:
            print(
                "Could not find a row containing 'Account Name' in "
                "the first 30 rows - proceeding with the original "
                "load as-is, but this file may need manual review."
            )
        else:
            print(f"Found real header at row {header_row + 1} - re-reading with the correct header.")
            if used_html_fallback:
                accounts = pd.read_html(input_file, header=header_row)[0]
            else:
                accounts = pd.read_excel(input_file, header=header_row)

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
