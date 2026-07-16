import pandas as pd
import time
import os

from datetime import datetime, timezone

from modules.llm_validator import validate_account


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
                llm_results["llm_model"].iloc[0],

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
                int(total_tokens / count),

            "input_cost_usd":
                round(input_cost,4),

            "output_cost_usd":
                round(output_cost,4),

            "total_cost_usd":
                round(total_cost,4),

            "average_cost_per_account":
                round(total_cost / count,4)
        }]
    )



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



    # ==========================================
    # USE CHECKPOINT IF AVAILABLE
    # ==========================================

    if os.path.exists(
        LLM_RESULTS_FILE
    ):

        print(
            "Existing LLM results found."
        )

        print(
            "Skipping Bedrock calls."
        )


        llm_results = pd.read_excel(
            LLM_RESULTS_FILE
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


            result["source_index"] = idx


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
    # MERGE BACK BY INDEX
    # ==========================================

    llm_results = llm_results.set_index(
        "source_index"
    )


    for col in llm_results.columns:

        llm_accounts.loc[
            llm_results.index,
            col
        ] = llm_results[col]



    llm_accounts = llm_accounts.loc[
        :,
        ~llm_accounts.columns.duplicated()
    ]


    return llm_accounts
