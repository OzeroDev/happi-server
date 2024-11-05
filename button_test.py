
from gpiozero import Button

button = Button(2)

button.wait_for_active()
print('You pushed me')