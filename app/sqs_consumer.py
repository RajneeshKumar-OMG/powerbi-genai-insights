from gemini_client import ask_gemini
import time

from snowflake_writer import (
    write_generating_status,
    write_ai_response,
    update_failed_status
)


from power_automate_client import send_ai_response

import boto3
import json

QUEUE_URL = "https://sqs.ap-south-1.amazonaws.com/334602886562/powerbi-ai-queue"

sqs = boto3.client(
    "sqs",
    region_name="ap-south-1"
)

print("Polling SQS...")

while True:

    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])

    if not messages:
        print("Polling SQS...")
        continue

    for message in messages:

        body = json.loads(message["Body"])

        request_id = body.get("request_id")

        rows = body.get("rows", [])

        prompt_type = body.get(
                                    "prompt_type",
                                    "General"
                                )

        print("\n========================================")
        print("Prompt Type:")
        print(prompt_type)

        print("\nRows Received:")
        print(json.dumps(rows, indent=4))

        write_generating_status(

            request_id=request_id,

            prompt_type=prompt_type,

            prompt_text=prompt_type,

            rows=rows,

            user_prompt=prompt_type

        )

        try:

            start = time.time()

            ai_response = ask_gemini(
                prompt_type,
                rows
            )

            response_time_ms = int(
                (time.time() - start) * 1000
            )

            print("\n========== AI RESPONSE ==========\n")
            print(ai_response)

            if (
                ai_response
                and "server busy" not in ai_response.lower()
                and "gemini unavailable" not in ai_response.lower()
            ):

                print("\nWriting response to Snowflake...")

                try:

                    write_ai_response(
                        request_id=request_id,
                        prompt_type=prompt_type,
                        prompt_text=prompt_type,
                        rows=rows,
                        ai_response=ai_response,
                        response_source="Gemini",
                        response_time_ms=response_time_ms,
                        status="Completed",
                        user_prompt=prompt_type
                    )

                    print("Snowflake write completed.")

                    send_ai_response(

                        request_id=request_id,

                        status="Completed",

                        response=ai_response,

                        response_source="Gemini",

                        response_time_ms=0,

                        user_prompt=prompt_type

                    )

                except Exception as sf_error:

                    print("\n========== SNOWFLAKE ERROR ==========\n")
                    print(type(sf_error))
                    print(sf_error)

            else:

                print("Skipping Snowflake write.")

            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=message["ReceiptHandle"]
            )

            print("\nMessage Deleted")

        except Exception as gemini_error:

            print("\n========== GEMINI ERROR ==========\n")
            print(type(gemini_error))
            print(gemini_error)

            try:

                update_failed_status(
                    request_id=request_id,
                    error_message=str(gemini_error)
                )

            except Exception as sf_error:

                print("Couldn't update failed status")
                print(sf_error)