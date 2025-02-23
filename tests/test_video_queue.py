import unittest
import os
from src.video.video_queue import VideoQueue

class TestVideoQueue(unittest.TestCase):
    def setUp(self):
        # Create mock video files for testing
        self.base_path = os.path.join('src', 'assets')
        os.makedirs(self.base_path, exist_ok=True)
        
        # Create empty transition files
        self.transitions = [
            'transition1.mp4',
            'transition2.mp4',
            'transition3.mp4',
            'transition4.mp4',
            'transition4_1.mp4'
        ]
        for t in self.transitions:
            path = os.path.join(self.base_path, t)
            open(path, 'a').close()
            
        # Create base videos
        self.base_videos = [
            os.path.join(self.base_path, 'base1.mp4'),
            os.path.join(self.base_path, 'base2.mp4')
        ]
        for v in self.base_videos:
            open(v, 'a').close()
            
    def tearDown(self):
        # Clean up test files
        for t in self.transitions:
            os.remove(os.path.join(self.base_path, t))
        for v in self.base_videos:
            os.remove(v)
            
    def test_interrupt_type_1(self):
        queue = VideoQueue(self.base_videos)
        queue.handle_interrupt(1)
        
        # Should have transition1 at front
        self.assertEqual(
            queue.get_next_video(),
            os.path.join(self.base_path, 'transition1.mp4')
        )
        
    def test_interrupt_type_2(self):
        queue = VideoQueue(self.base_videos)
        queue.handle_interrupt(2)
        
        # Should have transition2 then transition1
        self.assertEqual(
            queue.get_next_video(),
            os.path.join(self.base_path, 'transition2.mp4')
        )
        self.assertEqual(
            queue.get_next_video(),
            os.path.join(self.base_path, 'transition1.mp4')
        )
        
    def test_interrupt_type_3(self):
        queue = VideoQueue(self.base_videos)
        queue.handle_interrupt(3)
        
        # Should have just transition3
        self.assertEqual(
            queue.get_next_video(),
            os.path.join(self.base_path, 'transition3.mp4')
        )
        
    def test_interrupt_type_4(self):
        queue = VideoQueue(self.base_videos)
        queue.handle_interrupt(4)
        
        # Should have transition4 then transition4_1
        self.assertEqual(
            queue.get_next_video(),
            os.path.join(self.base_path, 'transition4.mp4')
        )
        self.assertEqual(
            queue.get_next_video(),
            os.path.join(self.base_path, 'transition4_1.mp4')
        )
        
    def test_base_videos_preserved(self):
        queue = VideoQueue(self.base_videos)
        queue.handle_interrupt(1)  # Add transition1
        
        # Skip transition
        queue.get_next_video()
        
        # Should still have base videos in order
        self.assertEqual(
            queue.get_next_video(),
            self.base_videos[0]
        )
        self.assertEqual(
            queue.get_next_video(),
            self.base_videos[1]
        )
        
if __name__ == '__main__':
    unittest.main() 