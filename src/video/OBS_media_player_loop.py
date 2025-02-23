import obsws_python as obs
import time
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
OBS_SERVER_PWD = os.getenv('OBS_SERVER_PWD')
VIDEO_FOLDER = os.getenv('VIDEO_FOLDER')

# Validate environment variables
if not OBS_SERVER_PWD:
    raise ValueError("OBS_SERVER_PWD not found in environment variables. Check your .env file.")
if not VIDEO_FOLDER:
    raise ValueError("VIDEO_FOLDER not found in environment variables. Check your .env file.")

class MediaPlayer:
    def __init__(self, host='localhost', port=4455, password=OBS_SERVER_PWD):
        try:
            print(f"Connecting to OBS WebSocket server on {host}:{port}...")
            self.client = obs.ReqClient(host=host, port=port, password=password)
            print("Successfully connected to OBS!")
        except obs.error.OBSSDKError as e:
            print("\nConnection Error! Please check:")
            print("1. Is OBS running?")
            print("2. Is the WebSocket server enabled? (Tools -> obs-websocket Settings)")
            print("3. Is the port correct? (Should be 4455)")
            print("4. Is the password correct?")
            print(f"\nError details: {str(e)}")
            raise
        
    def setup_media_source(self, source_name='VideoPlayer'):
        """Create or get the media source"""
        try:
            # First try to create a new media source with required settings
            input_settings = {
                'is_local_file': True,
                'local_file': '',  # Will be set later for each video
                'looping': False,
                'restart_on_activate': False,
                'close_when_inactive': False,
                'hw_decode': True,
                'clear_on_media_end': False
            }
            
            # Create the input if it doesn't exist
            self.client.create_input(
                sceneName='Scene',
                inputName=source_name,
                inputKind='ffmpeg_source',
                inputSettings=input_settings,
                sceneItemEnabled=True
            )
            print(f"Created new media source: {source_name}")
            
            # Set the transform to make it visible in the center
            transform = {
                "alignment": 5,  # Center
                "height": 1080.0,
                "positionX": 960.0,  # Half of 1920 for center
                "positionY": 540.0,  # Half of 1080 for center
                "rotation": 0.0,
                "scaleX": 1.0,
                "scaleY": 1.0,
                "width": 1920.0
            }
            
            # Get the scene item ID first
            scene_item_id = self.client.get_scene_item_id("Scene", source_name).scene_item_id
            
            # Set the transform
            self.client.set_scene_item_transform("Scene", scene_item_id, transform)
            print("Set video transform to be visible in preview")
            
        except obs.error.OBSSDKError as e:
            if "already exists" in str(e):
                print(f"Using existing media source: {source_name}")
                # Still try to set transform for existing source
                try:
                    scene_item_id = self.client.get_scene_item_id("Scene", source_name).scene_item_id
                    transform = {
                        "alignment": 5,  # Center
                        "height": 1080.0,
                        "positionX": 960.0,  # Half of 1920 for center
                        "positionY": 540.0,  # Half of 1080 for center
                        "rotation": 0.0,
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                        "width": 1920.0
                    }
                    self.client.set_scene_item_transform("Scene", scene_item_id, transform)
                    print("Updated existing source transform")
                except Exception as e:
                    print(f"Warning: Could not update transform: {e}")
            else:
                raise
        return source_name

    def wait_for_media_end(self, source_name):
        """Wait for media to finish playing"""
        while True:
            try:
                media_info = self.client.get_media_input_status(source_name)
                state = media_info.media_state
                if state in ["OBS_MEDIA_STATE_STOPPED", "OBS_MEDIA_STATE_ENDED", "OBS_MEDIA_STATE_ERROR"]:
                    return
                time.sleep(0.5)
            except Exception as e:
                print(f"Error checking media state: {e}")
                return

    def play_videos(self, video_folder, source_name='VideoPlayer'):
        """Continuously play videos from the specified folder"""
        video_files = list(Path(video_folder).glob('*.mp4'))
        if not video_files:
            raise ValueError(f"No MP4 files found in {video_folder}")

        print(f"Found {len(video_files)} MP4 files in {video_folder}")
        source_name = self.setup_media_source(source_name)
        
        try:
            while True:  # Outer loop for continuous playlist
                print("\nStarting playlist...")
                for video_file in video_files:
                    try:
                        print(f"\nPlaying: {video_file.name}")
                        
                        # Stop current playback
                        self.client.trigger_media_input_action(source_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP")
                        time.sleep(1)  # Give it a moment to stop
                        
                        # Set the media file path
                        settings = {
                            'is_local_file': True,
                            'local_file': str(video_file),
                            'looping': False,
                            'restart_on_activate': False,
                            'close_when_inactive': False,
                            'hw_decode': True,
                            'clear_on_media_end': False
                        }
                        self.client.set_input_settings(source_name, settings, True)
                        time.sleep(1)  # Give OBS a moment to load the file
                        
                        # Start playing
                        self.client.trigger_media_input_action(source_name, "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY")
                        
                        # Get initial media state
                        media_info = self.client.get_media_input_status(source_name)
                        print(f"Initial state: {media_info.media_state}")
                        
                        # Wait for the video to actually finish
                        self.wait_for_media_end(source_name)
                        print(f"Finished playing: {video_file.name}")
                        
                    except Exception as e:
                        print(f"Error playing {video_file.name}: {str(e)}")
                        time.sleep(2)  # Wait a bit before trying next video
                        continue
                
                print("\nRestarting playlist from beginning...")
                
        except KeyboardInterrupt:
            print("\nStopping video playback...")
        except Exception as e:
            print(f"\nPlayback error: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        # Initialize the player
        player = MediaPlayer()
        
        # Start playing videos from the folder specified in .env
        player.play_videos(VIDEO_FOLDER)
    except KeyboardInterrupt:
        print("\nStopping video playback...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please fix the error and try again.")