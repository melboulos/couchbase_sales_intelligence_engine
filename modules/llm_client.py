import boto3
import json


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
# CALL LLM
# =====================================================

def call_llm(prompt):


    response = client.invoke_model(

        modelId=MODEL_ID,

        body=json.dumps(
            {
                "prompt": prompt,

                "max_gen_len": 1024,

                "temperature": 0.1,

                "top_p": 0.9
            }
        ),

        contentType="application/json",

        accept="application/json"

    )



    response_body = json.loads(
        response["body"].read()
    )



    text = response_body.get(
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



    return {


        "text":
            text,


        "input_tokens":
            input_tokens,


        "output_tokens":
            output_tokens,


        "total_tokens":
            (
                input_tokens
                +
                output_tokens
            ),


        "model_id":
            MODEL_ID

    }
