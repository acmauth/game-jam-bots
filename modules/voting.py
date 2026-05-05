import discord
from discord.ext import commands
from discord import ApplicationContext as Context
from utils.database_handler import SQLiteHandler as sql

class VotingCog(discord.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.slash_command()
    async def submissions(self, ctx: Context):
        await sql.gather_submissions()

    @commands.slash_command()
    async def vote(self, ctx: Context):
        pass

def setup(bot: commands.Bot):
    bot.add_cog(VotingCog(bot))