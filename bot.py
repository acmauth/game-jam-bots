import discord, os, dotenv, asyncio, tracemalloc
from utils.utilities import *
from utils.database_handler import SQLiteHandler
from discord.ext import commands

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Create database file if not exists
if not os.path.isdir("data/"):
    os.mkdir("data/")
if not database_path.removeprefix("data/") in os.listdir("data/"):
    open(database_path, "x").close()

# Enabling default...
intents = discord.Intents().default()
# ...guild member-related...
intents.members = True
# ...and message-related intents
intents.message_content = True
# Our main Bot object (derived from discord.ext.commands and not from discord)
bot = commands.Bot(intents=intents, command_prefix=commands.when_mentioned_or("!"), help_command=None)

log_channel_id = 1369794169022971985

# Load cogs...
for filename in os.listdir("./modules"):
    if filename.endswith(".py"):
        bot.load_extension(f"modules.{filename[:-3]}")

# (For dbg reasons) The event is triggered when the bot connects to the Discord gateaway with no errors
@bot.event
async def on_ready() -> None:
    #await bot.get_channel(log_channel_id).send('I\'m online')
    await SQLiteHandler.check_tables()

@bot.event
async def on_command_error(ctx: commands.Context, err: discord.DiscordException) -> None:
    await bot.get_channel(log_channel_id).send(
        f'@here The command `{ctx.command.name}` raised an exception :\n\n**{err}**'
    )

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, err: discord.DiscordException) -> None:
    await bot.get_channel(log_channel_id).send(
        f'@here The command </{ctx.command.name}:{ctx.command.id}> raised an exception :\n\n**{err}**'
    )

@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    exc: Exception = args[1] if len(args) > 1 else args[0]
    await bot.get_channel(log_channel_id).send(
        f'@here An exception was raised by the event `{event}`:\n\n{exc}'
    )   

if __name__ == "__main__":
    dotenv.load_dotenv() # load .env
    token = os.getenv("DISCORD_BOT_TOKEN") # get the token
    tracemalloc.start()
    bot.run(token) # run the bot