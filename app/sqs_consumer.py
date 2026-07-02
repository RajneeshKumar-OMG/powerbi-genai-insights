from gemini_client import ask_gemini

from snowflake_writer import write_ai_response

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

        try:

            ai_response = ask_gemini(
                prompt_type,
                rows
            )

            print("\n========== AI RESPONSE ==========\n")
            print(ai_response)

            if (
                ai_response
                and "server busy" not in ai_response.lower()
                and "gemini unavailable" not in ai_response.lower()
                and "error" not in ai_response.lower()
            ):

                print("\nWriting response to Snowflake...")

                try:

                    write_ai_response(
                        request_id=request_id,
                        prompt_type=prompt_type,
                        prompt_text=prompt_type,
                        rows=rows,
                        ai_response=ai_response
                    )

                    print("Snowflake write completed.")

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