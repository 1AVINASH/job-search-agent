import os
import json
from datetime import datetime
from dataclasses import dataclass
import re
from logger import app_logger
from typing import Optional, List, Dict, Any

from openai import OpenAI
import tiktoken
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
HISTORY_DIR = "chat_histories"
MODEL = "gpt-4o"  # or gpt-3.5-turbo
enc = tiktoken.encoding_for_model(MODEL)

os.makedirs(HISTORY_DIR, exist_ok=True)

def count_tokens(messages, model=MODEL):
    # Get encoding for the specific model
    encoding = tiktoken.encoding_for_model(model)

    # Each message has role, content, maybe name — structure matters
    # Token calculation rules are model-specific
    if model.startswith("gpt-3.5"):
        tokens_per_message = 4  # 3.5-turbo
        tokens_per_name = -1
    elif model.startswith("gpt-4"):
        tokens_per_message = 3  # gpt-4 (as per OpenAI docs)
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"Token counting not supported for model {model}")

    total_tokens = 0
    for message in messages:
        total_tokens += tokens_per_message
        for key, value in message.items():
            total_tokens += len(encoding.encode(value))
            if key == "name":
                total_tokens += tokens_per_name
    total_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
    return total_tokens

class JobSearcher:
    def __init__(selft):
        ...

    def get_history_path(self) -> str:
        return os.path.join(HISTORY_DIR, f"jobs.json")

    def load_chat_history(self)-> List[Dict[str, Any]]:
        path = self.get_history_path()
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return [{"role": "system", "content": f"""You are an expert on searching job. You have to provide job details of companies that offer remote job. I am a software engineer that lives in Bengaluru with 4 years of experience and I am open to working at any company (location is not a bar). \
                 I am preferably looking to get hired at a Mid Seniority role.\
                 I have worked majorly with Python and also have 8 months of experience in Golang. Here are the other skills that might be relevant: AWS (Lambda, S3, API Gateway, RDBMS, EC2, Route53, etc.): 4 Yoe, Postgres, DynamoDB, Redis, \
                 Docker, MongoDB, RabbitMQ, NATS, Celery, FastAPI, Flask \
                 The company details should be in a valid json format and should follow these details:\
                 1. "company_name": The name of the company
                 2. "company_website": The website of the company
                 3. "company_domain": The domain that the company operates in
                 4. "mails": Mails of people working in the company that can be contacted for a job
                 5. "company_summary": A brief 2 liner summary of what the company does and how my job is connected to it
                 6. "company_location": The location of the company. This can be a list if there are multiple locations with the first one being the HQ
                 7. "metadata": It can have extra details about the company that you deem relevant
                 8. "jobs_open": This should be a dictionary with the job link, job description, and date posted
                 """}]

    def save_chat_history(self, history):
        path = self.get_history_path()
        with open(path, 'w') as f:
            json.dump(history, f, indent=2)

    def get_fact(self):
        history = self.load_chat_history()
        current_date = datetime.now().strftime("%d %b %Y")
        current_date_time = datetime.now().strftime("%d %b %YT%H:%M:%S")
        # Append user prompt
        history.append({"role": "user", "content": 
            f"Give me new company details in the above provided format that is hiring for remote role for a software engineer with 4 YoE. Only include jobs which were posted in 2025 and give preference to latest job posts and try to find something posted in the last month. Today is {current_date}\
        "})
        app_logger.info(f"Latest prompt: {history[-1]}")
        messages = [{"role": message["role"], "content": message["content"]} for message in history]
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        input_tokens = count_tokens(messages)
        assistant_reply = response.choices[0].message.content.strip()


        try:
            parsed_assistant_reply = json.loads(assistant_reply)
        except Exception as e:
            print(e)
            raise e
        # Append assistant response to history
        history.append({"role": "assistant", "content": assistant_reply, "metadata": {"current_date_time": current_date_time, "input_tokens": input_tokens, "company": parsed_assistant_reply}})
        self.save_chat_history(history)

        return assistant_reply