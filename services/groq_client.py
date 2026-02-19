import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Load .env manually here (safe for Docker, Gunicorn, Django)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path, override=True)


def get_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    return Groq(api_key=api_key)


def call_llama(prompt, max_tokens=300):
    client = get_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )

    return response.choices[0].message.content



    return response.choices[0].message["content"]
