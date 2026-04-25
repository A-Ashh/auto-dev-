import requests
import os

HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {os.environ['HF_TOKEN']}"
}


def call_llm(history):
    prompt = ""

    for msg in history:
        if msg["role"] == "user":
            prompt += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            prompt += f"Assistant: {msg['content']}\n"

    prompt += "Assistant:"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 50,
            "temperature": 0.3
        }
    }

    response = requests.post(HF_API_URL, headers=headers, json=payload)

    output = response.json()

    try:
        text = output[0]["generated_text"]
        return text.split("Assistant:")[-1].strip()
    except:
        print("HF error:", output)
        return "ls"
