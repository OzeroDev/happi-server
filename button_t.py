import RPi.GPIO as GPIO
from time import sleep

# Set up GPIO numbering mode
GPIO.setmode(GPIO.BCM)

# Define the button pin
button_pin = 17

# Set up the button as an input with pull-up resistor
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        # Check if the button is pressed
        if GPIO.input(button_pin) == GPIO.LOW:
            print("Button pressed!")
            # Do something when the button is pressed
            sleep(0.2)  # Debounce the button

except KeyboardInterrupt:
    # Clean up GPIO on exit
    GPIO.cleanup()