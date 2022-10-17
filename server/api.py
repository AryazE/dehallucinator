import os
import server.model as model
from dotenv import load_dotenv
from flask import Flask, request

app = Flask(__name__)

load_dotenv()
access_token = os.environ.get('access-token')

@app.route("/completion", methods=["GET", "POST"])
def completion():
    if request.method == "POST" and request.form['accessToken'] == access_token:
        return model.get_completion(request.form['context'])
    else:
        return "Error\n"


