import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = os.environ.get('api-url')
access_token = os.environ.get('access-token')

def get_completion(context: str) -> str:
    """Get code completion from the model"""
    url = API_URL + "/completion"
    data = {"accessToken": access_token, "context": context}
    response = requests.post(url, data=data)
    return response.text