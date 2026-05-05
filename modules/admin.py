import discord, json, requests, html
from discord.ext import commands
from discord.ext.commands import Context
from utils.utilities import active_gamejam_id, active_gamejam_name
from utils.database_handler import SQLiteHandler as sql

class AdminCog(discord.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gathersubmissions(self, ctx: Context):
        endpoint = f"https://itch.io/jam/{str(active_gamejam_id)}/entries.json"
        games = requests.get(endpoint).json()

        i = 0 # game counter
        for game in games["jam_games"]:
            game_url = game["game"]["url"]
            game_title = game["game"]["title"]
            game_id = game["game"]["id"]

            print(game["game"])

            sub_html = html.unescape(requests.get(f"https://itch.io/jam/{active_gamejam_name}/rate/{str(game_id)}").text)
            # team = sub_html[
            #     sub_html.find("What is your team's name?"):
            #     (sub_html.find("What is your team's name?")+sub_html[sub_html.find("What is your team's name"):]
            #      .find("</span>"))].replace("</strong><br/><span>", "")
            
            await sql.submit_game(f"Team {str(i)}", game_title, game_url, game_id)
            i += 1
        
        await ctx.send(f"All submissions were gathered successfully (counted {str(i)} games).")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearsubmissions(self, ctx: Context):
        await sql.clear_submissions()
        await ctx.send("Deleted all registered submissions.")


def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))