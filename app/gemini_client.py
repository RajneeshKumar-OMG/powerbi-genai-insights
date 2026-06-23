from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def ask_gemini(question):

    dummy_data = """
    Campaign A Spend = 12000
    Campaign A Target = 10000

    Campaign B Spend = 7000
    Campaign B Target = 10000
    """

    prompt = f"""
    You are a marketing analyst.

    Dataset:
    {dummy_data}

    Question:
    {question}

    Provide a short business answer.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text
