# Happi-Server

### Raspberry Pi Setup
##### Install the Following Libraries:
- *pip install flask*
- *pip install discord.py*
- *pip install python-dotenv*
- *pip install gpiozero*
- *sudo apt install sqlite3*

raspberry pi pip installation guide:
python -m venv ~/py_envs
source ~/py_envs/bin/activate
python -m pip install NAMEOFWHATEVER

pip install git+https://github.com/theacodes/phomemo_m02s.git

python3 -m phomemo_m02s --mac 00:15:83:37:xx:xx /path/to/image.png


using ngork for free tunneling with permanent domain:
ngrok http --url=mongoose-full-barely.ngrok-free.app 50298

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
