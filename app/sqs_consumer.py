from gemini_client import ask_gemini

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

        rows = body.get("rows", [])
        prompt_type = body.get("prompt_type", "General")

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

        except Exception as e:

            print("\n========== GEMINI ERROR ==========\n")
            print(e)

            ai_response = "Gemini unavailable."

        # Delete message only after processing
        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=message["ReceiptHandle"]
        )

        print("\nMessage Deleted")