from google import genai
from google.genai import types
from typing import Dict, Any
import os
import dotenv

dotenv.load_dotenv()

client = genai.Client(
  api_key=os.getenv("GEMINI_API_KEY"))

async def analyze_gmgn_data(gmgn_data: str) -> Dict[str, Any]:
  system_instruction = """You are an expert in analyzing GMGN.ai data.
  You are given a GMGN.ai data of a token.
  Analyze this token data and provide detailed insights in the following areas:

  1. Top Holders Analysis:
     - Top 10 holder percentages
     - Dev wallet status and transactions
     - Sniper activity and counts
     - Blue chip holder percentage

  2. Security Analysis:
     - Contract verification status
     - Honeypot check results
     - Buy/Sell taxes
     - Risk assessment score
     - Renounced status

  Format the response as a clean JSON object without any markdown formatting or additional headers. Include all available metrics and insights from the provided data."""

  model = "gemini-2.5-flash"
  
  prompt = f"""{system_instruction}

  Raw Data:
  {gmgn_data}"""
  
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text=prompt),
      ],
    ),
  ]
  
  generate_content_config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
      thinking_budget=-1,
    ),
  )

  response_text = ""
  for chunk in client.models.generate_content_stream(
    model=model,
    contents=contents,
    config=generate_content_config,
  ):
    response_text += chunk.text
  
  return {
    "analysis": response_text,
    "status": "success"
  }


# USAGE:
# import asyncio

# async def main():
#     result = await analyze_gmgn_data("""<GMGN DATA>""")
#     print(result)

# if __name__ == "__main__":
#     asyncio.run(main())