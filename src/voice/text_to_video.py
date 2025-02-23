import os
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

def create_talk():
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
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def get_talk_status(talk_id):
    d_id_api_key = os.getenv('D_ID_API_KEY')
    if not d_id_api_key:
        raise ValueError("D_ID_API_KEY not found in environment variables")

    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Basic {d_id_api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting talk status: {e}")
        return None

if __name__ == "__main__":
    # Create the talk
    talk_response = create_talk()
    if not talk_response:
        exit(1)
    
    talk_id = talk_response["id"]
    print(f"\nCreated talk with ID: {talk_id}")
    
    # Poll for the talk status until it's done
    while True:
        status_response = get_talk_status(talk_id)
        if not status_response:
            break
            
        status = status_response["status"]
        print(f"Status: {status}")
        
        if status == "done":
            print(f"\nTalk completed!")
            print(f"Result URL: {status_response['result_url']}")
            break
        elif status in ["error", "rejected"]:
            print(f"Talk failed with status: {status}")
            break
            
        time.sleep(1)  # Wait before checking again