import discord.client
import discord.message
from flask import Flask, request, json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import os
import discord
import asyncio
from threading import Thread
import sqlite3
from gpiozero import Button
import subprocess
import time

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







# Discord bot 

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
VERIFY_CHANNEL_ID = 1303107546164363286
PROMPT_CHANNEL_ID = 1303463361442353213



class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        channel = client.get_channel(PROMPT_CHANNEL_ID)
        await channel.send('Current Prompt:\n'+current_prompt)
        #await channel.purge()


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
                unverifyResponse(img_id)
            elif approval_reaction and approval_reaction.count > 1:
                verifyResponse(img_id)

@client.event
async def on_message(message):
    if message.author != client.user and message.channel.id == PROMPT_CHANNEL_ID and message.content:
        current_prompt = message.content
       
        with open('prompt.txt', 'w') as file:
            file.write(current_prompt)
        
        channel = client.get_channel(PROMPT_CHANNEL_ID)
        await channel.send('Current Prompt:\n'+current_prompt)

        
        



async def sendImageToVerify(imagePath):
    channel = client.get_channel(VERIFY_CHANNEL_ID)
    
    msg = await channel.send(file=discord.File(imagePath))
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')


async def saveImage(image, prompt, image_print_type):
    img_path = 'responses/'+str(saveResponseToDB(prompt, image_print_type))+'.png'
    image.save(img_path, 'PNG')

    channel = client.get_channel(VERIFY_CHANNEL_ID)
    #await channel.send('test')
    msg = await channel.send(file=discord.File(img_path))
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')


async def getPrompt():
    channel = client.get_channel(VERIFY_CHANNEL_ID)






# Flask endpoint


app = Flask(__name__)

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

            img = Image.open(BytesIO(base64.decodebytes(bytes(img_base64, "utf-8"))))

            img.thumbnail(thermal_printer_size)
            img.save('my-image.png')

            mod_img = Image.new("RGB", thermal_printer_size, (204, 255, 229))
            mod_img.paste(img, (0, 400))
            
            # 650
            draw = ImageDraw.Draw(mod_img)

            font = ImageFont.truetype("font.ttf", size=40)
            text_width, text_height = draw.textsize(prompt, font)
            text_x = (thermal_printer_size[0] - text_width) // 2  # Center text
            text_y = 20
            draw.text((text_x, text_y), prompt, fill=(0, 0, 0), font=font)

            client.loop.create_task(saveImage(mod_img, prompt, "thermal-printer"))

            return 'success'
        return 'failure'
    
    
    
# add_qr_response POST request
@app.route('/add_qr_response', methods = ['POST'])
def handle_add_qr_response():
    if request.method == 'POST':
        if request.headers['password'] == 'wegojapan':
            data = json.loads(request.data)
        
            img_base64 = data['image_base_64']
            img = Image.open(BytesIO(base64.decodebytes(bytes(img_base64, "utf-8"))))
            img.save('my-image.png')

            text_response = data['image_base64']

            prompt = data['prompt']

            return 'success'
        return 'failure'
    

 
@app.route('/get_prompt', methods = ['GET'])
def prompt_GET():
    return current_prompt


def run_discord_bot_in_thread():
    # Important to make an event loop for the new thread
    asyncio.set_event_loop(asyncio.new_event_loop())
    client.run(DISCORD_TOKEN)


def print_button_listener():
    # Important to make an event loop for the new thread
    asyncio.set_event_loop(asyncio.new_event_loop())

    button = Button(2)

    subprocess.run(['sudo', 'rfcomm', 'connect', '0', '24:54:89:AE:0A:51'])

    time.sleep(5)

    while True:

        button.wait_for_press()

        subprocess.run(['python', 'thermal-print.py', 'image.png', '>', '/dev/rfcomm0'])

        time.sleep(10)



    


if __name__ == '__main__':
    subprocess.run(['ngrok', 'http', '--url=mongoose-full-barely.ngrok-free.app', '50298'])
    Thread(target=run_discord_bot_in_thread, daemon=True).start()
    Thread(target=print_button_listener, daemon=True).start()

    app.run(host='0.0.0.0', port=50298, debug=False) 

