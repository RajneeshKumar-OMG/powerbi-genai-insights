import boto3

queue_url = "https://sqs.ap-south-1.amazonaws.com/334602886562/powerbi-ai-queue"

sqs = boto3.client(
    "sqs",
    region_name="ap-south-1"
)

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1
)

print(response)