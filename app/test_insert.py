from snowflake_writer import write_ai_response

write_ai_response(

    request_id="TEST123",

    prompt_type="Executive Summary",

    prompt_text="Executive Summary",

    rows=[
        {
            "Platform": "Pinterest",
            "Spend": 1000
        }
    ],

    ai_response="This is a test AI response."

)

print("Done")