import os,sys
sys.path.insert(0,".")
from openai import OpenAI

from transformers import AutoTokenizer
from codetiming import Timer
from pprint import pprint
from tqdm import tqdm

from codetiming import Timer
from pprint import pprint
from tqdm import tqdm
from langchain import PromptTemplate
from doc_dialog.prompts_openai import PROMPT_QA_SYSTEM, PROMPT_QA_USER


MODEL_ID = "hugging-quants/Meta-Llama-3.1-8B-Instruct-GPTQ-INT4"
TOKENIZER_REPO_ID = "hugging-quants/Meta-Llama-3.1-8B-Instruct-GPTQ-INT4"
class LLM:
    def __init__(self, verbose = False):
        self.verbose = verbose

        self.max_new_tokens = 1500
        self.context_length = 12000 #adjust based on available gpu memory
        self.max_input_tokens = self.context_length - self.max_new_tokens

        #get hostname of the host system
        hostname = os.environ["HOST_HOSTNAME"]
        self.client = OpenAI(base_url=f"http://{hostname}:8000/v1", api_key=os.getenv("VLLM_API_KEY", "-"))

        self.system_prompt = PROMPT_QA_SYSTEM
        user_prompt_template = PROMPT_QA_USER
        self.prompt_template = PromptTemplate(
            input_variables=["context", 
                            "question"],
            template=user_prompt_template
        )

        self.tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_REPO_ID)

    def get_prompt_length_in_tokens(self, prompt):
        """calculate the length of the prompt in tokes

        Args:
            prompt (_type_): prompt as string

        Returns:
            _type_: int indicating number of tokens
        """
        messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},                            
                ]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,

        )
        return len(inputs)


    def call(self, prompt):
        """calls the llm with the prompt

        Args:
            prompt (_type_): prompt as text. this is only the user prompt

        Returns:
            _type_: answer of the llm
        """        
        completion = self.client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},                            
                    ],
                    temperature = 0.0,
                    max_tokens = self.max_new_tokens
                    )

        result = completion.choices[0].message.content
        return result
    
    def encode(self, question, context):
        """encode question and context to a prompt

        Args:
            question (_type_): the question to be asked
            context (_type_): the context the question is directed to

        Returns:
            _type_: the encoded prompt that can be sent to the LLM
        """        
        prompt = self.prompt_template.format(
            question = question,
            context = context
        )
        return prompt

if __name__ == "__main__":
    llm =  LLM()
    question = "Wie alt bin ich?"
    context = "Du bist 40 Jahre alt, dein einer Bruder ist 37 und dein anderer Bruder ist 38. Ich bin 5 Jahre jünger als dein älterer Bruder."
    prompt = llm.encode(question, context)
    print(llm.get_prompt_length_in_tokens(prompt))
    print(f"len prompt: {len(prompt)}")
    print(prompt)
    with Timer():
        text = llm.call(prompt)
    print(text)
    