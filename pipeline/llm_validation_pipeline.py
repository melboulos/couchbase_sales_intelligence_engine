import pandas as pd
import time
import os

from datetime import datetime, timezone

from modules.sales_intelligence_pipeline import validate_account

# Confirmed wrong this session - was $0.99/1K (i.e. $990/million
# tokens), off by ~1,375x. Real AWS Bedrock on-demand pricing for
# Meta Llama 70B-class models (meta.llama3-70b-instruct-v1:0) is
# approximately $0.72 per MILLION tokens, input and output at the
# same rate, as of July 2026 (see https://aws.amazon.com/bedrock/pricing/
# - Meta section - and cross-referenced against independent trackers).
# $0.72/M = $0.00072/1K. If AWS Bedrock console/billing shows a
# different number for your account/region, trust that over this
# comment and update these constants accordingly.
LLM_INPUT_COST_PER_1K = 0.00072
LLM_OUTPUT_COST_PER_1K = 0.00072


LLM_RESULTS_FILE = (
    "output/"
    "llm_validation_results.xlsx"
)

TOKEN_SUMMARY_FILE = (
    "output/"
    "llm_token_summary.xlsx"
)



def generate_token_summary(llm_results):

    if len(llm_results) == 0:
        return pd.DataFrame()


    input_tokens = int(
        llm_results["llm_input_tokens"].fillna(0).sum()
    )

    output_tokens = int(
        llm_results["llm_output_tokens"].fillna(0).sum()
    )

    total_tokens = int(
        llm_results["llm_total_tokens"].fillna(0).sum()
    )


    input_cost = (
        input_tokens / 1000
    ) * LLM_INPUT_COST_PER_1K


    output_cost = (
        output_tokens / 1000
    ) * LLM_OUTPUT_COST_PER_1K


    total_cost = (
        input_cost +
        output_cost
    )


    count = len(llm_results)


    return pd.DataFrame(
        [{
            "llm_run_id":
                llm_results["llm_run_id"].iloc[0],

            "llm_model":
                llm_results["llm_model"].iloc[0]
                if "llm_model" in llm_results.columns
                else "",

            "run_timestamp":
                datetime.now(
                    timezone.utc
                ).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                ),

            "accounts_validated":
                count,

            "input_tokens":
                input_tokens,

            "output_tokens":
                output_tokens,

            "total_tokens":
                total_tokens,

            "average_tokens_per_account":
                int(total_tokens / count) if count else 0,

            "input_cost_usd":
                round(input_cost,4),

            "output_cost_usd":
                round(output_cost,4),

            "total_cost_usd":
                round(total_cost,4),

            "average_cost_per_account":
                round(total_cost / count,4) if count else 0
        }]
    )



# =====================================================
# VALIDATE ACCOUNTS
#
# Checkpoint behavior is PER-ROW, not per-file.
#
# If output/llm_validation_results.xlsx exists:
#   - Accounts already present with llm_validation == True
#     are kept as-is (no LLM call, no cost).
#   - Accounts present with llm_validation == False, OR not
#     present in the checkpoint at all, are (re)sent to the
#     LLM.
#
# To force a specific account to be re-run: open the
# checkpoint file, find its row, set llm_validation to
# FALSE, save, and re-run. Only that account is re-sent.
# =====================================================

import concurrent.futures

# Bedrock calls are independent network round trips, so run
# them concurrently rather than one at a time - sequential
# execution across hundreds of accounts could take well over
# an hour. Keep this modest; raise it only if you've confirmed
# Bedrock isn't throttling you at this concurrency.
MAX_WORKERS = 5

# Save progress to LLM_RESULTS_FILE every N completed accounts,
# not just once at the very end. Without this, a crash or
# dropped connection partway through a large run (e.g. ~500
# accounts) loses ALL progress, since nothing was written to
# disk until the whole batch finished.
CHECKPOINT_EVERY = 25


def _run_llm_batch(rows, kept_df, existing_columns):
    """
    Runs validate_account concurrently across `rows`, writing
    an incremental checkpoint (kept_df + completed results so
    far) to LLM_RESULTS_FILE every CHECKPOINT_EVERY completions.
    Returns the full list of new results once all rows are done.
    """

    total = len(rows)
    new_results = []
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(MAX_WORKERS, max(1, total))
    ) as executor:

        futures = {
            executor.submit(validate_account, row): row
            for row in rows
        }

        for future in concurrent.futures.as_completed(futures):

            row = futures[future]
            account_name = row.get("Account Name", "Unknown")

            try:
                result = future.result()
                result["Account Name"] = account_name
            except Exception as e:
                result = {
                    "Account Name": account_name,
                    "llm_validation": False,
                    "llm_error": f"Worker exception: {e}"
                }

            new_results.append(result)
            completed += 1

            print(f"[{completed}/{total}] {account_name} - done")

            if completed % CHECKPOINT_EVERY == 0 or completed == total:

                partial_df = pd.DataFrame(new_results)

                if kept_df is not None and len(kept_df) > 0:
                    combined = pd.concat(
                        [kept_df, partial_df], ignore_index=True
                    )
                else:
                    combined = partial_df

                combined = combined.loc[:, ~combined.columns.duplicated()]
                combined.to_excel(LLM_RESULTS_FILE, index=False)

                print(
                    f"  Checkpoint saved: {completed}/{total} "
                    f"complete ({LLM_RESULTS_FILE})"
                )

    return new_results


def validate_accounts(accounts):

    print(
        "\nStarting LLM validation..."
    )


    llm_accounts = accounts.copy()


    total = len(
        llm_accounts
    )


    print(
        f"LLM candidates: {total}"
    )


    if total == 0:
        return accounts


    if os.path.exists(
        LLM_RESULTS_FILE
    ):

        print(
            "Existing LLM results found. "
            "Checking which accounts still need to run..."
        )

        existing_results = pd.read_excel(
            LLM_RESULTS_FILE
        )

        existing_by_name = {}

        for _, existing_row in existing_results.iterrows():

            name = existing_row.get(
                "Account Name",
                ""
            )

            # If an account name appears more than once in the
            # checkpoint, keep the first occurrence.
            if name not in existing_by_name:
                existing_by_name[name] = existing_row


        already_done_rows = []
        rows_to_run = []


        for _, row in llm_accounts.iterrows():

            name = row.get(
                "Account Name",
                ""
            )

            existing_row = existing_by_name.get(name)

            already_validated = (
                existing_row is not None
                and bool(
                    existing_row.get(
                        "llm_validation",
                        False
                    )
                )
            )

            if already_validated:
                already_done_rows.append(existing_row)
            else:
                rows_to_run.append(row)


        print(
            f"Already validated (kept from checkpoint): "
            f"{len(already_done_rows)}"
        )

        print(
            f"To (re)run through the LLM: "
            f"{len(rows_to_run)}"
        )

        kept_df = (
            pd.DataFrame(already_done_rows)
            if already_done_rows
            else pd.DataFrame(columns=existing_results.columns)
        )

        new_results = _run_llm_batch(
            rows_to_run, kept_df, existing_results.columns
        )

        new_df = (
            pd.DataFrame(new_results)
            if new_results
            else pd.DataFrame(columns=existing_results.columns)
        )

        llm_results = pd.concat(
            [kept_df, new_df],
            ignore_index=True
        )

        llm_results = llm_results.loc[
            :,
            ~llm_results.columns.duplicated()
        ]

        llm_results.to_excel(
            LLM_RESULTS_FILE,
            index=False
        )

        print(
            f"Updated LLM checkpoint: {LLM_RESULTS_FILE}"
        )


    else:

        print(
            "Running threaded LLM validation "
            f"(max {MAX_WORKERS} concurrent, "
            f"checkpoint every {CHECKPOINT_EVERY})..."
        )

        start_time = time.time()

        rows = [row for _, row in llm_accounts.iterrows()]

        results = _run_llm_batch(rows, None, None)

        elapsed = time.time() - start_time
        print(f"All {total} accounts complete. Elapsed {elapsed:.1f}s")

        llm_results = pd.DataFrame(
            results
        )


        llm_results = llm_results.loc[
            :,
            ~llm_results.columns.duplicated()
        ]


        llm_results.to_excel(
            LLM_RESULTS_FILE,
            index=False
        )


        print(
            f"Saved LLM checkpoint: {LLM_RESULTS_FILE}"
        )



    # ==========================================
    # TOKEN REPORT
    # ==========================================

    token_summary = generate_token_summary(
        llm_results
    )


    print(
        "\n========== LLM TOKEN SUMMARY =========="
    )


    print(
        token_summary.to_string(
            index=False
        )
    )


    print(
        "======================================="
    )


    token_summary.to_excel(
        TOKEN_SUMMARY_FILE,
        index=False
    )


    print(
        f"Saved: {TOKEN_SUMMARY_FILE}"
    )



    # ==========================================
    # MERGE BACK BY ACCOUNT NAME
    # ==========================================

    llm_results_indexed = llm_results.set_index(
        "Account Name",
        drop=False
    )


    for col in llm_results_indexed.columns:

        if col == "Account Name":
            continue

        llm_accounts[col] = llm_accounts["Account Name"].map(
            llm_results_indexed[col]
        )



    llm_accounts = llm_accounts.loc[
        :,
        ~llm_accounts.columns.duplicated()
    ]


    return llm_accounts
