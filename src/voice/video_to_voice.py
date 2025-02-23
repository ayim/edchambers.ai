import os
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

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

def download_video(url, output_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the video file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Video saved to: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading video: {e}")
        return False

def wait_for_talk_completion(talk_id):
    while True:
        status_response = get_talk_status(talk_id)
        if not status_response:
            return None
            
        status = status_response["status"]
        print(f"Status: {status}")
        
        if status == "done":
            print(f"\nTalk completed!")
            return status_response['result_url']
        elif status in ["error", "rejected"]:
            print(f"Talk failed with status: {status}")
            return None
            
        time.sleep(1)  # Wait before checking again

if __name__ == "__main__":
    # Example usage
    talk_id = input("Enter talk ID: ")
    result_url = wait_for_talk_completion(talk_id)
    if result_url:
        print(f"Result URL: {result_url}")
        # Save video to output directory
        output_path = os.path.join('output', 'videos', f'{talk_id}.mp4')
        download_video(result_url, output_path)
