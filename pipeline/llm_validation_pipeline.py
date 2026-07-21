import pandas as pd
import time
import os

from datetime import datetime, timezone

from modules.sales_intelligence_pipeline import validate_account

LLM_INPUT_COST_PER_1K = 0.99
LLM_OUTPUT_COST_PER_1K = 0.99


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


        new_results = []

        for i, row in enumerate(rows_to_run):

            account_name = row.get(
                "Account Name",
                "Unknown"
            )

            print(
                f"[{i+1}/{len(rows_to_run)}] {account_name}"
            )

            result = validate_account(row)

            result["Account Name"] = account_name

            new_results.append(result)

            print(
                f"Completed {i+1}/{len(rows_to_run)}"
            )


        kept_df = (
            pd.DataFrame(already_done_rows)
            if already_done_rows
            else pd.DataFrame(columns=existing_results.columns)
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
            "Running sequential LLM validation..."
        )


        results = []


        start_time = time.time()


        for idx, row in llm_accounts.iterrows():

            account_name = row.get(
                "Account Name",
                "Unknown"
            )


            print(
                f"[{idx+1}/{total}] {account_name}"
            )


            result = validate_account(
                row
            )


            result["Account Name"] = account_name


            results.append(
                result
            )


            elapsed = (
                time.time()
                -
                start_time
            )


            print(
                f"Completed {idx+1}/{total} "
                f"Elapsed {elapsed:.1f}s"
            )



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
