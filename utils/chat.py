import discord
import os
from utils.data import dbase
from utils.manager import AIManager

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
PATH = os.path.dirname(THIS_PATH)

class SetupChat:
    def __init__(self, bot, user_id, chat_name):
        self.bot = bot
        self.user_id = user_id
        self.chat_name = chat_name
        self.aiManager = AIManager(bot, user_id, chat_name)
    

    async def setup(self,
                    message: discord.Message,
                    msg: str = 'hey',
                    thread: bool = False,
                    ping: bool = False,
                    channel: discord.channel = None):

        check_id = await dbase(user_id=self.user_id, chat_name=self.chat_name).getUserID
        resume = True if check_id else False

        get_mdl = await dbase(user_id=self.user_id, chat_name=self.chat_name).getChatModel
        model = 'palm' if not get_mdl else get_mdl[0]

        if resume == True:
            pass
        else:
            # Create Metadata for User and chat
            await dbase(self.user_id, self.chat_name).appendUserMetadata()
            await dbase(self.user_id, self.chat_name).appendSettings()
            await dbase(self.user_id, self.chat_name).appendPrivateSettings()
            await dbase(self.user_id, self.chat_name).appendChatMetadata(message, message.channel.id)

        return await self.chat(model=model, userInput=msg, ping=ping, channel=channel, message=message) 
 



    async def chat(self, model, userInput, ping, message, channel):
        if ping:
            return await self.aiManager.recursivePingChat(model, userInput, message, channel)
        elif model == 'gpt':
            reply = await self.aiManager.gptResponse(userInput)
        elif model == "palm":
            reply = await self.aiManager.palmResponse(userInput)

        return reply
