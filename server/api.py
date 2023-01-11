import os
from dotenv import load_dotenv
from flask import Flask, request

app = Flask(__name__)

load_dotenv()
access_token = os.environ.get('access-token')

@app.route("/codegen", methods=["GET", "POST"])
def codegen():
    if request.method == "POST" and request.form['accessToken'] == access_token:
        import server.codegen as codegen
        return codegen.get_completion(request.form['context'])
    else:
        return "Error\n"

@app.route("/polycoder", methods=["GET", "POST"])
def polycoder():
    if request.method == "POST" and request.form['accessToken'] == access_token:
        import server.polycoder as polycoder
        return polycoder.get_completion(request.form['context'])
    else:
        return "Error\n"