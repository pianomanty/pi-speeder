from picamera2 import Picamera2
import time
import cv2
from pathlib import Path
from threading import Thread
from collections import deque
import queue
"""
TODO: consider trying out true video
"""

N = 10  # Number of sharpest frames to keep

# Sharpness scoring function
def frame_sharpness(gray):
    # Resize to speed up scoring
    small = cv2.resize(gray, (320, 180))
    return cv2.Laplacian(small, cv2.CV_64F).var()

def capture_num_frames(send_queue, e1, receive_queue, testing_mode=True):
    camera = Picamera2()

    # Resolution for Pi 3
    camera_config = camera.create_video_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )
    camera.configure(camera_config)
    camera.start()
    time.sleep(1)

    # Camera controls
    if testing_mode:
        # Indoor testing mode: auto-exposure
        camera.set_controls({
            "AeEnable": True,
            "AwbEnable": True,
            "ScalerCrop": (0, 0, 1280, 720),
            "Contrast": 1.4,
            "Sharpness": 1.5
        })
    else:
        # Fast motion outdoors
        camera.set_controls({
            "AeEnable": False,
            "ExposureTime": 1000,  # 1 ms to freeze motion
            "AnalogueGain": 6.0,
            "Contrast": 1.4,
            "Sharpness": 1.5,
            "ScalerCrop": (0, 0, 1280, 720)
        })

    # Queue for async scoring
    score_queue = queue.Queue(maxsize=50)
    best_frames = deque(maxlen=N)

    # Async scoring worker
    def scoring_worker():
        while True:
            try:
                frame, max_speed = score_queue.get(timeout=1)
            except queue.Empty:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            score = frame_sharpness(gray)

            # Insert into top-N list safely
            if len(best_frames) < N:
                best_frames.append((score, frame))
            else:
                # Properly unpack the tuple
                min_idx, (min_score, _) = min(
                    enumerate(best_frames), key=lambda x: x[1][0]
                )
                if score > min_score:
                    best_frames[min_idx] = (score, frame)

    Thread(target=scoring_worker, daemon=True).start()

    try:
        while True:
            if not e1.wait(timeout=0.1):
                continue

            print("Capturing frames...")
            best_frames.clear()
            max_speed = receive_queue.get()

            # Capture loop
            while e1.is_set():
                frame = camera.capture_array()
                try:
                    score_queue.put_nowait((frame, max_speed))
                except queue.Full:
                    pass  # drop frames if queue is full
                # time.sleep(0.01)  # small sleep to reduce CPU spike

            # Sort top frames by sharpness
            sorted_frames = sorted(best_frames, key=lambda x: x[0], reverse=True)

            # Save results
            saved_files = []
            for i, (_, frame) in enumerate(sorted_frames):
                filename = f"image{i:02d}_max_speed{max_speed:.1f}.jpg"
                cv2.imwrite(str(filename), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                saved_files.append(filename)
                print(f"Saved {filename}")

            send_queue.put(saved_files)

    finally:
        camera.stop()
