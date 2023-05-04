import os
from gpt4free import theb
import aiohttp
import discord
from collections import deque
from keep_alive import keep_alive
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Set up the Discord bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN') # Loads Discord bot token from env

# Keep track of the channels where the bot should be active

allow_dm = True
active_channels = set()

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

def generate_response(prompt):
    response = theb.Completion.create(prompt)
    if not response:
        response = "I couldn't generate a response. Please try again."
    return ''.join(token for token in response)
    

def bonk():
    message_history.clear()
    

MAX_HISTORY = 4  # Number of messages to store for each user
message_history = {}

@bot.event
async def on_message(message):
    global allow_dm, message_history

    if ((isinstance(message.channel, discord.DMChannel) and allow_dm) or message.channel.id in active_channels) \
            and not message.author.bot and not message.content.startswith(bot.command_prefix):

        user_id = message.author.id
        if user_id not in message_history:
            message_history[user_id] = deque(maxlen=MAX_HISTORY)

        message_history[user_id].append(f"user: {message.content}")

        prompt = "\n".join(message_history[user_id]) + "\nb:"
        response = generate_response(prompt)

        message_history[user_id].append(f"b: {response}")
        await message.reply(response)

    await bot.process_commands(message)


@bot.command()
async def pfp(ctx, attachment_url=None):
    if attachment_url is None and not ctx.message.attachments:
        return await ctx.send(
            "Please provide an image URL or attach an image with the command"
        )

    if attachment_url is None:
        attachment_url = ctx.message.attachments[0].url

    async with aiohttp.ClientSession() as session:
        async with session.get(attachment_url) as response:
            await bot.user.edit(avatar=await response.read())

    await ctx.send("My profile picture has been updated!")

@bot.command()
async def ping(ctx):
    latency = bot.latency * 1000
    await ctx.send(f"Pong! Latency: {latency:.2f} ms")

@bot.command()
async def changeusr(ctx, new_username):
    # Check that the new username is not already taken
    taken_usernames = [user.name.lower() for user in bot.get_all_members()]
    if new_username.lower() in taken_usernames:
        await ctx.send(f"Sorry, the username '{new_username}' is already taken.")
        return

@bot.command()
async def toggledm(ctx):
    global allow_dm
    allow_dm = not allow_dm
    await ctx.send(f"DMs are now {'allowed' if allow_dm else 'disallowed'} for active channels.")
    
@bot.command()
@commands.has_permissions(administrator=True)
async def toggleactive(ctx):
    channel_id = ctx.channel.id
    if channel_id in active_channels:
        active_channels.remove(channel_id)
        with open("channels.txt", "w") as f:
            for id in active_channels:
                f.write(str(id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been removed from the list of active channels."
        )
    else:
        active_channels.add(channel_id)
        with open("channels.txt", "a") as f:
            f.write(str(channel_id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been added to the list of active channels.")

# Read the active channels from channels.txt on startup
if os.path.exists("channels.txt"):
    with open("channels.txt", "r") as f:
        for line in f:
            channel_id = int(line.strip())
            active_channels.add(channel_id)
      
@bot.command(name='bonk')
async def _bonk(ctx):
    bonk()
    await ctx.send('Ugh my head hurts')
    
@bot.command()
async def welp(ctx):
    embed = discord.Embed(title="Bot Commands", color=0x00ff00)
    embed.add_field(name="!pfp [image_url]", value="Change the bot's profile picture", inline=False)
    embed.add_field(name="!bonk", value="Clears history of the bot", inline=False)
    embed.add_field(name="!changeusr [new_username]", value="Change the bot's username", inline=False)
    embed.add_field(name="!ping", value="Pong", inline=False)
    embed.add_field(name="!toggleactive", value="Toggle the current channel to the list of active channels", inline=False)   
    embed.add_field(name="!toggledm", value="Toggle if DM should be active or not", inline=False)   
    embed.set_footer(text="Created by Mishal#1916")
            

keep_alive()

bot.run(TOKEN)
