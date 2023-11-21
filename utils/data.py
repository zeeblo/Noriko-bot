from contextlib import asynccontextmanager
from utils.encrypt import passManager
import os
import sqlite3
import json

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
PATH = os.path.dirname(THIS_PATH)



@asynccontextmanager
async def get_db(db_name):
    conn = sqlite3.connect(db_name)
    yield conn.cursor()
    conn.commit()
    conn.close()




class dbase:

    def __init__(self, user_id, chat_name):
        self.user_id = user_id
        self.chat_name = chat_name

    @staticmethod
    async def c_tables():
        # NON-USER RELATED

        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("""CREATE TABLE IF NOT EXISTS channels (
                channel_id INT,
                PRIMARY KEY(channel_id)
            ) """)

        ##  USER SPECIFIC # #
    
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                user_id INT,
                PRIMARY KEY(user_id)
            ) """)

        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("""CREATE TABLE IF NOT EXISTS settings (
                user_id INT,
                chat_model TEXT,
                LLM TEXT,
                DMS BOOLEAN,
                img_model TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            ) """)

        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("""CREATE TABLE IF NOT EXISTS private_settings (
                user_id INT,
                gpt_token BLOB,
                palm_token BLOB,
                img_token BLOB,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            ) """)

        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("""CREATE TABLE IF NOT EXISTS chat_info (
                user_id INT,
                chat_name TEXT,
                thread INT,
                PRIMARY KEY(user_id, chat_name)
            ) """)



        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("""CREATE TABLE IF NOT EXISTS chat_logs (
                user_id INT,
                chat_name TEXT,
                role TEXT,
                content TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(chat_name) REFERENCES chat_info(user_id)
            ) """)




    # INSERT | NON-USER RELATED

    async def appendChannel(interaction, channel_id):
        try:
            async with get_db(f"{PATH}/data/data.db") as c:
                c.execute("INSERT INTO channels(channel_id) VALUES(?)", (channel_id,))
        except sqlite3.IntegrityError:
            return await interaction.response.send_message(content="Already whitelisted.")
            

    ## INSERT | USER SPECIFIC  # #

    async def appendUserMetadata(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (self.user_id,))
            

    async def appendChatMetadata(self, interaction, thread):
        try:
            async with get_db(f"{PATH}/data/data.db") as c:
                c.execute("INSERT INTO chat_info(user_id, thread, chat_name) VALUES(?, ?, ?)",
                        (self.user_id, thread, self.chat_name,))
        except sqlite3.IntegrityError:
            return await interaction.response.send_message("This chat name already exists!")
        
    async def appendSettings(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("INSERT INTO settings(user_id, chat_model, LLM, DMS, img_model) VALUES(?, ?, ?, ?, ?)",
                    (self.user_id, "palm", "text-bison-001", True, None,))
            
    async def appendPrivateSettings(self):
        raw_token = bytes(info().getDefaultToken["PALM_TOKEN"], 'utf-8')
        pw = await passManager(self.user_id).hide(raw_token)

        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("INSERT INTO private_settings(user_id, gpt_token, palm_token, img_token) VALUES(?, ?, ?, ?)",
                    (self.user_id, None, pw, None,))

    async def appendChatHistory(self, role, msg):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("INSERT INTO chat_logs(user_id, chat_name, role, content) VALUES(?, ?, ?, ?)",
                    (self.user_id, self.chat_name, role, msg,))
    



    ##  UPDATE | USER SPECIFIC ##

    async def updateThreadID(self, thread_id):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute(f"UPDATE chat_info SET thread = ? WHERE user_id = ?", (thread_id, self.user_id,))

    async def updateDMS(self, value):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("UPDATE settings SET DMS = ? WHERE user_id = ?", (value, self.user_id,))

    async def updateModel(self, model):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("UPDATE settings SET chat_model = ? WHERE user_id = ?", (model, self.user_id,))

    async def updateLLM(self, LLM):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("UPDATE settings SET LLM = ? WHERE user_id = ?", (LLM, self.user_id,))

    async def updatePalmToken(self, token):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("UPDATE private_settings SET palm_token = ? WHERE user_id = ?", (token, self.user_id,))

    async def updateGPTToken(self, token):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("UPDATE private_settings SET gpt_token = ? WHERE user_id = ?", (token, self.user_id,))



    ##  GET | NON-USER  # #


    async def getChannelID(self, channel_id):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT channel_id FROM channels WHERE channel_id = ?;", (channel_id,))
            result = c.fetchone()
        return result



    ##  GET | USER SPECIFIC # #

    @property
    async def getUserID(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT user_id FROM users WHERE user_id = ?", (self.user_id,))
            result = c.fetchone()
        return result


    @property
    async def getSettings(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT * FROM settings WHERE user_id = ?", (self.user_id,))
            result = c.fetchall()
        return result
    
    @property
    async def getPrivateSettings(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT * FROM private_settings WHERE user_id = ?", (self.user_id,))
            result = c.fetchall()
        return result


    @property
    async def getDMSValue(self):
        try:
            async with get_db(f"{PATH}/data/data.db") as c:
                c.execute("SELECT DMS FROM settings WHERE user_id = ?", (self.user_id,))
                result = c.fetchone()[0]
            return result
        except TypeError:
            return None
        except KeyError:
            return None

    @property
    async def getChatInfo(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT * FROM chat_info WHERE user_id = ?", (self.user_id,))
            result = c.fetchall()
        return result


    @property
    async def getChatName(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT chat_name FROM chat_info WHERE user_id = ? AND chat_name = ?", (self.user_id, self.chat_name,))
            result = c.fetchone()
        return result
    

    @property
    async def getPalmToken(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT palm_token FROM private_settings WHERE user_id = ?", (self.user_id,))
            result = c.fetchone()
        return result[0]
    

    @property
    async def getGPTToken(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT gpt_token FROM private_settings WHERE user_id = ?", (self.user_id,))
            result = c.fetchone()
        return result[0]


    @property
    async def getChatModel(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT chat_model FROM settings WHERE user_id = ?", (self.user_id,))
            result = c.fetchone()
        return result
    
    @property
    async def getLLM(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT LLM FROM settings WHERE user_id = ?", (self.user_id,))
            result = c.fetchone()
        return result[0]




    async def getChatHistory(self, mode):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("SELECT role, content FROM chat_logs WHERE user_id = ? AND chat_name = ?", (self.user_id, self.chat_name,))
            result = c.fetchall()

        history = []
        if mode == "palm":
            for row in result:
                if row[0] == 'palm':
                    history.append(f"{row[1]}")

        elif mode == "gpt":
            for row in result:
                if row[0] == 'user' or row[0] == 'assistant':
                    history.append({'role': row[0], 'content': row[1]})
        return history




    async def getThreadID(self, chat_name):
        try:
            async with get_db(f"{PATH}/data/data.db") as c:
                c.execute("SELECT thread FROM chat_info WHERE user_id = ? AND chat_name = ?", (self.user_id, chat_name,))
                result = c.fetchone()
            return result[0]
        except KeyError:
            return None




##  DELETE | USER SPECIFIC # #
    @property
    async def delChatLog(self):
        async with get_db(f"{PATH}/data/data.db") as c:
            c.execute("DELETE FROM chat_logs WHERE user_id = ? AND chat_name = ?", (self.user_id, self.chat_name,))




class info:
    
    @property
    async def getExamplePrompts(self):
        with open(f'{PATH}/assets/prompts/LLM_templates.json', 'r') as f:
            examplePrompts = json.load(f)
        return examplePrompts
    
    @property
    async def getHelpInfo(self):
        with open(PATH +'/assets/info/help.json', 'r') as f:
            help = json.load(f)
        return help[0]
    
    @property
    async def getCmdsInfo(self):
        with open(PATH +'/assets/info/cmds.json', 'r') as f:
            desc = json.load(f)
        return desc

    @property
    def getModels(self):
        with open(PATH + "/assets/info/LLM_info.json", "r") as f:
            models = json.load(f)
        return models
    
    @property
    def getSettings(self):
        with open(PATH + "/assets/info/settings.json", "r") as f:
            settings = json.load(f)
        return settings
    
    @property
    def getAPISetup(self):
        with open(PATH + "/assets/info/setup.json", "r") as f:
            setup = json.load(f)
        return setup
    
    @property
    def getDefaultToken(self):
        with open(f'{PATH}/config.json', 'rb') as f:
            config = json.load(f)
        return config
    
    
    

class Misc:
    
    @property
    async def getDummyText(self):
        with open(f'{PATH}/assets/static_phrases/dummy_msgs.json') as f:
            misc = json.load(f)
        return misc

    @property
    def getByeMsgs(self):
        with open(PATH + "/assets/static_phrases/bye.json", "r") as f:
            bye = json.load(f)
        return bye
    
    @property
    def getPoke(self):
        with open(PATH + "/assets/static_phrases/poke.json", "r") as f:
            poke = json.load(f)
        return poke




import string
class Sanitizer:
    async def cleanInput(self, text: str, default_allowed: str = " ", custom_allowed: str = ",._)("):
        """Sanitize user input by getting rid of special chars"""
        valid_chars = set(string.ascii_letters + string.digits +
                          default_allowed + custom_allowed)
        raw_text = text.strip()
        sanitized_text = ''.join(char for char in raw_text if char in valid_chars)
        return sanitized_text

    async def getValidChars(self, extraChars: str = ''):
        return set(string.ascii_letters + string.digits + ' _-)(' + extraChars)