from cryptography.fernet import Fernet
import json
import os

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
PATH = os.path.dirname(THIS_PATH)

with open(f'{PATH}/config.json', 'rb') as f:
    key = json.load(f)['Key']

class passManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.crypt = Fernet(key)

    async def hide(self, password):
        pw = self.crypt.encrypt(password)
        return pw

    async def show(self, password):
        pw = str(self.crypt.decrypt(password), 'utf-8')
        return pw