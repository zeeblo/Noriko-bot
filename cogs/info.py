from utils.data import info
from utils.data import dbase
from utils.views import SettingsOptions, ChatOptions
from discord.ext import commands
from discord import app_commands
from utils.data import info
from utils.views import ImagePaginationView
from utils.encrypt import passManager
import discord
import json
import io


class CustomHelp(commands.Cog):
  
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help")
    async def help(self, interaction:discord.Interaction):
        """Brief overview of how to use the bot going forward"""
        help_info = await info().getHelpInfo
        await interaction.response.send_message(content=help_info, ephemeral=True)




    @app_commands.command(name="commands")
    async def commands(self, interaction:discord.Interaction):
        """List of all commands available to the user"""
        cmds_info = await info().getCmdsInfo

        embed = discord.Embed(description=cmds_info['desc'], color=0xF875AA)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)

        for category, commands_list in cmds_info["cmds"].items():
            embed.add_field(name=f"{category} - `{commands_list.count(',') + 1}`", value=commands_list, inline=False)

        await interaction.response.send_message(embed=embed)




    @app_commands.command(name="setup")
    async def setup(self, interaction: discord.Interaction, model: str = "palm"):
        """Guide for how to get API key for specific API"""
        api = info().getAPISetup[model]
        descs = []
        imgs = []

        for i in api:
            desc = api[i]["desc"]
            img = api[i]["img"]

            with open(f"{self.bot.PATH}/{img}", "rb") as f:
                img = f.read()
            imgs.append(img)
            descs.append(desc)

        file = discord.File(io.BytesIO(imgs[0]), filename="setup.png")
        
        embed = discord.Embed(title=f"{model.capitalize()} API Setup",
                            description=f"**Step 1 out of {len(api)}:** {descs[0]}",
                            color=0xF875AA)
        embed.set_image(url="attachment://setup.png")
        
        view = ImagePaginationView(interaction, model.capitalize(), imgs, descs)
        
        await interaction.response.send_message(embed=embed, file=file, view=view)




    @app_commands.command(name="ai-models")
    async def LLMS(self, interaction:discord.Interaction):
        """List of all the AI models"""
        embed = discord.Embed(title="AI models ",
        description="List of all available AI models.",
        color=0xF875AA)
        
        user_id = interaction.user.id
        static_models = info().getModels
        user_model = await dbase(user_id, chat_name=None).getChatModel

        models = ["None"]
        try:
            for m in static_models:
                if user_model[0].lower() == m['name'].lower():
                    models = m['models']
        except TypeError:
            pass

        for i in static_models:
            embed.add_field(name=i["name"], value=i["long_desc"], inline=False)
        await interaction.response.send_message(embed=embed, view=ChatOptions(user_id, models))




    @app_commands.command(name="keywords")
    async def keywords(self, interaction:discord.Interaction):
        """Keywords used to activate certain actions"""
        end_chat = "**<n_end_chat>** used to end ur current talking session if you've recently pinged the bot"
        reset_chat = "**<n_rst_chat>** used to clear the database of ur current talking session"
        await interaction.response.send_message(f"{end_chat}\n{reset_chat}")




    @app_commands.command(name="chats")
    async def chats(self, interaction:discord.Interaction):
        """Display chat session names"""
        embed = discord.Embed(color=0xF875AA)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar)

        chat_info = await dbase(user_id=interaction.user.id, chat_name=None).getChatInfo
        chat_names = [f"`{chat[1]}`" for chat in chat_info]
        names_str = ", ".join(chat_names)

        embed.add_field(name=f"Threads", value=names_str, inline=True)

        await interaction.response.send_message(embed=embed)




    async def loadDefault(self, user_id):
        """Reload old default settings"""
        await dbase(user_id, chat_name=None).updateModel('palm')

        raw_token = bytes(info().getDefaultToken["PALM_TOKEN"], 'utf-8')
        pw = await passManager(user_id).hide(raw_token)

        await dbase(user_id, chat_name=None).updatePalmToken(pw)
        await dbase(user_id, chat_name=None).updateLLM('text-bison-001')




    @app_commands.command(name="settings")
    async def settings(self, interaction:discord.Interaction, default:bool=False):
        """Display overview of settings"""
        # Wip Messy Settings
        user = interaction.user
        embed = discord.Embed(description="Select a config option for more info", title="Settings", color=0xF875AA)
        embed.set_author(name=user.name, icon_url=user.display_avatar)

        user_info = await dbase(user_id=user.id, chat_name=None).getUserID
        if not user_info:
            return await interaction.response.send_message("You haven't been added to the database yet")
        
        if default:
            await self.loadDefault(user_id=user.id)

        
        settings_info = await dbase(user_id=user.id, chat_name=None).getSettings
        private_info = await dbase(user_id=user.id, chat_name=None).getPrivateSettings

        for i in settings_info:
            chat_mdls = i[1]
            LLM = i[2]
            DMS = i[3]

        for v in private_info:
            palm_token = False if v[2] == None else True
            gpt_token = False if v[1] == None else True
        
        mode = "<:enabled:1173729621959790743> **enabled**" if DMS else "<:disabled:1173729641534595092> **disabled**"

        embed.add_field(name="<:white_small_square:1172829243072327680> Chat Model", value=f"└ `{chat_mdls}` | `{LLM}`", inline=False)
        embed.add_field(name="<:white_small_square:1172829243072327680> DMS", value=f"└ {mode}", inline=False)
        embed.add_field(name="<:white_small_square:1172829243072327680> PaLM Key", value=f"└ `{palm_token}`", inline=False)
        embed.add_field(name="<:white_small_square:1172829243072327680> GPT Key", value=f"└ `{gpt_token}`", inline=False)

        await interaction.response.send_message(embed=embed, view=SettingsOptions(user.id, str(mode)), ephemeral=False)

 


async def setup(bot):
  await bot.add_cog(CustomHelp(bot))