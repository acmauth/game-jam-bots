import discord
from discord import ApplicationContext as Context
from discord.ext import commands

from utils.database_handler import SQLiteHandler as sql
from utils.utilities import embed_colour

class TeamsCog(discord.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.slash_command(description='Η εντολή στέλνει αίτημα ένταξης σε ομάδα της επιλογής σου!')
    @discord.option(name='team_name',
                    description='Το όνομα της ομάδας',
                    input_type=str)
    async def join(self, ctx: Context, team_name: str) -> None:
        await ctx.defer()

        info = await sql.team_exists(team_name)
        exists = info[0]
        team = info[1]
        user_id = ctx.author.id

        if not await sql.is_user_on_any_team(user_id):
            if exists:
                result = await sql.create_team_request(team, user_id)
                if result == -1: await ctx.interaction.respond('Η ομάδα που ανέφερες έχει συμπληρώσει τον μέγιστο αριθμό επιτρεπτών μελών!',
                                                   ephemeral=True)
                elif result == 0: await ctx.interaction.respond(f'Έχεις ήδη αιτηθεί την ένταξή σου στην ομάδα {team}',
                                                    ephemeral=True)
                else:
                    await ctx.interaction.respond(f'Η αίτηση ένταξης προς την ομάδα {team} στάλθηκε!',
                                        ephemeral=True)
                    final_team_string = f'team-{team_name}'.lower().replace(' ', '-')
                    await discord.utils.get(ctx.guild.text_channels, name=final_team_string).send(f'Ο χρήστης {ctx.author.mention} μόλις έστειλε αίτημα ένταξης προς την ομάδα σας!')
            else:
                try:
                    await sql.create_team(team_name, user_id) # create the team
                    await sql.dismiss_all_user_requests(user_id) # delete all sent requests

                    # create and assign the role
                    role = await ctx.guild.create_role(reason=f'Role creation for team {team_name}',
                                                name=team_name,
                                                colour=discord.Colour.random(),
                                                permissions=discord.utils.get(ctx.guild.roles, name="@everyone").permissions,
                                                mentionable=False)
                    await ctx.author.add_roles(role,
                                               reason=f'Adding appropriate role to user of team {team_name}')

                    # create the channel
                    txt_channel = await ctx.guild.create_text_channel(reason=f'Channel creation for team {team_name}',
                                                                      name=f'team-{team_name}',
                                                                      category=discord.utils.get(ctx.guild.categories, name='Teams\' Chats'),
                                                                      overwrites={
                                                                          discord.utils.get(ctx.guild.roles, name=team_name) : discord.PermissionOverwrite(
                                                                              view_channel = True, use_slash_commands=True
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles, name='Moderator') : discord.PermissionOverwrite(
                                                                              view_channel = True
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles, name="Mentor") : discord.PermissionOverwrite(
                                                                              view_channel = True
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles, name='@everyone') : discord.PermissionOverwrite(
                                                                              view_channel = False
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles, name='ThessGameJamBot') : discord.PermissionOverwrite(
                                                                              view_channel = True, manage_channels = True
                                                                          )
                                                                      })

                    vc_channel = await ctx.guild.create_voice_channel(reason=f'Channel creation for team {team_name}',
                                                                      name=f'Team {team_name}',
                                                                      category=discord.utils.get(ctx.guild.categories, name='Teams\' Voice Chats'),
                                                                      user_limit=4,
                                                                      overwrites={
                                                                          discord.utils.get(ctx.guild.roles,
                                                                                            name=team_name): discord.PermissionOverwrite(
                                                                              view_channel=True
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles,
                                                                                            name='Moderator'): discord.PermissionOverwrite(
                                                                              view_channel=True
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles, name="Mentor") : discord.PermissionOverwrite(
                                                                              view_channel = True
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles,
                                                                                            name='@everyone'): discord.PermissionOverwrite(
                                                                              view_channel=False
                                                                          ),
                                                                          discord.utils.get(ctx.guild.roles,
                                                                                            name='ThessGameJamBot'): discord.PermissionOverwrite(
                                                                              view_channel=True, manage_channels=True
                                                                          )
                                                                      })

                    # send the final response
                    await ctx.interaction.respond(f'Η ομάδα `{team_name}` δημιουργήθηκε επιτυχώς! Επιπλέον, πήρες τον ειδικό ρόλο {role.mention}, όπως και '
                                      f'δημιουργήθηκαν τα κανάλια {txt_channel.mention} και {vc_channel.mention} αποκλειστικά για τα μέλη της ομάδας σου!', ephemeral=True)
                except:
                    await ctx.interaction.respond(f'**__Σφάλμα__**: Ανεπιτυχής δημιουργία της ομάδας `{team_name}`. Παρακαλώ επικοινώνησε με κάποιο μέλος προσωπικού.', ephemeral=True)
        else:
            leave_cmd = discord.utils.get(self.bot.application_commands, name='leave')
            await ctx.interaction.respond(f'Ανήκεις ήδη σε ομάδα! Αν επιθυμείς να ενταχθείς σε κάποια άλλη, χρησιμοποίησε την εντολή </leave:{leave_cmd.id}> '
                              'για να αποχωρήσεις από την ομάδα σου και έπειτα προσπάθησε ξανά!', ephemeral=True)

    @commands.slash_command(description='Η εντολή επιστρέφει τα αιτήματα ένταξης χρηστών προς την ομάδα σου!')
    async def requests(self, ctx: Context) -> None:
        user_id = ctx.author.id

        if await sql.is_user_on_any_team(user_id):
            team: str = await sql.get_team_by_member(user_id)
            requests_list = await sql.get_team_total_requests(team)
            if len(requests_list) == 0: await ctx.interaction.respond('Δεν υπάρχουν διαθέσιμα αιτήματα προς έλεγχο.')
            else:
                correct_description = f'Υπάρχουν {len(requests_list)} αιτήματα' if len(requests_list) > 1 else 'Υπάρχει 1 αίτημα'
                embed = discord.Embed(
                    colour=embed_colour,
                    title=f'Αιτήματα ομάδας {team}',
                    description=f'{correct_description} προς έλεγχο.',
                )
                user_list = list()

                for user_id in requests_list:
                    user = discord.utils.get(ctx.guild.members, id=user_id)
                    if user is None: continue
                    user_list.append(user.mention)

                final_applicants_string = ', '.join(user_list)

                embed.add_field(
                    name='Αιτούμενοι χρήστες',
                    value=final_applicants_string,
                    inline=False
                )

                await ctx.interaction.respond(embed=embed, ephemeral=True)
        else:
            await ctx.interaction.respond('Δεν ανήκεις σε κάποια ομάδα!', ephemeral=True)

    @commands.slash_command(description='Η εντολή αποδέχεται το αίτημα ένταξης του χρήστη της παραμέτρου προς την ομάδα σου!')
    @discord.option(name='user',
                    description='Ο αιτούμενος χρήστης',
                    input_type=discord.Member)
    async def accept(self, ctx: Context, user: discord.Member) -> None:
        applicant_id = user.id
        author_id = ctx.author.id

        if await sql.is_user_on_any_team(author_id):
            team = await sql.get_team_by_member(author_id)
            member_list = await sql.get_team_total_members(team)
            if author_id == member_list[0]: #if the user is the leader
                if await sql.request_exists(team, applicant_id):
                    if not await sql.is_user_on_any_team(applicant_id):
                        if not len(member_list) >= 4:
                            await sql.add_user_to_team(team, applicant_id)
                            await user.add_roles(discord.utils.get(ctx.guild.roles, name=team), reason=f'Assigning role to member of team {team}')

                            await sql.dismiss_all_user_requests(applicant_id)

                            await ctx.interaction.respond(f'Αποδέχτηκες το αίτημα του αιτούμενου χρήστη. Καλωσόρισες {user.mention}!')
                        else: await ctx.interaction.respond('Η ομάδα σου είναι γεμάτη. (4/4 μέλη συνολικά)')
                    else:
                        await sql.dismiss_team_request(team, applicant_id)
                        await ctx.interaction.respond(f'Ο χρήστης {user.mention} ανήκει ήδη σε ομάδα. Το αίτημα του διαγράφτηκε αυτόματα.')
                else: await ctx.interaction.respond('Δεν υπάρχει αίτημα ένταξης προς την ομάδα σου από αυτόν τον χρήστη.')
            else: await ctx.interaction.respond('Μόνο ο αρχηγός της ομάδας σου μπορεί να αποδεχτεί αιτήματα.')
        else: await ctx.interaction.respond('Δεν ανήκεις σε κάποια ομάδα!')

    @commands.slash_command(description='Η εντολή απορρίπτει το αίτημα ένταξης του χρήστη της παραμέτρου προς την ομάδα σου!')
    @discord.option(name='user',
                    description='Ο αιτούμενος χρήστης',
                    input_type=discord.Member)
    async def dismiss(self, ctx: Context, user: discord.Member) -> None:
        applicant_id = user.id
        author_id = ctx.author.id

        if await sql.is_user_on_any_team(author_id):
            team = await sql.get_team_by_member(author_id)
            members = await sql.get_team_total_members(team)
            if author_id == members[0]:
                if await sql.request_exists(team, applicant_id):
                    await sql.dismiss_team_request(team, applicant_id)
                    await ctx.interaction.respond(f'Το αίτημα του χρήστη {user.mention} απορρίφθηκε επιτυχώς.')
                else: await ctx.interaction.respond('Δεν υπάρχει αίτημα ένταξης προς την ομάδα σου από αυτόν τον χρήστη.')
            else: await ctx.interaction.respond('Μόνο ο αρχηγός της ομάδας σου μπορεί να απορρίψει αιτήματα.')
        else: await ctx.interaction.respond('Δεν ανήκεις σε κάποια ομάδα!')

    @commands.slash_command(description='Η εντολή διώχνει τον χρήστη της παραμέτρου από την ομάδα σου!')
    @discord.option(name='user',
                    description='Ο χρήστος-μέλος της ομάδας',
                    input_type=discord.Member)
    async def kick(self, ctx: Context, user: discord.Member) -> None:
        member_id = user.id
        author_id = ctx.author.id
        leave_cmd = discord.utils.get(self.bot.application_commands, name='leave')

        if await sql.is_user_on_any_team(author_id):
            team = await sql.get_team_by_member(author_id)
            members = await sql.get_team_total_members(team)
            if author_id == members[0]:
                if member_id != author_id:
                    if member_id in members:
                        await sql.remove_member_from_team(team, member_id)
                        await user.remove_roles(discord.utils.get(ctx.guild.roles, name=team), reason=f'Kicking user from team {team}')
                        await ctx.interaction.respond(f'Ο χρήστης {user.mention} εκδιώχθηκε επιτυχώς από την ομάδα!')
                    else: await ctx.interaction.respond('Αυτός ο χρήστης δεν είναι μέλος της ομάδας σου!')
                else: await ctx.interaction.respond('Δεν μπορείς να διώξεις τον εαυτό σου! Αν επιθυμείς να φύγεις από την ομάδα,'
                                                    f' χρησιμοποίησε την εντολή </leave:{leave_cmd.id}>.')
            else: await ctx.interaction.respond('Μόνο ο αρχηγός της ομάδας σου μπορεί να διώξει άτομα.')
        else: await ctx.interaction.respond('Δεν ανήκεις σε κάποια ομάδα!')

    @commands.slash_command(description='Η εντολή σε αφαιρεί από την ομάδα σου!')
    async def leave(self, ctx: Context) -> None:
        user_id = ctx.author.id
        team = await sql.get_team_by_member(user_id)

        if await sql.is_user_on_any_team(user_id):
            members = await sql.get_team_total_members(team)
            if len(members) > 1:
                if members[0] == user_id: #the user is the team's leader
                    await sql.transfer_team_leadership(team) #...to the next user BY ORDER in the members list
                if await sql.remove_member_from_team(team, user_id):
                    await ctx.author.remove_roles(
                        discord.utils.get(ctx.guild.roles, name=team),
                        reason=f'Removing member from team {team}'
                    )
                    await ctx.interaction.respond(f'Επιτυχής αποχώρηση από την ομάδα `{team}`.', ephemeral=True)
                else: await ctx.interaction.respond('Βρέθηκε σφάλμα, παρακαλώ επικοινώνησε άμεσα με ένα μέλος προσωπικού.', ephemeral=True) #just in case
            else: # delete the team
                final_team = team.replace(' ', '-').lower()
                await discord.utils.get(ctx.guild.text_channels, name=f'team-{final_team}').delete(reason=f'Deleting team {team}')
                await discord.utils.get(ctx.guild.voice_channels, name=f'Team {team}').delete(reason=f'Deleting team {team}')
                await discord.utils.get(ctx.guild.roles, name=team).delete(reason=f'Deleting team {team}')

                await sql.delete_team(team)
                await sql.dismiss_all_team_requests(team)

                try:
                    await ctx.interaction.respond(f'Επιτυχής αποχώρηση από την ομάδα `{team}`. Επειδή ήσουν το μόνο μέλος της, η ομάδα διαγράφτηκε.', ephemeral=True)
                except discord.NotFound:
                    pass #the channel was already deleted
        else: await ctx.interaction.respond('Δεν ανήκεις σε κάποια ομάδα!', ephemeral=True)

    @commands.slash_command(description='Η εντολή εκτυπώνει τα μέλη μιας ομάδας!')
    @discord.option(name='team_name',
                    description='',
                    input_type=str,
                    required=False,
                    default='')
    async def members(self, ctx: Context, team_name: str = '') -> None:
        team: str = await sql.get_team_by_member(ctx.author.id) if len(team_name) == 0 else team_name
        info = await sql.team_exists(team)
        team = info[1]
        exists = info[0]
        if await sql.is_user_on_any_team(ctx.author.id):
            if exists:
                member_list = await sql.get_team_total_members(team)
                correct_member_form = 'μέλη, τα οποία παρουσιάζονται' if len(member_list) > 1 else 'μέλος, το οποίο παρουσιάζεται'
                embed = discord.Embed(colour=embed_colour,
                                      title=f'Team {team}',
                                      description=f'Η ομάδα **{team}** αποτελείται από **{len(member_list)}** {correct_member_form} παρακάτω:')

                leader_string = ''
                member_mentions_list = list()

                for member in member_list:
                    user = discord.utils.get(ctx.guild.members, id=member)
                    if user is None: continue
                    if member == member_list[0]: leader_string = user.mention
                    else: member_mentions_list.append(user.mention)

                embed.add_field(
                    name='`Αρχηγός`',
                    value=f'{leader_string}',
                    inline=False
                )

                if len(member_mentions_list) > 0:
                    final_string = ', '.join(member_mentions_list)
                    embed.add_field(
                        name='`Μέλη`',
                        value=f'{final_string}',
                        inline=False
                    )

                await ctx.interaction.respond(embed=embed, ephemeral=True)
            else:
                await ctx.interaction.respond('Η ομάδα που ανέφερες δεν υπάρχει!', ephemeral=True)
        else: await ctx.interaction.respond('Δεν ανήκεις σε κάποια ομάδα!', ephemeral=True)

    @commands.slash_command(description='Η εντολή εκτυπώνει όλες τις υπάρχουσες ομάδες!')
    async def teams(self, ctx: Context) -> None:
        teams = await sql.get_all_teams()
        correct_description = f'Υπάρχουν **{len(teams.keys())}** ομάδες' if len(teams.keys()) != 1 else 'Υπάρχει **1** ομάδα'
        embed = discord.Embed(
            colour=embed_colour,
            title='Υπάρχουσες ομάδες',
            description=f'{correct_description} συνολικά.'
        )

        for team, members in teams.items():
            leader = discord.utils.get(ctx.guild.members, id=members[0])

            embed.add_field(
                name=f'Team `{team}`',
                value=f'> **Αρχηγός**: {leader.mention}\n> **Πλήθος μελών**: {len(members)}',
                inline=False
            )

        await ctx.interaction.respond(embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(TeamsCog(bot))