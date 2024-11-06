# Happi-Server

### Raspberry Pi Setup
##### Install the Following Libraries:
- *pip install flask*
- *pip install discord.py*
- *pip install Pillow*
- *pip install python-dotenv*
- *pip install gpiozero*
- *sudo apt install sqlite3*

raspberry pi pip installation guide:
python -m venv ~/py_envs
source ~/py_envs/bin/activate
python -m pip install NAMEOFWHATEVER

### phomemo printer instructions
24:54:89:AE:0A:51

bash commands:
bluetoothctl devices
bluetoothctl pair 24:54:89:AE:0A:51
sudo rfcomm connect 0 24:54:89:AE:0A:51
sudo chmod a+rw /dev/rfcomm0
thermal-print.py my-image.png > /dev/rfcomm0

### color printer instructions
0C:86:29:61:9B:14

sudo apt-get install bluetooth libbluetooth-dev
sudo pip install pybluez
sudo apt-get install obexftp


bash commands:
bluetoothctl pair 0C:86:29:61:9B:14
obexftp --nopath --noconn --uuid none --bluetooth 0C:86:29:61:9B:14 --channel 2 -p color.png

using ngork for free tunneling with permanent domain:
ngrok http --url=mongoose-full-barely.ngrok-free.app 50298

curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
	| sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
	&& echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
	| sudo tee /etc/apt/sources.list.d/ngrok.list \
	&& sudo apt update \
	&& sudo apt install ngrok

ngrok config add-authtoken 2oRkK1wgSOXSluBaBvt2il8Xedi_dPazXWyV1P4c5QZm3Mxc

ngrok http --url=mongoose-full-barely.ngrok-free.app 50298

https://mongoose-full-barely.ngrok-free.app/

### API Ussage

#### add_ipad_response : POST
**header: password**
**body: {"image_base64", "prompt"}**
image must be encoded as base64
make sure the base64 doesn't include the tag *"data:image/png;base64,"*


#### add_qr_response : POST
**header: password**
**body: {"image_base64", "test_response", "prompt"}**
image must be encoded as base64
make sure the base64 doesn't include the tag *"data:image/png;base64,"*
