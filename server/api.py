import os
from dotenv import load_dotenv
from flask import Flask, request

from server.codegen import CodeGen
from server.polycoder import PolyCoder
app = Flask(__name__)

load_dotenv()
access_token = os.environ.get('access-token')
codegen_model = CodeGen()
polycoder_model = PolyCoder()

@app.route("/codegen", methods=["GET", "POST"])
def codegen():
    if request.method == "POST" and request.form['accessToken'] == access_token:
        if polycoder_model.is_active():
            polycoder_model.unload_model()
        return codegen_model.get_completion(request.form['context'])
    else:
        return "Error\n"

@app.route("/polycoder", methods=["GET", "POST"])
def polycoder():
    if request.method == "POST" and request.form['accessToken'] == access_token:
        if codegen_model.is_active():
            codegen_model.unload_model()
        return polycoder_model.get_completion(request.form['context'])
    else:
        return "Error\n"