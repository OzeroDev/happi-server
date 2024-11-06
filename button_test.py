import subprocess
from gpiozero import Button
import time
subprocess.Popen(['sudo', 'rfcomm', 'connect', '0', '24:54:89:AE:0A:51'])

print('c')
time.sleep(5)

button = Button(2)

button.wait_for_press()
print('You pushed me')

subprocess.Popen(['python', 'thermal-print.py', 'image.png', '>', '/dev/rfcomm0'])