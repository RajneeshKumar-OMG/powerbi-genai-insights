from google import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def ask_gemini(prompt_type, rows):

    # Convert Power BI rows into readable JSON
    dataset = json.dumps(rows, indent=4)

    # -------------------------
    # Executive Summary
    # -------------------------

    if prompt_type == "Executive Summary":

        prompt = f"""
You are a Senior Marketing Analytics Consultant.

Below is campaign data exported from Power BI.

Dataset

{dataset}

Generate:

1. Executive Summary
2. Overall campaign performance
3. Highest spending campaigns
4. Platform level observations
5. Any unusual trends
6. Business recommendations

Keep the response concise and suitable for senior leadership.
"""

    # -------------------------
    # Budget Optimization
    # -------------------------

    elif prompt_type == "Budget Optimization":

        prompt = f"""
You are a Digital Marketing Budget Optimization Expert.

Dataset

{dataset}

Analyze the spend and provide:

1. Campaigns overspending
2. Campaigns underspending
3. Budget redistribution suggestions
4. Cost-saving opportunities
5. Optimization recommendations

Keep the response practical and business focused.
"""

    # -------------------------
    # QA Analysis
    # -------------------------

    elif prompt_type == "QA Analysis":

        prompt = f"""
You are a Marketing QA Analyst.

Dataset

{dataset}

Check for:

1. Missing values
2. Duplicate campaigns
3. Unexpected platform assignments
4. Abnormal spend values
5. Data quality issues
6. Validation recommendations

Return findings in bullet points.
"""

    # -------------------------
    # Risk Assessment
    # -------------------------

    elif prompt_type == "Risk Assessment":

        prompt = f"""
You are a Marketing Risk Analyst.

Dataset

{dataset}

Identify:

1. Campaigns that may overspend
2. Platform concentration risk
3. Budget allocation risks
4. Operational risks
5. Financial risks
6. Recommendations to reduce risk

Keep the response concise.
"""

    # -------------------------
    # Root Cause Analysis
    # -------------------------

    elif prompt_type == "Root Cause Analysis":

        prompt = f"""
You are a Marketing Performance Consultant.

Dataset

{dataset}

Analyze the data and identify:

1. Possible reasons for high spend
2. Possible reasons for low spend
3. Platform level issues
4. Campaign level observations
5. Root causes
6. Recommended corrective actions

Think step-by-step before answering.
"""

    # -------------------------
    # Default / Future Custom Prompt
    # -------------------------

    else:

        prompt = f"""
You are a Marketing Analytics Expert.

Dataset

{dataset}

Analyze the data and provide useful business insights.
"""
    
    print("Calling Gemini model: gemini-2.5-flash")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text