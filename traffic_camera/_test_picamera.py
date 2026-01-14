""" Test LPR API with static images taken from picamera."""


import time
import os
import requests
from pprint import pprint
from datetime import datetime

from picamera2 import Picamera2, Preview

from file_org import create_daily_folder

# Token from LPR
TOKEN = 'b0d681034ef2a4b8d3db7e0813e440f4780e1519'

# Create testing folder
current_date = datetime.now()
sub_directory = create_daily_folder(current_date, os.getcwd())

# Create camera object
camera = Picamera2()

    camera_config = camera.create_preview_configuration()
    camera.configure(camera_config)
    camera.start_preview(Preview.DRM)
    camera.start()
    time.sleep(2)
    camera.capture_file("Bubba1.jpg")

name = input('Create a name for the picture: ') + '.jpeg'



# Camera Configurations
camera.zoom = (0.35, 0.35, 0.30, 0.30)
camera.color_effects = (128,128) # black and white
camera.contrast = 13
#camera.shutter_speed = 8000
camera.exposure_mode = 'sports'
# camera.iso = 400

time.sleep(2)
camera.capture_file(name)
print("%s snapped!" % name)


with open(name, 'rb') as fp:
    print("Sending to LPR...")
    response = requests.post(
        'https://api.platerecognizer.com/v1/plate-reader/',
        files=dict(upload=fp),
        headers={'Authorization': f'Token {TOKEN}'})
pprint(response.json())




