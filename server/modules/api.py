import json
import requests

TOKEN = "" #補完してください
API_URL = f"https://api-inference.huggingface.co/models/kkuramitsu/kogi-mt5-test"
headers = {"Authorization": f"Bearer {TOKEN}"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

if __name__ == "__main__":

    output = query({
	    "inputs": "ハローワールドと表示する",
        # option:カンマ区切り
    })
    
    print(output)
    print(output[0]["generated_text"])
