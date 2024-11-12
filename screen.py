
import tkinter as tk
import cv2
from PIL import Image, ImageTk


frame_index = 0

frame_count = 800
text = ''

def updateText():
    global text
    with open('prompt.txt', 'r') as file:
        text = file.read().replace('\n', '')


def play_video():
    global frame_index, frame_count, text
    
    if frame_count >= 800:
        updateText()
        frame_count = 0
    else:
        frame_count=frame_count+1


    ret, frame = cap.read()
    
    if not ret:
        frame_index = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Resize the frame to the screen size
    frame = cv2.resize(frame, (screen_width, screen_height))

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    img = ImageTk.PhotoImage(img)
    label.config(image=img)
    label.image = img

    root.after(1, play_video)


root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes("-type", "splash")
root.config(background = "#000000")
root.title("Happi Display")

cap = cv2.VideoCapture("blink.mp4")  # Replace with your video file

label = tk.Label(root)
label.pack(fill=tk.BOTH, expand=True)  # This makes the label expand to fill the window


root.after(30, play_video)

root.mainloop()