import discord
from discord.ext import commands
from discord import ApplicationContext as Context
from utils.database_handler import SQLiteHandler as sql, JSONHandler as json
from utils.utilities import embed_colour

class VotingCog(discord.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def get_titles(ctx: discord.AutocompleteContext):
        games = await sql.gather_submissions()
        titles = []

        for game in games:
            titles.append(game[2])

        return titles

    @commands.slash_command(description="Η εντολή επιστρέφει όλες τις έγκυρες εγγραφές παιχνιδιών, τα οποία μπορείς να αξιολογήσεις!")
    async def submissions(self, ctx: Context):
        subs = await sql.gather_submissions()

        if len(subs) != 0:
            embed = discord.Embed(
                colour = embed_colour,
                title = "Έγκυρες εγγραφές παιχνιδιών",
                description = "Όλα τα παιχνίδια τα οποία μπορείς να δοκιμάσεις και να αξιολογήσεις! Για να αξιολογήσεις ένα παιχνίδι, χρησιμοποιείς το **όνομά** του!"
            )

            for game in subs:
                embed.add_field(
                    name = f"{game[2]} | ID: {str(game[1])}", # title
                    value = f"Ομάδα: {game[0]} | [Σύνδεσμος του παιχνιδιού]({game[3]})",
                    inline = False
                )

            await ctx.interaction.respond(embed=embed)
        else:
            await ctx.interaction.respond("Δεν υπάρχουν έγκυρες εγγραφές παιχνιδιών διαθέσιμες προς αξιολόγηση. Λογικά δεν είναι η ώρα της αξιολόγησης...", ephemeral=True)

    @commands.slash_command()
    @discord.option(name='game_title',
                    description='Ο τίτλος του παιχνιδιού το οποίο θέλεις να αξιολογήσεις',
                    input_type=str,
                    required=True,
                    autocomplete=discord.utils.basic_autocomplete(get_titles))
    @discord.option(name='rating',
                    description='Η βαθμολογία του παιχνδιού. Πρέπει να είναι πραγματικός αριθμός μεταξύ του 0 και 10.',
                    input_type=float,
                    required=True,
                    min_value=0.0,
                    max_value=10.0)
    async def rate(self, ctx: Context, game_title: str, rating: float):
        if await sql.submission_exists(game_title):
            judge_role = discord.utils.get(ctx.guild.roles, name="Judge")
            volunteer = discord.utils.get(ctx.guild.roles, name="Volunteer")
            rtype = "community"
            special_roles = [
                discord.utils.get(ctx.guild.roles, name="Moderator"),
                judge_role,
                discord.utils.get(ctx.guild.roles, name="Mentor")
            ]

            if len([e for e in special_roles if e in ctx.author.roles]) > 0: 
                team = ctx.author.name
                if judge_role in ctx.author.roles: rtype = "judge"
            elif volunteer in ctx.author.roles: ctx.author.roles[1].name if len(ctx.author.roles) > 2 else ctx.author.name
            else: team = ctx.author.roles[1].name if len(ctx.author.roles) > 1 else ctx.author.name

            if await sql.crosscheck_game_team(game_title, team):
                await json.submit_rating(ctx.author.name, game_title, rating, rtype)
                await ctx.interaction.respond(f"Επιτυχής αξιολόγηση του παιχνιδιού `{game_title}`. Ο βαθμός σου είναι `{str(rating)}`!", ephemeral=True)
            else: 
                await ctx.interaction.respond("Δεν μπορείς να ψηφίσεις το δικό σου παιχνίδι!", ephemeral=True)
        else: await ctx.interaction.respond(f"Το παιχνίδι `{game_title}` δεν υπάρχει στις έγκυρες εγγραφές προς αξιολόγηση.", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(VotingCog(bot))