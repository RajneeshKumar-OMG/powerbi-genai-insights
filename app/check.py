import os
from dotenv import load_dotenv

load_dotenv()

print(os.getenv("GEMINI_API_KEY"))
print(os.getenv("AWS_REGION"))
print(os.getenv("SNOWFLAKE_SECRET_NAME"))