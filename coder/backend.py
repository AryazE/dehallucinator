from typing import List
import requests
import openai
from dotenv import dotenv_values
import time

env_vars = dotenv_values('.env')
API_URL = env_vars['api-url']
access_token = env_vars['access-token']
openai.api_key = env_vars['openai-api-key']

class Completion:
    def __init__(self):
        self.last_time = time.monotonic()

    def get_completion(self, model: str, context: str, **kwargs) -> List[str]:
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
            if 'k' in kwargs:
                k = kwargs['k']
                del kwargs['k']
                if k > 1:
                    temperature = 0.2
                else:
                    temperature = 0
            else:
                k = 1
                temperature = 0
            params = {
                'engine': 'code-cushman-001',
                'prompt': context,
                'n': k,
                'temperature': temperature,
                'max_tokens': 500,
                'stop': ['\n\n\n', 'def ', 'async def ', 'class ']
            }
            params.update(kwargs)
            now = time.monotonic()
            delay = 2*k + 3
            if now - self.last_time < delay: # This is done to prevent going over the API rate limit
                time.sleep(delay - (now - self.last_time))
            while True:
                try:
                    res = [i.text for i in openai.Completion.create(**params).choices]
                    break
                except Exception as e:
                    print(e)
                    if isinstance(e, openai.error.RateLimitError):
                        print('Rate limit error, waiting 60 seconds')
                        time.sleep(60)
                    else:
                        raise e
            self.last_time = time.monotonic()
            return res
        elif model == "CodeT5":
            url = "https://api-inference.huggingface.co/models/Salesforce/codet5-large"
            headers = {"Authorization": f"Bearer {env_vars['hf-codet5-api-key']}"}

            def query(payload):
                response = requests.post(url, headers=headers, json=payload)
                return response.json()
                
            output = query({
                "inputs": context,
            })
            return output