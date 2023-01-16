import os
import requests
import openai
from dotenv import dotenv_values
import time

env_vars = dotenv_values('.env')
API_URL = env_vars['api-url']
access_token = env_vars['access-token']
openai.api_key = env_vars['openai-api-key']
print(env_vars)

class Completion:
    def __init__(self):
        self.last_time = time.monotonic()

    def get_completion(self, model: str, context: str) -> str:
        """Get code completion from the model"""
        if model == "CodeGen":
            url = API_URL + "/codegen"
            data = {"accessToken": access_token, "context": context}
            response = requests.post(url, data=data)
            return response.text
        elif model == "PolyCoder":
            url = API_URL + "/polycoder"
            data = {"accessToken": access_token, "context": context}
            response = requests.post(url, data=data)
            return response.text
        elif model == "Codex":
            now = time.monotonic()
            if now - self.last_time < 6: # This is done to prevent going over the API rate limit
                time.sleep(6 - (now - self.last_time))
            res = openai.Completion.create(
                engine="code-cushman-001",
                prompt=context,
                temperature=0,
                max_tokens=500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=["\n\n\n", "def ", "class "]
            ).choices[0].text
            self.last_time = time.monotonic()
            return res