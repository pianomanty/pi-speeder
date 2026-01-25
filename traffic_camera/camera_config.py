"""
File name: camera_config.py
Author: Christian Pedrigal (pedrigalchristian@gmail.com)
Date created: 10/25/2021
Date last modified: 10/25/2021
Python Version: 1.1

TODO:
- Look into using openCV (cv2) to score the sharpness of images, only keep
the top 3 sharpest images of each car, out of the 30fps capture
- Dial in sensor crop (ie zoom)
"""
from picamera2 import Picamera2, Preview
import time
import cv2
# def frame_sharpness(gray):
#     """Return a focus metric based on Laplacian variance"""
#     return cv2.Laplacian(gray, cv2.CV_64F).var()



def capture_num_frames(send_queue, e1, receive_queue):
    """ Create camera object and start background process for camera capture

    Parameters:
    - send_queue: puts pictures into queue for future access with Queue.get()
    - e1: an event that triggers the continuous camera capture, which runs
          indefinitely until e1 is cleared using the Event.clear()
          in data_array_any_amount() function.
    - receive_queue: receives max_speed data and parses value
                     into picture filename
    """

    # Camera Initializations
    camera = Picamera2()

    # 13Jan neuCode to start acquire
    # camera_config = camera.create_preview_configuration()
    camera_config = camera.create_video_configuration(
        main={
            "size": (1920, 1080), "format": "RGB888",
            "format": "YUV420"  # Faster + OCR-friendly
            }

    )

    camera.configure(camera_config)
    camera.start()    

    # Let auto-exposure settle
    time.sleep(1)
   
    # Camera controls (best-effort equivalents)
    camera.set_controls({
        "AeEnable": False,
        "ExposureTime": 3000,   # µs
        "AnalogueGain": 6.0,
        "Contrast": 1.4,
        "Sharpness": 1.5,
        "FrameRate": 30.0,
        "ScalerCrop": (1200, 800, 2000, 1200) #TODO: dial this crop (zoom) in for a real scene
    })
    
    # Runs background process
    try:
        
        while True:
            # Block efficiently until capture is requested
            if not e1.wait(timeout=0.1):
                continue
            else:
                print('Attempting to capture pictures')

            pic_array = []
            # frame_candidates = []
            max_speed = receive_queue.get()

            counter = 0
            while e1.is_set():
                filename = (
                    f"image{counter:02d}_max_speed{max_speed:02d}.mph.jpg"
                )
                frame = camera.capture_array()
                # camera.capture_file(filename) #decoupling taking and saving picture is better

                pic_array.append(filename)

                print(f"{filename} created!")
                counter += 1
                time.sleep(0.03)  # ~30 FPS

                # # Convert YUV → grayscale for scoring
                # gray = cv2.cvtColor(frame, cv2.COLOR_YUV2GRAY_I420)
                # score = frame_sharpness(gray)
                # frame_candidates.append((score, gray))


            # #keep the N sharpest frames
            # frame_candidates.sort(reverse=True, key=lambda x: x[0])
            # best_frames = frame_candidates[:5]  # tune as needed
            # for i, (_, gray) in enumerate(best_frames):
            #     filename = (
            #         f"image{i:02d}_max_speed{max_speed:02d}.mph.jpg"
            #     )
            #     cv2.imwrite(filename, gray)
            #     pic_array.append(filename)
            #     print(f"{filename} saved")

            send_queue.put(pic_array)
    except Exception as e:
        print(f'Error: {e}')
    finally:
        camera.stop()