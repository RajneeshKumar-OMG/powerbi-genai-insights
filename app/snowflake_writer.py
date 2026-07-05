import os
import json
import boto3
import snowflake.connector

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from dotenv import load_dotenv

load_dotenv()


def get_snowflake_connection():

    secret_name = os.getenv("SNOWFLAKE_SECRET_NAME")

    region = os.getenv("AWS_REGION")

    client = boto3.client(
        "secretsmanager",
        region_name=region
    )

    response = client.get_secret_value(
        SecretId=secret_name
    )

    secret = json.loads(
    response["SecretString"])

    print("Snowflake Secret Loaded")

    private_key = serialization.load_pem_private_key(
    secret["private_key"].encode(),
    password=None,
    backend=default_backend()
    )

    pkb = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    conn = snowflake.connector.connect(
        user=secret["user"],
        account=secret["account"],
        warehouse=secret["warehouse"],
        database=secret["database"],
        schema=secret["schema"],
        role=secret["role"],
        private_key=pkb
    )

    print("Connected to Snowflake")

    return conn

def write_ai_response(
    request_id,
    prompt_type,
    prompt_text,
    rows,
    ai_response,
    response_source,
    response_time_ms,
    status,
    user_prompt
):

    conn = get_snowflake_connection()

    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO AI_RESPONSE
            (
                REQUEST_ID,
                PROMPT_TYPE,
                PROMPT_TEXT,
                INPUT_DATA,
                AI_RESPONSE,
                RESPONSE_SOURCE,
                RESPONSE_TIME_MS,
                STATUS,
                USER_PROMPT
            )

            SELECT
                SELECT
                    %s,
                    %s,
                    %s,
                    PARSE_JSON(%s),
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
            """,
            (
                (
                    request_id,
                    prompt_type,
                    prompt_text,
                    json.dumps(rows),
                    ai_response,
                    "Gemini",
                    None,
                    "Completed",
                    prompt_text
                )
            )
        )

        conn.commit()

        print("AI Response Written to Snowflake")

    finally:

        cur.close()
        conn.close()