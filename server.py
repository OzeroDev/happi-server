import discord.client
import discord.message
from flask import Flask, request, json, render_template, jsonify
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
from dotenv import load_dotenv
import os
import discord
import asyncio
from threading import Thread
import sqlite3
import subprocess
# import tkinter as tk
# import cv2
import time
import requests


load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
VERIFY_CHANNEL_ID = 1305668137408008252
PROMPT_CHANNEL_ID = 1305668162091618345
SERVER_CHANNEL_ID = 1305668190935847003
COLOR_PRINT_CHANNEL_ID = 1310582694723190834

current_prompt = ''

with open('prompt.txt', 'r') as file:
    current_prompt = file.read().replace('\n', '')

# database init
VERIFIED = 1
UNVERIFIED = 0

con = sqlite3.connect("responses.db", check_same_thread=False)
cur = con.cursor()

def saveResponseToDB(prompt, response_type):
    cur.execute('''
        INSERT INTO responses (prompt, type) 
        VALUES (?, ?)
    ''', (prompt, response_type))
    con.commit()

    return cur.lastrowid

def verifyResponse(res_id):
    cur.execute('''UPDATE responses SET verified = ? WHERE id = ?''', (VERIFIED, res_id))
    con.commit()

def unverifyResponse(res_id):
    cur.execute('''UPDATE responses SET verified = ? WHERE id = ?''', (UNVERIFIED, res_id))
    con.commit()


def logEvent(eType):
    try:
        requests.post("https://brief-uniformly-drum.ngrok-free.app/event", data={"event_type": eType}, timeout=(None, 0.00001))
    except requests.exceptions.ReadTimeout:
        pass


async def colorPrintToDiscord(img_path):
    channel = client.get_channel(COLOR_PRINT_CHANNEL_ID)

    msg = await channel.send(content="Print this on color printer:", file=discord.File(img_path))


def printRandomImg(prompt):

    cur.execute("""
        SELECT id, printedCount, type
        FROM responses
        WHERE prompt = ?
            AND verified = 1
        ORDER BY printedCount ASC, id ASC
        LIMIT 1
    """, (prompt,))


    # Fetch the result
    result = cur.fetchone()

    if result:
        response_id, printedCount, type = result
        # Increment the printedCount value by 1
        cur.execute("""
            UPDATE responses
            SET printedCount = ?
            WHERE id = ?
        """, (printedCount + 1, response_id))
        
        # Commit the changes to the database
        con.commit()

        if type == "color-printer":
            client.loop.create_task(colorPrintToDiscord("responses/"+str(response_id)+".png"))
            return ""
        
        return "responses/"+str(response_id)+".png"
    else:
        return "no-responses.png"
    


# Discord bot 

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        channel = client.get_channel(SERVER_CHANNEL_ID)
        await channel.send('The happi-server has just started running with the following prompt:\n'+current_prompt+'\n...')


intents = discord.Intents.default()
intents.message_content = True
client = Client(intents=intents)

@client.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == VERIFY_CHANNEL_ID:
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        img_id = message.attachments[0].url.split('/')[-1].split('.', 1)[0]

        if payload.emoji.name == '✅' or payload.emoji.name == '❌':
            approval_reaction = discord.utils.get(message.reactions, emoji='✅')
            disapproval_reaction = discord.utils.get(message.reactions, emoji='❌')
            
            if disapproval_reaction and disapproval_reaction.count > 1:
                
                await message.edit(content="❌ Disproved")
                user = client.get_user(payload.user_id)
                #await message.remove_reaction(payload.emoji.name, user)
                for reaction in message.reactions:
                    async for user in reaction.users():
                        if not user.bot:
                            await reaction.remove(user)

                unverifyResponse(img_id)

            elif approval_reaction and approval_reaction.count > 1:

                await message.edit(content="✅ Verified")
                user = client.get_user(payload.user_id)
                #await message.remove_reaction(payload.emoji, user)
                for reaction in message.reactions:
                    async for user in reaction.users():
                        if not user.bot:
                            await reaction.remove(user)

                verifyResponse(img_id)
        

@client.event
async def on_message(message):
    if message.author != client.user and message.channel.id == PROMPT_CHANNEL_ID and message.content:
        current_prompt = message.content
       
        with open('prompt.txt', 'w') as file:
            file.write(current_prompt)
        
        channel = client.get_channel(PROMPT_CHANNEL_ID)
        await channel.send('The current prompt is now:\n'+current_prompt)

        
        




async def saveImage(image, prompt, image_print_type):
    img_path = 'responses/'+str(saveResponseToDB(prompt, image_print_type))+'.png'
    image.save(img_path, 'PNG')

    channel = client.get_channel(VERIFY_CHANNEL_ID)

    msg = await channel.send(content="Awaiting Verification", file=discord.File(img_path))
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')


async def getPrompt():
    channel = client.get_channel(VERIFY_CHANNEL_ID)






# Flask endpoint


app = Flask(__name__)
CORS(app)

thermal_printer_size = (818, 1258)
photo_printer_size = (818, 1258)

# add_ipad_response POST request
@app.route('/add_ipad_response', methods = ['POST'])
def handle_add_ipad_response():
    if request.method == 'POST':
        if request.headers['password'] == 'wegojapan':
            data = json.loads(request.data)
        
            img_base64 = data['image_base_64']
            prompt = data['prompt']

            raw_img = Image.open(BytesIO(base64.decodebytes(bytes(img_base64, "utf-8"))))
            img = Image.new("RGBA", raw_img.size, "WHITE") # Create a white rgba background
            img.paste(raw_img, (0, 0), raw_img)              # Paste the image on the background. Go to the links given below for details.

            img = ImageOps.expand(img, border=(0,70,0,0), fill=(255,255,255))
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("font.ttf", size=26)

            text_width = draw.textlength(prompt, font)
            text_x = (img.width - text_width) // 2  # Center text
            draw.text((text_x,10),prompt, fill=(0, 0, 0),font=font)

            # adding

            width, height = img.size # aspect is 

            if (width/height)>(3/2):
                # find height diff to make it be 5/4
                height_d = (width/1.25)-height

                height_border = int(height_d/2) #size of height to add

                border_img = Image.open('goldy.png')
                border_img = border_img.resize((height_border, height_border), Image.Resampling.LANCZOS)

                img = ImageOps.expand(img, border=(0,height_border,0,height_border), fill=(255,255,255))

                row_count = width // height_border

                offset = int(((width)-(row_count*height_border))/2)

                for i in range(row_count):
                    img.paste(border_img, (offset+(i*height_border),0))
                    img.paste(border_img, (offset+(i*height_border),height+height_border))


            client.loop.create_task(saveImage(img, prompt, "thermal-printer"))

            return 'success'
        return 'failure'
    
    

# add_qr_response POST request
@app.route('/add_qr_response', methods = ['POST'])
def handle_add_qr_response():
    if request.method == 'POST':
        if request.headers['dtype'] == 'img':
            data = json.loads(request.data)
        
            response_img = data['image']
            prompt = data['prompt']
            text = prompt
            raw_img = Image.open(BytesIO(base64.decodebytes(bytes(response_img, "utf-8")))).convert("RGBA")



            img = Image.new("RGBA", raw_img.size, "WHITE") # Create a white rgba background
            img.paste(raw_img, (0, 0), raw_img)              # Paste the image on the background. Go to the links given below for details.

            img = ImageOps.expand(img, border=(0,100,0,0), fill=(255,255,255))
            draw = ImageDraw.Draw(img)


            max_font_size = 75
            font_path = "font.ttf"
            font = ImageFont.truetype(font_path, max_font_size)


            width, height = img.size # aspect is 

            # Function to check if the text fits within the given width and height
            def text_fits(font, text, max_width, max_height):
                lines = text.split('\n')
                total_height = 0
                max_line_width = 0
                
                for line in lines:
                    # Use textbbox() to calculate the bounding box of the text
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]  # width of the text
                    line_height = bbox[3] - bbox[1]  # height of the text
                    max_line_width = max(max_line_width, line_width)
                    total_height += line_height
                
                return max_line_width <= max_width and total_height <= max_height
            
            # Start with the max font size and reduce until text fits
            font_size = max_font_size
            while font_size > 1:
                font = ImageFont.truetype(font_path, font_size)
                
                # Check if the text fits within the image bounds
                if text_fits(font, text, width-20, 70):
                    break
                
                font_size -= 1
            
            # Now we have the maximum font size that fits within the bounds, calculate the wrapping
            lines = text.split('\n')
            total_text_height = 0
            line_heights = []
            
            # Calculate total height of all lines and individual line heights
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_text_height += line_height
                line_heights.append(line_height)
            
            # Calculate position to center the text
            y_offset = (70 - total_text_height) // 2
            for i, line in enumerate(lines):
                # Get the bounding box of the line to center it horizontally
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_offset = (width - text_width) // 2  # Center the text horizontally
                draw.text((x_offset, y_offset), line, font=font, fill="black")
                y_offset += line_heights[i]  # Move to the next line
            

            client.loop.create_task(saveImage(img, prompt, "color-printer"))

            return jsonify(res='success')
        elif request.headers['dtype'] == 'text':
            data = json.loads(request.data)
        
            text = data['text']
            prompt = data['prompt']

            img = Image.new("RGBA", (900, 400), "WHITE")
            

            width, height = img.size
            draw = ImageDraw.Draw(img)
            
            # img = ImageOps.expand(img, border=(0,70,0,0), fill=(255,255,255))
            font = ImageFont.truetype("font.ttf", size=26)

            text_width = draw.textlength(prompt, font)
            text_x = (img.width - text_width) // 2  # Center text
            draw.text((text_x,10),prompt, fill=(0, 0, 0),font=font)




            max_font_size = 75
            font_path = "Roboto-Regular.ttf"
            font = ImageFont.truetype(font_path, max_font_size)



            # Function to check if the text fits within the given width and height
            def text_fits(font, text, max_width, max_height):
                lines = text.split('\n')
                total_height = 0
                max_line_width = 0
                
                for line in lines:
                    # Use textbbox() to calculate the bounding box of the text
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]  # width of the text
                    line_height = bbox[3] - bbox[1]  # height of the text
                    max_line_width = max(max_line_width, line_width)
                    total_height += line_height
                
                return max_line_width <= max_width and total_height <= max_height
            
            # Start with the max font size and reduce until text fits
            font_size = max_font_size
            while font_size > 1:
                font = ImageFont.truetype(font_path, font_size)
                
                # Check if the text fits within the image bounds
                if text_fits(font, text, 820, 320):
                    break
                
                font_size -= 1
            
            # Now we have the maximum font size that fits within the bounds, calculate the wrapping
            lines = text.split('\n')
            total_text_height = 0
            line_heights = []
            
            # Calculate total height of all lines and individual line heights
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_text_height += line_height
                line_heights.append(line_height)
            
            # Calculate position to center the text
            y_offset = (height - total_text_height) // 2
            for i, line in enumerate(lines):
                # Get the bounding box of the line to center it horizontally
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_offset = (width - text_width) // 2  # Center the text horizontally
                draw.text((x_offset, y_offset), line, font=font, fill="black")
                y_offset += line_heights[i]  # Move to the next line
            






            width, height = img.size # aspect is 

            if (width/height)>(3/2):
                # find height diff to make it be 5/4
                height_d = (width/1.25)-height

                height_border = int(height_d/2) #size of height to add

                border_img = Image.open('goldy.png')
                border_img = border_img.resize((height_border, height_border), Image.Resampling.LANCZOS)

                img = ImageOps.expand(img, border=(0,height_border,0,height_border), fill=(255,255,255))

                row_count = width // height_border

                offset = int(((width)-(row_count*height_border))/2)

                for i in range(row_count):
                    img.paste(border_img, (offset+(i*height_border),0))
                    img.paste(border_img, (offset+(i*height_border),height+height_border))

            client.loop.create_task(saveImage(img, prompt, "thermal-printer"))



            return jsonify(res='success')
        elif request.headers['dtype'] == 'both':
            data = json.loads(request.data)
        
            response_img = data['image']
            response_txt = data['text']
            prompt = data['prompt']
            text = prompt
            raw_img = Image.open(BytesIO(base64.decodebytes(bytes(response_img, "utf-8")))).convert("RGBA")



            img = Image.new("RGBA", raw_img.size, "WHITE") # Create a white rgba background
            img.paste(raw_img, (0, 0), raw_img)              # Paste the image on the background. Go to the links given below for details.

            img = ImageOps.expand(img, border=(0,100,0,120), fill=(255,255,255))
            draw = ImageDraw.Draw(img)


            max_font_size = 75
            font_path = "font.ttf"
            font = ImageFont.truetype(font_path, max_font_size)


            width, height = img.size # aspect is 

            # Function to check if the text fits within the given width and height
            def text_fits(font, text, max_width, max_height):
                lines = text.split('\n')
                total_height = 0
                max_line_width = 0
                
                for line in lines:
                    # Use textbbox() to calculate the bounding box of the text
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]  # width of the text
                    line_height = bbox[3] - bbox[1]  # height of the text
                    max_line_width = max(max_line_width, line_width)
                    total_height += line_height
                
                return max_line_width <= max_width and total_height <= max_height
            
            # Start with the max font size and reduce until text fits
            font_size = max_font_size
            while font_size > 1:
                font = ImageFont.truetype(font_path, font_size)
                
                # Check if the text fits within the image bounds
                if text_fits(font, text, width-20, 70):
                    break
                
                font_size -= 1
            
            # Now we have the maximum font size that fits within the bounds, calculate the wrapping
            lines = text.split('\n')
            total_text_height = 0
            line_heights = []
            
            # Calculate total height of all lines and individual line heights
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_text_height += line_height
                line_heights.append(line_height)
            
            # Calculate position to center the text
            y_offset = (70 - total_text_height) // 2
            for i, line in enumerate(lines):
                # Get the bounding box of the line to center it horizontally
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_offset = (width - text_width) // 2  # Center the text horizontally
                draw.text((x_offset, y_offset), line, font=font, fill="black")
                y_offset += line_heights[i]  # Move to the next line
            



            text = response_txt


            font_path = "Roboto-Regular.ttf"
            font = ImageFont.truetype(font_path, max_font_size)


            # Start with the max font size and reduce until text fits
            font_size = max_font_size
            while font_size > 1:
                font = ImageFont.truetype(font_path, font_size)
                
                # Check if the text fits within the image bounds
                if text_fits(font, text, width-20, 110):
                    break
                
                font_size -= 1
            
            # Now we have the maximum font size that fits within the bounds, calculate the wrapping
            lines = text.split('\n')
            total_text_height = 0
            line_heights = []
            
            # Calculate total height of all lines and individual line heights
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                total_text_height += line_height
                line_heights.append(line_height)
            
            # Calculate position to center the text
            y_offset = height-110+(total_text_height //2)
            for i, line in enumerate(lines):
                # Get the bounding box of the line to center it horizontally
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x_offset = (width - text_width) // 2  # Center the text horizontally
                draw.text((x_offset, y_offset), line, font=font, fill="black")
                y_offset += line_heights[i]  # Move to the next line
            
            client.loop.create_task(saveImage(img, prompt, "color-printer"))
            
            return jsonify(res='success')
    return 'failure'


@app.route('/print_response', methods = ['POST'])
def handle_print_response():
    with open('prompt.txt', 'r') as file:
        current_prompt = file.read().replace('\n', '')

    toPrintImgPath = printRandomImg(current_prompt)

    if toPrintImgPath == "":
        logEvent("color-print")
        return 'success'

    os.system('python thermal-print.py '+toPrintImgPath+' > /dev/rfcomm0')
    logEvent("thermal-print")
    return 'success'
    

 
@app.route('/get_prompt', methods = ['GET'])
def prompt_GET():
    with open('prompt.txt', 'r') as file:
        current_prompt = file.read().replace('\n', '')
    return jsonify({"prompt": current_prompt})

@app.route('/frontend')
def frontendHTML():
    return render_template('index.html')

def run_discord_bot_in_thread():
    # Important to make an event loop for the new thread
    asyncio.set_event_loop(asyncio.new_event_loop())
    client.run(DISCORD_TOKEN)

def connect_to_printer():
    # Important to make an event loop for the new thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    subprocess.Popen(['sudo', 'rfcomm', 'connect', '0', '24:54:89:AE:0A:51'])
    time.sleep(1)
    subprocess.Popen(['sudo', 'chmod', 'a+rw', '/dev/rfcomm0'])
'''  
frame_index = 0

def display_thread():
    asyncio.set_event_loop(asyncio.new_event_loop())
    time.sleep(2)
    # Display

    def play_video():
        global frame_index
        
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

        root.after(20, play_video)


    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes("-type", "splash")
    root.config(background = "#000000")
    root.title("Happi Display")

    cap = cv2.VideoCapture("blink.mp4")  # Replace with your video file

    label = tk.Label(root)
    label.pack(fill=tk.BOTH, expand=True)  # This makes the label expand to fill the window


    root.after(60, play_video)

    root.mainloop()
'''


if __name__ == '__main__':

    status = 'Not connected'
    while status == 'Not connected':
        response = os.system("ping -c 1 8.8.8.8")
        if response == 0:
            print('Connected to the Internet')
            status = 'Connected'
        else:
            print('Not connected to the Internet')
        time.sleep(2)

    staticUrl = subprocess.Popen(['ngrok', 'http', '--url=mongoose-full-barely.ngrok-free.app', '50298'])
    Thread(target=run_discord_bot_in_thread, daemon=True).start()
    Thread(target=connect_to_printer, daemon=True).start()
    # Thread(target=display_thread, daemon=True).start()

    app.run(host='0.0.0.0', port=50298, debug=False) 

    staticUrl.terminate()

