import os
import requests
import openai
from dotenv import load_dotenv
import time

last_time = time.time()
load_dotenv()
API_URL = os.environ.get('api-url')
access_token = os.environ.get('access-token')
openai.api_key = os.environ.get('openai-api-key')

def get_completion(model: str, context: str) -> str:
    """Get code completion from the model"""
    global last_time
    if model == "CodeGen":
        url = API_URL + "/completion"
        data = {"accessToken": access_token, "context": context}
        response = requests.post(url, data=data)
        return response.text
    elif model == "Codex":
        if time.time() - last_time < 4: # This is done to prevent going over the API rate limit
            time.sleep(4)
        last_time = time.time()
        return openai.Completion.create(
            engine="code-cushman-001",
            prompt=context,
            temperature=0,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n\n\n", "def ", "class "]
        ).choices[0].text