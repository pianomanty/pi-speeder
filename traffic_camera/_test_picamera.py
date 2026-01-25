"""
_test_picamera.py

Test harness for camera_config.py using Picamera2.
Triggers a capture cycle and prints returned filenames.
"""

import time
import multiprocessing as mp
from camera_config import capture_num_frames
from datetime import datetime
from pathlib import Path
import os

def create_daily_folder(current_date, sub_directory):
    """ Creates a child directory for every new day the program is run.""" 
    
    date = datetime.now()
    
    if current_date == date:
        return current_date
    else:
        
        # Creation of daily folder filename.
        year = date.strftime("%Y")
        month = date.strftime("%m")
        day = date.strftime("%d")
        folder_name = "{}{}{}".format(year,month,day)
        
        # Creation of full path to daily folder.
        full_path = os.path.join(sub_directory, folder_name) 
        os.chdir(sub_directory)
        
        # Creates new daily folder if doesn't exist already.
        if not os.path.exists(full_path):
            os.mkdir(folder_name)
            
        os.chdir(full_path)
        return (full_path, date)


main_folder = "speed_photos_test"  # Name of your main directory
parent_directory = '/home/mediaunion/Pictures/'  # Location of your main directory
curr_directory = os.path.join(parent_directory,main_folder)
current_date = datetime.now()

def main():
    (daily_folder_path, current_date) = create_daily_folder(
                                                    current_date,
                                                    curr_directory
                                                    )    # Multiprocessing primitives
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
