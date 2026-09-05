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


    cur = conn.cursor()

    try:
        cur.execute(
            "ALTER SESSION SET TIMEZONE = 'Asia/Kolkata'"
        )
    finally:
        cur.close()

    

    print("Connected to Snowflake")

    return conn

def get_request_status(request_id):

    conn = get_snowflake_connection()

    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT STATUS
            FROM AI_RESPONSE
            WHERE REQUEST_ID = %s
            ORDER BY CREATED_AT DESC
            LIMIT 1
            """,
            (request_id,)
        )

        result = cur.fetchone()

        if result:
            return result[0]

        return None

    finally:

        cur.close()
        conn.close()

def write_generating_status(
    request_id,
    prompt_type,
    prompt_text,
    rows,
    user_prompt
):

    conn = get_snowflake_connection()

    cur = conn.cursor()

    try:

        # Check whether this request already exists
        cur.execute(
            """
            SELECT COUNT(*)
            FROM AI_RESPONSE
            WHERE REQUEST_ID = %s
            """,
            (request_id,)
        )

        existing_count = cur.fetchone()[0]

        if existing_count > 0:

            cur.execute(
                """
                UPDATE AI_RESPONSE
                SET
                    PROMPT_TYPE = %s,
                    PROMPT_TEXT = %s,
                    INPUT_DATA = PARSE_JSON(%s),
                    STATUS = 'Generating',
                    USER_PROMPT = %s
                WHERE REQUEST_ID = %s
                """,
                (
                    prompt_type,
                    prompt_text,
                    json.dumps(rows),
                    user_prompt,
                    request_id
                )
            )

            print("Existing request reset to Generating")

        else:

            cur.execute(
                """
                INSERT INTO AI_RESPONSE
                (
                    REQUEST_ID,
                    PROMPT_TYPE,
                    PROMPT_TEXT,
                    INPUT_DATA,
                    STATUS,
                    USER_PROMPT
                )

                SELECT
                    %s,
                    %s,
                    %s,
                    PARSE_JSON(%s),
                    'Generating',
                    %s
                """,
                (
                    request_id,
                    prompt_type,
                    prompt_text,
                    json.dumps(rows),
                    user_prompt
                )
            )

            print("New Generating status written")

        conn.commit()

    finally:

        cur.close()
        conn.close()


def update_failed_status(
    request_id,
    error_message
):

    conn = get_snowflake_connection()

    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE AI_RESPONSE
            SET
                STATUS = 'Failed',
                AI_RESPONSE = %s
            WHERE REQUEST_ID = %s
            """,
            (
                error_message[:5000],
                request_id
            )
        )

        conn.commit()

        print("Failed status written")

    finally:

        cur.close()
        conn.close()


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
            UPDATE AI_RESPONSE
            SET
                AI_RESPONSE = %s,
                RESPONSE_SOURCE = %s,
                RESPONSE_TIME_MS = %s,
                STATUS = %s
            WHERE REQUEST_ID = %s
            """,
            (
                ai_response,
                response_source,
                response_time_ms,
                status,
                request_id
            )
        )

        conn.commit()

        print("AI Response Updated in Snowflake")

    finally:

        cur.close()
        conn.close()