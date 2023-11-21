from discord.ext import commands
from discord.ext.commands import (CommandNotFound, CommandOnCooldown,
                                  MissingRequiredArgument)
from utils import data as db
from utils import chat
import discord
import json
import os
import random

PATH = os.path.dirname(os.path.realpath(__file__))

with open(f'{PATH}/config.json') as f:
    config = json.load(f)

TOKEN = config["BOT_TOKEN"]
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True
COMMAND_PREFIX = "nr!"




class Bot(commands.Bot):

    async def setup_hook(self):
        """This will be called before any events are dispatched"""
        for filename in os.listdir(f'{PATH}/cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
        await db.dbase.c_tables()

    async def on_ready(self):
        print(f"Running on version: {discord.__version__} ")




    async def on_message(self, message: discord.Message):
        if message.author == bot.user:
            return
        user_id = message.author.id
        msg = message.content.replace(bot.user.mention, bot.user.name)

        if message.content == "<n_end_chat>":
            try:
                bot.ongoing.pop(user_id)
                return await message.channel.send("👋")
            except KeyError:
                pass
            
        if isinstance(message.channel, discord.DMChannel):
            reply = await chat.SetupChat(bot, user_id, "<DM>").setup(message, msg)
            return await message.channel.send(reply)
        
        elif isinstance(message.channel, discord.Thread):
            reply = await chat.SetupChat(bot, user_id, message.channel.name).setup(message, msg, thread=True)
            return await message.channel.send(reply)
        
        elif bot.user.mentioned_in(message):
            try:
                if bot.ongoing[user_id]: return
            except KeyError: pass
            
            reply = await chat.SetupChat(bot, user_id, f"<{message.channel.id}>")\
            .setup(message, msg, ping=True, channel=message.channel)
        
        elif random.randint(1,80) == 2:
            if (await db.dbase(user_id=user_id, chat_name="<DM>").getUserID):

                DMS_State = await db.dbase(user_id=user_id, chat_name="<DM>").getDMSValue
                if DMS_State != True: return

                with open(PATH + "/assets/static_phrases/rnd_dms.json") as f:
                    msg = json.load(f)
                await message.author.send(random.choice(msg))

        await bot.process_commands(message)




bot = Bot(command_prefix=COMMAND_PREFIX,
          intents=INTENTS,
          case_insensitive=True,
          allowed_mentions=discord.AllowedMentions(roles=False, everyone=False),
          owner_ids=[1063386002955190312]
        )
bot.remove_command('help')
bot.PATH = PATH
bot.ongoing = {}


@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Used to update all slash commands when a change is made to them"""
    await ctx.send("Attemping to sync...")
    try:
        synced = await bot.tree.sync()
    except Exception as e:
        print(f"Error during sync: {e}")
    return await ctx.send(f"{len(synced)} commands were synced.")


@bot.command()
@commands.is_owner()
async def going(ctx):
    return await ctx.send(f"Ongoing dict: {bot.ongoing}")



if __name__ == "__main__":
    bot.run(TOKEN)
