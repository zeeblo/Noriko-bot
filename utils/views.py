from discord import Interaction, TextStyle, SelectOption
from discord.ui import Modal, TextInput

from utils.data import info, dbase
from utils import chat
from utils.encrypt import passManager

import discord
import io

class ChatOptions(discord.ui.View):

    def __init__(self, user_id, models):
        super().__init__()
        self.user_id = user_id
        self.models = models
        self.add_item(SelectChatModel(user_id=self.user_id, models=self.models))


class SelectChatModel(discord.ui.Select):

    def __init__(self, user_id, models):
        self.user_id = user_id
        self.models = models
        options = [ SelectOption(label=m) for m in self.models ]
        super().__init__(placeholder=f"Select LLM",
                         max_values=1,
                         min_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            if self.values[0] == "None":
                return await interaction.response.send_message(f"**N/A:**")
            
            await dbase(self.user_id, chat_name=None).updateLLM(self.values[0])
            return await interaction.response.send_message(f"**Success:** You're now currently using {self.values[0]}")

    



class SettingsOptions(discord.ui.View):

    def __init__(self, user_id, mode):
        super().__init__()
        self.user_id = user_id
        self.mode = mode
        self.add_item(SelectSettings(user_id=self.user_id, mode=self.mode))


class SelectSettings(discord.ui.Select):

    def __init__(self, user_id, mode):
        self.settings = info().getSettings
        self.user_id = user_id
        self.mode = mode
        options = [ SelectOption(label=i) for i in self.settings ]
        super().__init__(placeholder=f"Select the config you want to change",
                         max_values=1,
                         min_values=1,
                         options=options)
        

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == int(self.user_id)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            embed = discord.Embed(title=self.values[0], description=f"> {self.settings[self.values[0]][1]}", color=0xF875AA)
            embed.add_field(name="<:white_small_square:1172829243072327680> Mode", value=f"└ {self.mode}", inline=False)

            view = self.settings[self.values[0]][0]
            if view == "switch":
                view = CurrentMode(self.user_id, self.mode)
            elif view == "form":
                view = TokenForm(self.user_id)
                return await interaction.response.send_modal(view)

            return await interaction.response.send_message(embed=embed, view=view)
        







class CurrentMode(discord.ui.View):

    def __init__(self, user_id, mode):
        super().__init__()
        self.user_id = user_id
        self.mode = mode
        self.enabled = 'enabled' in self.mode
        self.disabled = not 'enabled' in self.mode
        
        enabled_button = discord.ui.Button(label='Enable', style=discord.ButtonStyle.success, disabled=self.enabled, custom_id="enabled_button")
        disabled_button = discord.ui.Button(label='Disable', style=discord.ButtonStyle.danger, disabled=self.disabled, custom_id="disabled_button")
        
        enabled_button.callback = self.enable_button_click
        disabled_button.callback = self.disable_button_click
        
        self.add_item(enabled_button)
        self.add_item(disabled_button)

    async def enable_button_click(self, interaction: discord.Interaction):
        await self.handle_enable_disable(interaction, True)

    async def disable_button_click(self, interaction: discord.Interaction):
        await self.handle_enable_disable(interaction, False)

    async def handle_enable_disable(self, interaction: discord.Interaction, enable: bool):
        if enable:
            message = "The mode has been set to ENABLED."
        else:
            message = "The mode has been set to DISABLED."
        
        await dbase(user_id=self.user_id, chat_name=None).updateDMS(enable)

        await interaction.response.send_message(message, ephemeral=True)

        self.children[0].disabled = enable  # Enabled button
        self.children[1].disabled = not enable  # Disabled button

        await interaction.message.edit(view=self)




class TokenForm(Modal):
    def __init__(self, bot):
        super().__init__(title="API TOKEN", timeout=None)
        self.bot = bot
        self.interaction = None
        self.models = TextInput(label="AI Model",
                               placeholder="palm",
                               min_length=1,
                               style=TextStyle.short)
        self.token = TextInput(label="API Token",
                               placeholder="********",
                               min_length=4,
                               style=TextStyle.short)
        self.add_item(self.models)
        self.add_item(self.token)

    async def on_submit(self, interaction: Interaction):
        user_id = interaction.user.id
        model = self.models.value
        token = bytes(self.token.value, 'utf-8')
        examples = info().getModels

        models = [m['name'].lower() for m in examples]

        if model.lower() in models:
            await dbase(user_id, chat_name=None).updateModel(model)
            pw = await passManager(user_id).hide(token)

            if model == 'palm':
                await dbase(user_id, chat_name=None).updatePalmToken(pw)
                await dbase(user_id, chat_name=None).updateLLM('text-bison-001')
            elif model == 'gpt':
                await dbase(user_id, chat_name=None).updateGPTToken(pw)
                await dbase(user_id, chat_name=None).updateLLM('gpt-3.5-turbo-16k')
                
            return await interaction.response.send_message(
                "**Success!** Remember to never expose your token publicly. If you believe it has been leaked, you can destroy it on the website you generated it on",
                    ephemeral=True)
        else:
            return await interaction.response.send_message(
                f"**Failed:** You entered an invalid name. Here are your available choices: {', '.join(models)} ",
                    ephemeral=True)




class ImagePaginationView(discord.ui.View):
    def __init__(self, interaction, model, image_urls, description):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.model = model
        self.image_urls = image_urls
        self.description = description
        self.current_page = 0 

        back_button = discord.ui.Button(label='Back', style=discord.ButtonStyle.primary, disabled=True, custom_id="back_button")
        next_button = discord.ui.Button(label='Next', style=discord.ButtonStyle.primary, disabled=False, custom_id="next_button")
        
        back_button.callback = self.back_button_click
        next_button.callback = self.next_button_click
        
        self.add_item(back_button)
        self.add_item(next_button)


    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self.interaction.user:
            return True
        else:
            await interaction.response.send_message(content="Only the author can respond to this",
                                                     ephemeral=True)
            return False

    async def next_button_click(self, interaction: discord.Interaction):
        if self.current_page < len(self.image_urls) - 1:
            self.current_page += 1

            # If it's last page disable the Next button.
            if self.current_page == len(self.image_urls) - 1:
                self.children[1].disabled = True  

            self.children[0].disabled = False  
            await self.update_image(interaction)

    async def back_button_click(self, interaction):
        if self.current_page > 0:
            self.current_page -= 1

            # If it's the first page disable the Back button.
            if self.current_page == 0:
                self.children[0].disabled = True
            self.children[1].disabled = False

            await self.update_image(interaction)


    async def update_image(self, interaction: discord.Interaction):
        file = discord.File(io.BytesIO(self.image_urls[self.current_page]), filename="setup.png")
        embed = discord.Embed(title=f"{self.model} API Setup",
                              description=f"**Step {self.current_page + 1} out of {len(self.image_urls)}:** {self.description[self.current_page]}",
                              color=0xF875AA)
        embed.set_image(url="attachment://setup.png")

        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)