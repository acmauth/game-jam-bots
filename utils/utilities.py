import asyncio, sys

# Colour assigned to embeds sent by the bot
embed_colour = 0xd03df5

# Database file relative path
database_path = "data/database.db"

# Votes file relative path
votes_path = "data/votes.json"

# Active Game Jam ID as given by itch.io
active_gamejam_id = 416205
active_gamejam_name = "thess-game-jam"

# Async console printing
async def aprint(output) -> None:
    await asyncio.to_thread(sys.stdout.write, f'{output}\n')

# Async parallel execution of Future objects
async def parallel_execute(coro_future_gens: list) -> None:
    await asyncio.gather(*coro_future_gens)