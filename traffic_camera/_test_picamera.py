"""
_test_picamera.py

Test harness for camera_config.py using Picamera2.
Triggers a capture cycle and prints returned filenames.
"""

import time
import multiprocessing as mp

from camera_config import capture_num_frames


def main():
    # Queues and event
    send_queue = mp.Queue()
    receive_queue = mp.Queue()
    capture_event = mp.Event()

    # Start camera process
    cam_process = mp.Process(
        target=capture_num_frames,
        args=(send_queue, capture_event, receive_queue),
        daemon=True
    )
    cam_process.start()

    print("Camera process started.")
    time.sleep(2)  # give camera time to initialize

    # Simulate speed input (used in filename)
    test_speed = 42
    receive_queue.put(test_speed)

    print("Triggering capture...")
    capture_event.set()

    # Let it capture for a moment
    time.sleep(1.5)

    # Stop capture
    capture_event.clear()

    # Retrieve results
    if not send_queue.empty():
        images = send_queue.get()
        print("\nCaptured images:")
        for img in images:
            print("  ", img)
    else:
        print("No images returned.")

    # Cleanup
    cam_process.terminate()
    cam_process.join()


if __name__ == "__main__":
    main()
