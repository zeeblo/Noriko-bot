from discord.ext import commands
import discord

class personal(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def poke(self, ctx):
        return await ctx.send('ow')




async def setup(bot):
    await bot.add_cog(personal(bot))