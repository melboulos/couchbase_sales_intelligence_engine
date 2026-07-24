# =====================================================
# LLM CLIENT
# Couchbase Sales Intelligence Agent
#
# Architecture:
#
# Deterministic Gate
#        |
#        |
#        v
# Single LLM Intelligence Generation
#
# Responsibilities:
#
# - Send prompt to AWS Bedrock
# - Force JSON output
# - Parse JSON response
# - Capture token usage
# - Return structured result
#
# Does NOT:
#
# - qualify accounts
# - score accounts
# - validate sales logic
# - create business rules
#
# =====================================================


import boto3
import json
import re



# =====================================================
# CONFIG
# =====================================================


BEDROCK_REGION = "us-east-1"


MODEL_ID = (
    "meta.llama3-70b-instruct-v1:0"
)



# =====================================================
# BEDROCK CLIENT
# =====================================================


client = boto3.client(

    "bedrock-runtime",

    region_name=BEDROCK_REGION

)



# =====================================================
# JSON EXTRACTION
# =====================================================


def extract_json(text):


    if not text:


        raise ValueError(

            "Empty LLM response"

        )



    text = text.strip()



    #
    # Remove markdown wrappers
    #

    if "```json" in text:


        text = (

            text

            .split(
                "```json",
                1
            )[1]

            .split(
                "```",
                1
            )[0]

        )



    elif "```" in text:


        text = (

            text

            .split(
                "```",
                1
            )[1]

            .split(
                "```",
                1
            )[0]

        )



    text = text.strip()



    #
    # Extract JSON object
    #

    match = re.search(

        r"\{.*\}",

        text,

        re.DOTALL

    )



    if match:


        text = match.group(0)



    return json.loads(

        text

    )



# =====================================================
# CALL LLM
# =====================================================


def call_llm(prompt):


    if not isinstance(

        prompt,

        str

    ):


        raise TypeError(

            "call_llm expects string prompt"

        )



    formatted_prompt = f"""

<|begin_of_text|>

<|start_header_id|>user<|end_header_id|>


{prompt}


SYSTEM REQUIREMENTS:

Return ONLY valid JSON.

No markdown.

No explanation.

No additional text.


<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>

"""



    response = client.invoke_model(


        modelId=MODEL_ID,


        body=json.dumps(

            {


                "prompt":

                    formatted_prompt,


                "max_gen_len":

                    1500,


                "temperature":

                    0,


                "top_p":

                    0.5


            }

        ),


        contentType=

            "application/json",


        accept=

            "application/json"


    )



    response_body = json.loads(

        response["body"].read()

    )



    raw_text = response_body.get(

        "generation",

        ""

    )



    input_tokens = response_body.get(

        "prompt_token_count",

        0

    )



    output_tokens = response_body.get(

        "generation_token_count",

        0

    )



    #
    # Parse JSON
    #

    try:


        parsed = extract_json(

            raw_text

        )


        if not isinstance(

            parsed,

            dict

        ):


            raise ValueError(

                "LLM response must be JSON object"

            )



    except Exception as e:


        parsed = {


            "llm_parse_error":

                str(e),


            "llm_raw_response":

                raw_text


        }



    #
    # Attach metadata
    #

    parsed.update(

        {


            "llm_input_tokens":

                input_tokens,


            "llm_output_tokens":

                output_tokens,


            "llm_total_tokens":

                (

                    input_tokens

                    +

                    output_tokens

                ),


            "llm_model":

                MODEL_ID


        }

    )



    return parsed
