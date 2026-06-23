from gemini_client import ask_gemini

import boto3
import json

QUEUE_URL = "https://sqs.ap-south-1.amazonaws.com/334602886562/powerbi-ai-queue"

sqs = boto3.client(
    "sqs",
    region_name="ap-south-1"
)

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

        question = body["question"]

        print(f"Question Received: {question}")

        try:
            response = ask_gemini(question)

            print("\nAI RESPONSE:")
            print(response)

        except Exception as e:
            print("\nGEMINI ERROR:")
            print(e)

            response = "Gemini unavailable"

        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=message["ReceiptHandle"]
        )

        print("Message Deleted")