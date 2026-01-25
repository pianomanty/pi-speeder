"""
_test_picamera.py

Test harness for camera_config.py using Picamera2.
Triggers a capture cycle and prints returned filenames.
"""

import time
import multiprocessing as mp
from camera_config import capture_num_frames
import datetime
from pathlib import Path
import os

def create_daily_folder(base_dir:Path):
    today = datetime.now().strftime("%Y%m%d")
    path = base_dir / today
    path.mkdir(parents=True, exist_ok=True)

    os.chdir(path)
    return path


main_folder = "speed_photos_test"  # Name of your main directory
parent_directory = '/home/mediaunion/Pictures/'  # Location of your main directory


def main():
    create_daily_folder(Path(parent_directory)/main_folder)
    # Multiprocessing primitives
    send_queue = mp.Queue()
    receive_queue = mp.Queue()
    capture_event = mp.Event()

    # Start camera worker
    cam_process = mp.Process(
        target=capture_num_frames,
        args=(send_queue, capture_event, receive_queue)
    )
    cam_process.start()

    print("Camera process started.")
    time.sleep(2)  # Allow camera to initialize

    # Send test metadata
    test_speed = 42
    receive_queue.put(test_speed)

    print("Triggering capture...")
    capture_event.set()

    # Allow frames to accumulate
    time.sleep(1.5)

    # Stop capture
    capture_event.clear()

    # Wait for results from camera process
    try:
        images = send_queue.get(timeout=15)
        print("\nCaptured images:")
        for img in images:
            print(" ", img)
    except Exception:
        print("Timed out waiting for camera results.")

    # Clean shutdown
    cam_process.join(timeout=2)
    if cam_process.is_alive():
        cam_process.terminate()
        cam_process.join()

    print("Test complete.")


if __name__ == "__main__":
    main()
