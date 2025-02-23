import os
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

url = "https://api.d-id.com/talks"

payload = {
    "source_url": "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg",
    "script": {
        "type": "text",
        "subtitles": False,
        "provider": {
            "type": "microsoft",
            "voice_id": "Sara"
        },
        "input": "Hey, thanks for taking the time to speak with me. I'm Ed Chambers account executive. How are you today?"
    },
    "config": { "fluent": False }
}

# Get API keys
eleven_api_key = os.getenv('e11even_API_KEY')
d_id_api_key = os.getenv('D_ID_API_KEY')

if not eleven_api_key:
    raise ValueError("e11even_API_KEY not found in environment variables")
if not d_id_api_key:
    raise ValueError("D_ID_API_KEY not found in environment variables")

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "Authorization": f"Basic {d_id_api_key}"
}

try:
    start_time = time.time()
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    elapsed_time = time.time() - start_time
    print(f"Response received in {elapsed_time:.2f} seconds:")
    print(response.text)
except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")