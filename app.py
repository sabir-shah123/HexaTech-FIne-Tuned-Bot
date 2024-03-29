from flask import Flask, render_template, request, session, jsonify
import json
import os
import openai
import PyPDF2
from gpt_index import (
    SimpleDirectoryReader,
    GPTSimpleVectorIndex,
    LLMPredictor,
    PromptHelper,
)
from langchain import OpenAI
import requests
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)
# Set the OpenAI API key


def open_file(filepath):
    with open(filepath, "r", encoding="utf-8") as infile:
        return infile.read()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


def setClientEnvironment(data):
    # set the client environment
    os.environ["OPENAI_API_KEY"] = data["key"]
    openai.api_key = os.environ["OPENAI_API_KEY"]
    os.environ["DOMAIN"] = data["domain"]
    os.environ["COMPANY_NAME"] = data["company_name"]
    os.environ["TO_REPLACE_KEYWORD"] = data["to_replace_keyword"]
    os.environ["BOT_NAME"] = data["bot_name"]


@app.route("/domain_auth", methods=["POST"])
@csrf.exempt
def domain_auth():
    parent_url = request.json["parentURL"]
    print(parent_url)
    # API call to get the domain name
    domain_name = "http://propertyqualification.hexatechsolution.com/api/domain-check"
    # get data
    data = {"parentURL": parent_url}
    # header user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
    }
    response = requests.get(domain_name, data=json.dumps(data), headers=headers)
    try:
        response_data = response.json()
        key = response_data["key"]
        # set the client environment
        setClientEnvironment(response_data)
        return jsonify(response_data)
    except ValueError as e:
        error_message = f"Error decoding JSON: {str(e)}"
        return jsonify({"error": error_message}), 500


@app.route("/ask", methods=["POST"])
def ask():
    query = request.form["query"]
    response = ask_bot(query)
    if response is not None:
        return response
    else:
        return "I'm sorry, I couldn't generate a response."


@app.route("/send_prompt", methods=["POST"])
@csrf.exempt
def send_prompt():
    prompt = json.loads(request.data)["prompt"]
    # check the os environment variable is set or not
    if "DOMAIN" not in os.environ:
        return jsonify({"error": "Please set the domain name"}), 500
    folder = "clients/" + os.environ["DOMAIN"].lower().replace("https://", "").replace(
        "http://", ""
    ).replace("www.", "")
    file_path = folder + "/index.json"
    response = ask_bot(prompt)
    return response


def ask_bot(prompt, input_index="index.json"):
    if "conversation_history" not in session:
        session["conversation_history"] = ""
    index = GPTSimpleVectorIndex.load_from_disk(input_index)
    response = index.query(prompt)

    if response is not None and response.response is not None:
        company_name = os.environ["COMPANY_NAME"]
        replace_with = os.environ["TO_REPLACE_KEYWORD"]
        conversation_history = session["conversation_history"]
        conversation_history += prompt + "\nCRM Bot: " + response.response + "\n"
        session["conversation_history"] = conversation_history
        response_text = response.response
        if "CRM" in response_text:
            response_text = response_text.replace(replace_with, company_name)
        if "GoHighLevel" in response_text:
            response_text = response_text.replace("GoHighLevel", "")
        conversation_history += prompt + "\nCRM Bot: " + response_text + "\n"
        return response_text
    else:
        return "I'm sorry, I couldn't generate a response."


if __name__ == "__main__":
    app.run(debug=True)
