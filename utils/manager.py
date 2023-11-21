from utils.data import info, dbase, Misc
from utils.ai_tools import AIGen
import json
import asyncio
import random

class AIManager():

    def __init__(self, bot, user_id, chat_name):
        self.bot = bot
        self.user_id = user_id
        self.chat_name = chat_name
        self.dbase = dbase(user_id, chat_name)
    
    @property
    def enforceContextActions(self):
        """The AI will sometimes get go off the rails and not follow the desired
        outputs, this is intended to help mitigate that by reminding it w/ appended
        prompts."""
        with open(f"{self.bot.PATH}/assets/prompts/noriko_context.json") as f:
            context = json.load(f)
        return context
    

    async def addKeywords(self, reply):
        """Codes used to spice up the writing style of the AI such as swearing"""
        with open(f"{self.bot.PATH}/assets/misc/codes.json") as f:
            codes = json.load(f)
        for i in codes:
            reply = reply.replace(i, codes[i])
        return reply




    async def removeKeywords(self, reply:str):
        """Get rid of keywords and return a clean string"""
        if reply.startswith('[CONTENT]'):
            reply = reply.split("[CONTENT]")[1].strip()
            reply = reply.replace('7h7', 'shit')
            reply = reply.replace('8h8', 'fuck')
        else:
            # If the user said something deemed inappropriate it wont follow the
            # [CONTENT] guideline, so return a random phrase instead.
            dummyText = await Misc().getDummyText
            return random.choice(dummyText)
        return reply




    async def recursivePingChat(self, model, userInput, message, channel):
        self.bot.ongoing[self.user_id] = True
        if model == 'gpt':
            reply = await self.gptResponse(userInput)
        elif model == "palm":
            reply = await self.palmResponse(userInput)

        # An error happened
        if reply[0] == False:
            await message.reply(reply[1])
            return self.bot.ongoing.pop(self.user_id)

        await message.channel.send(f"<@{self.user_id}> {reply}")
        try:
            raw_usr_msg = (await self.bot.wait_for("message",
            check=lambda message: message.author.id == int(self.user_id) and message.channel.id == channel.id, 
            timeout = 180)).content.strip()
        
            usr_msg = ''.join(char for char in raw_usr_msg)
            usr_msg = usr_msg[:256] # Number of characters allowed (not words)
        except asyncio.exceptions.TimeoutError:
            self.bot.ongoing.pop(self.user_id)
            byeText = Misc().getByeMsgs
            return await message.channel.send(f"<@{self.user_id}> " + str(random.choice(byeText)))
        
        if usr_msg == "<n_end_chat>":
            return
        
        if usr_msg == "<n_rst_chat>":
            self.bot.ongoing.pop(self.user_id)
            await dbase(self.user_id, self.chat_name).delChatLog
            print(f"Cleared: {self.chat_name}")
            return
        
        return await self.recursivePingChat(model, usr_msg, message, channel)




    async def gptResponse(self, msg: str):
        examples = (await info().getExamplePrompts)["gpt_3"]

        # Log user input
        await self.dbase.appendChatHistory('user', msg + " {<NAI>}")
        chat_history = await self.dbase.getChatHistory("gpt")

        contextAndUserMsg = examples + chat_history
        reply = await AIGen(user_id=self.user_id, chat_name=self.chat_name).getGPT(prompt=contextAndUserMsg)

        # Log AI input
        await self.dbase.appendChatHistory('assistant', reply)
        reply = await self.removeKeywords(reply)
        reply = await self.addKeywords(reply)
        return reply
    



    async def palmResponse(self, msg: str):
        examples = (await info().getExamplePrompts)["palm"]
        chat_history = await self.dbase.getChatHistory("palm")

        contextAndUserMsg = " ".join(examples) + "\n ".join(chat_history) + f"input: {msg}\noutput: "
        reply = await AIGen(user_id=self.user_id, chat_name=self.chat_name).getPALM(contextAndUserMsg)

        # An error happened
        if reply[0] == False:
            return reply[0], reply[1]

        dummyText = await Misc().getDummyText
        if reply not in dummyText:
            await self.dbase.appendChatHistory('palm', f"input: {msg}\noutput: {reply}")

        reply = await self.addKeywords(reply)
        return reply

