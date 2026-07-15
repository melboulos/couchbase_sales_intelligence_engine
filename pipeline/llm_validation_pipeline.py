import pandas as pd
import time
import os

from datetime import datetime, timezone

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from modules.llm_validator import validate_account



# =====================================================
# TOKEN COST CONFIGURATION
# =====================================================

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



# =====================================================
# TOKEN SUMMARY
# =====================================================

def generate_token_summary(
    llm_results
):

    if len(llm_results) == 0:
        return pd.DataFrame()



    input_tokens = int(
        llm_results[
            "llm_input_tokens"
        ].sum()
    )


    output_tokens = int(
        llm_results[
            "llm_output_tokens"
        ].sum()
    )


    total_tokens = int(
        llm_results[
            "llm_total_tokens"
        ].sum()
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


    count = len(
        llm_results
    )


    return pd.DataFrame(
        [
            {
                "llm_run_id":
                    llm_results[
                        "llm_run_id"
                    ].iloc[0],

                "llm_model":
                    llm_results[
                        "llm_model"
                    ].iloc[0],

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
                    int(
                        total_tokens /
                        count
                    ),

                "input_cost_usd":
                    round(
                        input_cost,
                        4
                    ),

                "output_cost_usd":
                    round(
                        output_cost,
                        4
                    ),

                "total_cost_usd":
                    round(
                        total_cost,
                        4
                    ),

                "average_cost_per_account":
                    round(
                        total_cost /
                        count,
                        4
                    )
            }
        ]
    )



# =====================================================
# SINGLE LLM CALL
# =====================================================

def run_llm_validation(
    row
):

    account_name = row.get(
        "Account Name",
        "Unknown"
    )


    result = validate_account(
        row
    )


    return (
        account_name,
        result
    )



# =====================================================
# MAIN VALIDATION PIPELINE
# =====================================================

def validate_accounts(
    accounts
):


    print(
        "\nStarting LLM validation..."
    )


    tier1_accounts = accounts[
        accounts[
            "priority_tier"
        ]
        ==
        "Tier 1 Strategic"
    ].copy()



    total = len(
        tier1_accounts
    )


    print(
        f"LLM candidates: {total}"
    )



    if total == 0:
        return accounts



    # =====================================================
    # LOAD EXISTING CHECKPOINT
    # =====================================================

    if os.path.exists(
        LLM_RESULTS_FILE
    ):


        print(
            "\nExisting LLM results found."
        )


        print(
            "Skipping Bedrock calls."
        )


        llm_results = pd.read_excel(
            LLM_RESULTS_FILE
        )



    else:


        # =====================================================
        # RUN LLM THREADS
        # =====================================================

        MAX_WORKERS = 5


        print(
            f"Using {MAX_WORKERS} LLM workers"
        )


        results = []


        start_time = time.time()



        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:


            futures = []


            for _, row in tier1_accounts.iterrows():

                futures.append(
                    executor.submit(
                        run_llm_validation,
                        row
                    )
                )



            completed = 0



            for future in as_completed(
                futures
            ):


                account_name, result = (
                    future.result()
                )


                results.append(
                    result
                )


                completed += 1



                elapsed = (
                    time.time()
                    -
                    start_time
                )


                avg_time = (
                    elapsed /
                    completed
                )


                remaining = (
                    avg_time *
                    (
                        total -
                        completed
                    )
                )


                print(
                    f"[{completed}/{total}] "
                    f"{account_name} | "
                    f"Elapsed: {elapsed/60:.1f} min | "
                    f"Avg: {avg_time:.2f}s | "
                    f"ETA: {remaining/60:.1f} min"
                )



        # =====================================================
        # CREATE RESULTS DATAFRAME
        # =====================================================

        llm_results = pd.DataFrame(
            results
        )


        llm_results = llm_results.loc[
            :,
            ~llm_results.columns.duplicated()
        ]



        # =====================================================
        # SAVE CHECKPOINT BEFORE ANY MERGE
        # =====================================================

        llm_results.to_excel(
            LLM_RESULTS_FILE,
            index=False
        )


        print(
            f"\nSaved LLM checkpoint: {LLM_RESULTS_FILE}"
        )



    # =====================================================
    # TOKEN COST REPORT
    # =====================================================

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



    # =====================================================
    # CLEAN BEFORE MERGE
    # =====================================================

    tier1_accounts = tier1_accounts.loc[
        :,
        ~tier1_accounts.columns.duplicated()
    ]


    llm_results = llm_results.loc[
        :,
        ~llm_results.columns.duplicated()
    ]



    # =====================================================
    # MERGE LLM RESULTS
    # =====================================================

    tier1_accounts = pd.concat(
        [
            tier1_accounts.reset_index(drop=True),
            llm_results.reset_index(drop=True)
        ],
        axis=1
    )


    tier1_accounts = tier1_accounts.loc[
        :,
        ~tier1_accounts.columns.duplicated()
    ]



    # =====================================================
    # NON TIER 1
    # =====================================================

    non_tier1 = accounts[
        accounts[
            "priority_tier"
        ]
        !=
        "Tier 1 Strategic"
    ].copy()


    non_tier1 = non_tier1.loc[
        :,
        ~non_tier1.columns.duplicated()
    ]



    # =====================================================
    # FINAL MERGE
    # =====================================================

    final = pd.concat(
        [
            tier1_accounts,
            non_tier1
        ],
        ignore_index=True
    )


    final = final.loc[
        :,
        ~final.columns.duplicated()
    ]


    return final
