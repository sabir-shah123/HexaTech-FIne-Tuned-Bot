from flask import Flask, render_template, request, session
import json
import os
import openai
import PyPDF2
from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI

app = Flask(__name__)

app.secret_key =   os.urandom(24)

# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.environ["OPENAI_API_KEY"]

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def construct_index(directory_path):
    # Set maximum input size
    max_input_size = 4096
    # Set number of output tokens
    num_outputs = 256
    # Set maximum chunk overlap
    max_chunk_overlap = 0.2  # Updated: Use float value between 0 and 1
    # Set chunk size limit
    chunk_size_limit = 600
    #Bot introduction
    assistant_name =  "HexaBot"
    introduction = "The Chat is between a user and Hexabot about the GoHighLevel CRM"
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    # Define LLM
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=num_outputs))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk('index.json')
    return index

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    response = ask_bot(query)
    if response is not None:
        return response
    else:
        return "I'm sorry, I couldn't generate a response."

@app.route('/send_prompt', methods=['POST'])
def send_prompt():
    prompt = json.loads(request.data)['prompt']
    response = ask_bot(prompt)
    return response

def ask_bot(prompt, input_index='index.json'):
    if 'conversation_history' not in session:
        session['conversation_history'] = ""
    
    index = GPTSimpleVectorIndex.load_from_disk(input_index)
    response = index.query(prompt)
    
    if response is not None and response.response is not None:
        conversation_history = session['conversation_history']
        conversation_history += prompt + "\nHexaBot: " + response.response + "\n"
        session['conversation_history'] = conversation_history
        
        response_text = response.response
        replacements = [
            ('crm', 'JDFunnel'),
            ('gohighlevel', ' '),
            ('GoHighLevel', ''),
            ('Go High Level', ''),
            ('GHL', ''),
            ('ghl', ''),
            ('HL', '')
        ]

        if 'CRM' in response_text:
            response_text = response_text.replace('CRM', 'JDFunnel')
        if 'GoHighLevel' in response_text:
            response_text = response_text.replace('GoHighLevel', '')
        conversation_history += prompt + "\nHexaBot: " + response_text + "\n"
        return response_text
    else:
        return "I'm sorry, I couldn't generate a response."

if __name__ == '__main__':
    index = construct_index("data/")
    app.run(debug=True)
