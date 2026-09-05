from gemini_client import ask_gemini
import time

from snowflake_writer import (
    get_request_status,
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

        try:

            current_status = get_request_status(request_id)

            print("Current Snowflake status:", current_status)

            if current_status == "Completed":

                print(
                    f"Request {request_id} already completed. "
                    "Skipping duplicate message."
                )

                try:
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"]
                    )

                    print("Duplicate message deleted.")

                except Exception as delete_error:

                    print("\n========== SQS DELETE ERROR ==========\n")
                    print(type(delete_error))
                    print(delete_error)

                continue

            print("\n========== REQUEST ID DEBUG ==========")
            print("Request ID received from SQS:", request_id)
            print("Full SQS message:")
            print(json.dumps(body, indent=4))
            print("======================================\n")

            rows = body.get("rows", [])

            prompt_type = body.get(
                "prompt_type",
                "General"
            )

            user_prompt = body.get(
                "user_prompt",
                ""
            )

            if prompt_type == "Custom Prompt" and user_prompt:
                prompt_to_send = user_prompt
            else:
                prompt_to_send = prompt_type

            print("\nPrompt Type:")
            print(prompt_type)

            print("\nUser Prompt:")
            print(user_prompt)

            print("\nPrompt being sent to Gemini:")
            print(prompt_to_send)

            print("\n========================================")
            print("Prompt Type:")
            print(prompt_type)

            print("\nRows Received:")
            print(json.dumps(rows, indent=4))

            write_generating_status(
                request_id=request_id,
                prompt_type=prompt_type,
                prompt_text=prompt_to_send,
                rows=rows,
                user_prompt=user_prompt
            )

            start = time.time()

            ai_response = ask_gemini(
                prompt_type,
                rows,
                user_prompt
            )

            response_time_ms = int(
                (time.time() - start) * 1000
            )

            print("\n========== AI RESPONSE ==========\n")
            print(ai_response)

            if (
                not ai_response
                or "server busy" in ai_response.lower()
                or "gemini unavailable" in ai_response.lower()
            ):

                raise RuntimeError(
                    f"Invalid Gemini response: {ai_response}"
                )

            print("\nWriting response to Snowflake...")

            write_ai_response(
                request_id=request_id,
                prompt_type=prompt_type,
                prompt_text=prompt_to_send,
                rows=rows,
                ai_response=ai_response,
                response_source="Gemini",
                response_time_ms=response_time_ms,
                status="Completed",
                user_prompt=user_prompt
            )

            print("Snowflake write completed.")

        except Exception as processing_error:

            print("\n========== PROCESSING ERROR ==========\n")
            print(type(processing_error))
            print(processing_error)

            try:

                update_failed_status(
                    request_id=request_id,
                    error_message=str(processing_error)
                )

            except Exception as sf_error:

                print("Couldn't update failed status")
                print(sf_error)

            continue

        # Callback is intentionally outside the processing
        # try/except because Snowflake already contains
        # the authoritative Completed result.

        try:

            send_ai_response(
                request_id=request_id,
                status="Completed",
                response=ai_response,
                response_source="Gemini",
                response_time_ms=response_time_ms,
                user_prompt=user_prompt
            )

        except Exception as callback_error:

            print("\n========== CALLBACK ERROR ==========\n")
            print(type(callback_error))
            print(callback_error)

        # SQS deletion is also separate from AI processing.
        # If deletion fails, the message may be delivered again.
        # The duplicate check will prevent Gemini from running again.

        try:

            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=message["ReceiptHandle"]
            )

            print("\nMessage Deleted")

        except Exception as delete_error:

            print("\n========== SQS DELETE ERROR ==========\n")
            print(type(delete_error))
            print(delete_error)