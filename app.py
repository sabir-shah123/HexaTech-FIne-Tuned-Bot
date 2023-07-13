from flask import Flask, render_template, request, session
from flask_wtf.csrf import CSRFProtect
import json
import os
import openai
import PyPDF2
from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI


app = Flask(__name__)

app.secret_key =   os.urandom(24)
csrf = CSRFProtect(app)
# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.environ["OPENAI_API_KEY"]

#dt.load_dotenv()
#openai.api_key = os.getenv("OPENAI_API_KEY")

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()

def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 256
    max_chunk_overlap = 0.2  #Note : Use float value between 0 and 1
    chunk_size_limit = 600
    # company name and bot names from .env file
    bot_name = 'HexaTech' 
    #os.getenv("BOT_NAME")
    company_name = 'HTS'
    # os.getenv("COMPANY_NAME")
    
    introduction = f"{bot_name} is a chatbot that can answer questions about {company_name}."
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    # Define LLM to train the file
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=num_outputs))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk('index.json')
    return index

@app.route('/')
def index():
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
@csrf_protect
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
        company_name = 'HTS'#os.getenv("COMPANY_NAME")
        replace_with = 'CRM' #os.getenv("TO_REPLACE_KEYWORD")
        conversation_history = session['conversation_history']
        conversation_history += prompt + "\nCRM Bot: " + response.response + "\n"
        session['conversation_history'] = conversation_history
        response_text = response.response
        if 'CRM' in response_text:
            response_text = response_text.replace(replace_with, company_name)
        if 'GoHighLevel' in response_text:
            response_text = response_text.replace('GoHighLevel', '')
        conversation_history += prompt + "\nCRM Bot: " + response_text + "\n"
        return response_text
    else:
        return "I'm sorry, I couldn't generate a response."

if __name__ == '__main__':
    training_folder= 'data'
    #os.getenv("TRAINING_FOLDER")
    if not os.path.exists(training_folder):
        print("Training folder does not exist. Please create a folder named " + training_folder + " and add training files to it.")
        exit()
    print ("Constructing index..." + training_folder)
    index = construct_index(training_folder)
    app.run(debug=False)
