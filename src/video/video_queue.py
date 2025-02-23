from collections import deque
import os
from typing import List

class VideoQueue:
    def __init__(self, base_videos: List[str]):
        """Initialize the video queue with base videos.
        
        Args:
            base_videos: List of paths to base video files
        """
        self.queue = deque(base_videos)
        self.base_path = os.path.join('src', 'assets')
        
        # Define transition video paths
        self.transitions = {
            'transition1': os.path.join(self.base_path, 'transition1.mp4'),
            'transition2': os.path.join(self.base_path, 'transition2.mp4'),
            'transition3': os.path.join(self.base_path, 'transition3.mp4'),
            'transition4': os.path.join(self.base_path, 'transition4.mp4'),
            'transition4_1': os.path.join(self.base_path, 'transition4_1.mp4')
        }
        
        # Verify all transition files exist
        for path in self.transitions.values():
            if not os.path.exists(path):
                raise FileNotFoundError(f"Transition video not found: {path}")

    def handle_interrupt(self, interrupt_type: int) -> None:
        """Handle different types of interrupts by adding appropriate transition videos.
        
        Args:
            interrupt_type: Integer representing the type of interrupt (1-4)
        """
        if interrupt_type == 1:
            # Add transition1 to front
            self.queue.appendleft(self.transitions['transition1'])
            
        elif interrupt_type == 2:
            # Add transition2 followed by transition1
            self.queue.appendleft(self.transitions['transition1'])
            self.queue.appendleft(self.transitions['transition2'])
            
        elif interrupt_type == 3:
            # Add transition3
            self.queue.appendleft(self.transitions['transition3'])
            
        elif interrupt_type == 4:
            # Add transition4 followed by transition4_1
            self.queue.appendleft(self.transitions['transition4_1'])
            self.queue.appendleft(self.transitions['transition4'])
        else:
            raise ValueError(f"Invalid interrupt type: {interrupt_type}")

    def get_next_video(self) -> str:
        """Get the next video from the queue.
        
        Returns:
            Path to the next video file
        
        Raises:
            IndexError: If queue is empty
        """
        if not self.queue:
            raise IndexError("Video queue is empty")
        return self.queue.popleft()
    
    def add_video(self, video_path: str, to_front: bool = False) -> None:
        """Add a video to the queue.
        
        Args:
            video_path: Path to the video file
            to_front: If True, add to front of queue, else add to back
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
            
        if to_front:
            self.queue.appendleft(video_path)
        else:
            self.queue.append(video_path)
    
    def is_empty(self) -> bool:
        """Check if queue is empty.
        
        Returns:
            True if queue is empty, False otherwise
        """
        return len(self.queue) == 0
    
    def clear(self) -> None:
        """Clear all videos from the queue."""
        self.queue.clear()
    
    def __len__(self) -> int:
        """Get number of videos in queue."""
        return len(self.queue) 