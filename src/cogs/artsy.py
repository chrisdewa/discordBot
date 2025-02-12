# A good template for cogs
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
ART_TOKEN = os.getenv('ART_API')


class artsy(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot



async def setup(bot: commands.Bot):

    await bot.add_cog(
        artsy(bot)
    )
