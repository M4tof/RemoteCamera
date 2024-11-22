from picamera2 import Picamera2, Preview
from time import sleep
from libcamera import Transform

# Initialize the Picamera2 instance
picam2 = Picamera2()

# Configure the camera for preview mode
camera_config = picam2.create_preview_configuration(transform=Transform(hflip=True, vflip=True))
picam2.configure(camera_config)
picam2.start_preview(Preview.QTGL)

# Start the camera
picam2.start()
sleep(5)

# Define new white balance gains (Red and Blue)
# I've kept the third gain (1.2, 1.2) and added some additional values.
awb_gains = [
    (1.2, 1.2),  # Neutral balance (kept)
    (1.3, 1.0),  # Slightly warmer
    (1.0, 1.3),  # Slightly cooler
    (1.5, 1.0),  # Warmer
    (1.0, 1.5)   # Cooler
]

# Iterate over each white balance gain
for red_gain, blue_gain in awb_gains:
    # Set white balance settings, keeping exposure at default
    picam2.set_controls({
        "AnalogueGain": 2.0,  # Adjust analog gain as needed for brightness
        "ColourGains": (red_gain, blue_gain)
    })

    # Print current settings to the terminal
    print(f"Previewing with ColourGains (Red, Blue): ({red_gain}, {blue_gain})")

    # Keep each preview running for 10 seconds
    sleep(5)

# Stop the camera preview
picam2.stop_preview()
picam2.stop()
