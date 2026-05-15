import discord, csv, requests, html, json
from discord.ext import commands
from discord.ext.commands import Context
from utils.utilities import active_gamejam_id, active_gamejam_name, embed_colour
from utils.database_handler import SQLiteHandler as sql, JSONHandler as jsondb

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

            req = requests.get(f"https://itch.io/jam/{active_gamejam_name}/rate/{str(game_id)}")
            req.encoding = req.apparent_encoding

            sub_html = html.unescape(req.text)
            team = sub_html[
                sub_html.find("What is your team's name?"):
                (sub_html.find("What is your team's name?")+sub_html[sub_html.find("What is your team's name"):]
                 .find("</span>"))].replace("</strong><br/><span>", "").replace("What is your team's name?", "")
            
            # await sql.submit_game(f"Team {str(i)}", game_title, game_url, game_id)
            await sql.submit_game(team, game_title, game_url, game_id)
            i += 1
        
        # await sql.submit_game(ctx.author.name, "Test game", "https://www.google.com", "676767")
        await ctx.send(f"All submissions were gathered successfully (counted {str(i)} games).")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearsubmissions(self, ctx: Context):
        await sql.clear_submissions()
        await ctx.send("Deleted all registered submissions.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def exportratings(self, ctx: Context):
        dataset = await jsondb.get_all_ratings()
        
        embed = discord.Embed(
            colour = embed_colour,
            title = "Community ratings"
        )

        for key, value in dataset.items():
            game = key
            users = 0
            rating = 0
            for user, rating_dict in value.items():
                rating += (rating_dict["theme_cohesion"] + rating_dict["assets"] + rating_dict["enjoyment"] + rating_dict["gameplay"])/4
                users += 1
            
            rating = rating/users

            embed.add_field(
                name = game,
                value = f"Mean rating: **{str(rating)}**",
                inline = False
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rawratings(self, ctx: Context):
        file = discord.File("data/votes.json")
        await ctx.send(
            content="The ratings file",
            file=file
        )

    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def forcedeleteteam(self, ctx: Context, *team):
        final_team = " ".join(team)
        errors = []

        try: await sql.delete_team(final_team)
        except: errors.append("SQLite Database did not contain the team")

        try: await discord.utils.get(ctx.guild.roles, name=final_team).delete(reason=f'Deleting team {final_team}')
        except: errors.append("Role was missing")

        try: await discord.utils.get(ctx.guild.text_channels, name=f'team-{final_team.lower()}').delete(reason=f'Deleting team {final_team}')
        except: errors.append("Text channel was missing")

        try: await discord.utils.get(ctx.guild.voice_channels, name=f'Team {final_team}').delete(reason=f'Deleting team {final_team}')
        except: errors.append("Voice Channel was missing")

        await ctx.send(f"Team {final_team} was successfully deleted. Errors encountered:\n\n{", ".join(errors)}")
        

def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))