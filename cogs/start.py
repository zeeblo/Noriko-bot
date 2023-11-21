import discord
from discord.ext import commands
from discord import app_commands
from utils import data as db
from utils.data import Sanitizer
from utils.ai_tools import AIGen
from utils import chat
from better_profanity import profanity


class Start(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.sanitizer = Sanitizer()

    @app_commands.command(name="add_channel")
    @commands.is_owner()
    async def add_channel(self, interaction:discord.Interaction, channel_id:str):
        """Add a channel for novels to be initialized in"""
        if isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message(content="**This cannot be done in a Thread!**")

        if not self.bot.get_channel(int(channel_id)):
            return await interaction.response.send_message(content="This isn't a valid channel ID")

        await db.dbase.appendChannel(interaction, int(channel_id))
        
        return await interaction.response.send_message(content="Channel added to list of available chats!")




    @app_commands.command(name="talk")
    async def talk(self, interaction:discord.Interaction, chat_name:str):
        """Start exploring a unique visual novel"""
        if isinstance(interaction.channel, discord.Thread) or isinstance(interaction.channel, discord.DMChannel):
            return await interaction.response.send_message(content="I cant use that command here")
        #TODO: Check if chat_name returns an empty string
        user_id = interaction.user.id
        channel = interaction.channel.id
        chat_name = await self.sanitizer.cleanInput(text=chat_name)

        if profanity.contains_profanity(chat_name) or (await AIGen(user_id, chat_name).hasProfanity(chat_name)):
            return await interaction.response.send_message("Mmmmmm... No. Try a different name, thanks.", ephemeral=True)

        channel_ = await db.dbase(user_id, chat_name).getChannelID(channel)
        if not channel_:
            return await interaction.response.send_message("The owner of this server hasn't **whitelisted.** this channel apparently")
        
        name_check = await db.dbase(user_id, chat_name).getChatName
        if name_check:
            return await interaction.response.send_message("We already have a thread with this name...")
        
        LLM = await db.dbase(user_id=user_id, chat_name=chat_name).getChatModel
        model = 'text-bison-001' if not LLM else LLM[0]

        thread = await interaction.channel.create_thread(name=chat_name)
        thread_msg = await thread.send(f"{interaction.user.mention}")
        await thread_msg.pin()

        return await chat.SetupChat(self.bot, user_id, chat_name).setup(interaction, model)




async def setup(bot):
    await bot.add_cog(Start(bot))