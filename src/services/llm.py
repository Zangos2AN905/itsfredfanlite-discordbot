import asyncio

import aiohttp
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, OPENROUTER_API_KEY

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


async def request_openrouter_script(prompt: str, model_id: str) -> str:
    """Routes script generation request to Gemini or OpenRouter."""
    if model_id.startswith("gemini-"):
        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ]
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=safety_settings,
                temperature=0.7,
            ),
        )
        return response.text.strip() if response.text else ""

    else:  # OpenRouter API
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    err_body = await resp.text()
                    raise Exception(f"OpenRouter LLM Error ({resp.status}): {err_body}")
