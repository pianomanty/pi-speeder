from picamera2 import Picamera2
import time
import cv2
from pathlib import Path

im_save_dir = Path("~/Pictures").expanduser()
im_save_dir.mkdir(parents=True, exist_ok=True)


def frame_sharpness(gray):
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def capture_num_frames(send_queue, e1, receive_queue):

    camera = Picamera2()
    N = 10

    camera_config = camera.create_video_configuration(
        main={
            "size": (1920, 1080),
            "format": "YUV420"
        }
    )

    camera.configure(camera_config)
    camera.start()
    time.sleep(1)

    camera.set_controls({
        "AeEnable": False,
        "ExposureTime": 3000,
        "AnalogueGain": 6.0,
        "Contrast": 1.4,
        "Sharpness": 1.5,
        "ScalerCrop": (1200, 800, 2000, 1200)
    })

    try:
        while True:
            # Wait for capture signal
            if not e1.wait(timeout=0.1):
                continue

            print("Capturing frames...")

            frames = []
            max_speed = receive_queue.get()

            # ---- CAPTURE ONLY ----
            while e1.is_set():
                frame = camera.capture_array()
                frames.append(frame)
                time.sleep(0.03)  # ~30 FPS

            print(f"Captured {len(frames)} frames")

            # ---- SCORING PHASE ----
            scored_frames = []
            for frame in frames:
                gray = frame[:, :, 0] if frame.ndim == 3 else frame
                score = frame_sharpness(gray)
                scored_frames.append((score, frame))

            scored_frames.sort(reverse=True, key=lambda x: x[0])
            best_frames = scored_frames[:N]

            # ---- SAVE RESULTS ----
            saved_files = []

            for i, (_, frame) in enumerate(best_frames):
                filename = (
                    im_save_dir /
                    f"image{i:02d}_max_speed{max_speed:02d}.jpg"
                )

                bgr = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                cv2.imwrite(str(filename), bgr)

                saved_files.append(filename)
                print(f"Saved {filename}")

            send_queue.put(saved_files)

    finally:
        camera.stop()
