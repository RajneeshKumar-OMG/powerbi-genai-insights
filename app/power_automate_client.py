import os
import requests

from dotenv import load_dotenv

load_dotenv()

FLOW_URL = os.getenv("POWER_AUTOMATE_CALLBACK_URL")


def send_ai_response(
    request_id,
    status,
    response,
    response_source,
    response_time_ms,
    user_prompt
):

    payload = {

        "request_id": request_id,
        "status": status,
        "response": response,
        "response_source": response_source,
        "response_time_ms": response_time_ms,
        "user_prompt": user_prompt

    }

    r = requests.post(
        FLOW_URL,
        json=payload,
        timeout=30
    )

    print("Power Automate Status:", r.status_code)
    print(r.text)

    r.raise_for_status()