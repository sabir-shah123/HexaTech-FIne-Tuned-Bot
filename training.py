from gpt_index import SimpleDirectoryReader, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI

def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 256
    max_chunk_overlap = 0.2  #Note : Use float value between 0 and 1
    chunk_size_limit = 600
    bot_name = 'HexaTech' 
    company_name = 'HTS'
    introduction = f"{bot_name} is a chatbot that can answer questions about {company_name}."
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)
    # Define LLM to train the file
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0, model_name="text-davinci-003", max_tokens=num_outputs))
    documents = SimpleDirectoryReader(directory_path).load_data()
    index = GPTSimpleVectorIndex(documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index.save_to_disk('index.json')
    return index

if __name__ == '__main__':
    training_folder = 'data'
    if not os.path.exists(training_folder):
        print("Training folder does not exist. Please create a folder named " + training_folder + " and add training files to it.")
        exit()
    index = construct_index(training_folder)
    index.save_to_disk('index.json')
