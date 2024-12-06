import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime
import os
import logging
import sys

# Set up logging
logger = logging.getLogger('AoCBot')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Create bot instance with command prefix '!'
import discord
from discord.ext import tasks
import aiohttp
import json
import os

from leaderboard import AoCLeaderboard

try:
    from config import *
except ImportError:
    # Load from environment variables if config.py doesn't exist
    TOKEN = os.getenv('DISCORD_TOKEN')
    AOC_SESSION_TOKEN = os.getenv('AOC_SESSION_TOKEN')
    AOC_LEADERBOARD_ID = os.getenv('AOC_LEADERBOARD_ID')
    AOC_YEAR = int(os.getenv('AOC_YEAR', '2024'))
    TESTING_MODE = os.getenv('TESTING_MODE', 'False').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', '900'))


class AoCBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.messages = True

        super().__init__(intents=intents)

        # Add command tree for slash commands
        self.tree = app_commands.CommandTree(self)

        # Configuration
        self.ANNOUNCEMENT_CHANNEL_ID = (
            1313520321747222610  # Channel to post announcements
        )
        self.AOC_SESSION_TOKEN = (
            AOC_SESSION_TOKEN  # Store token in environment variable
        )
        self.LAST_CHECK_FILE = "last_check.txt"

        # Read last check time from file or default to 15 minutes ago
        self.last_check_time = self.read_last_check_time()

        # Manual mapping of AoC users to Discord names
        self.user_mapping = {
        }

        self.TESTING_MODE = TESTING_MODE
        if self.TESTING_MODE:
            logger.info("🧪 Running in TESTING MODE - no messages will be sent to Discord")

        # Create leaderboard instance
        self.leaderboard = AoCLeaderboard(
            session_token=AOC_SESSION_TOKEN,
            leaderboard_id=AOC_LEADERBOARD_ID,
            year=AOC_YEAR
        )

    async def setup_hook(self):
        logger.info("Bot is starting up...")
        await self.check_for_new_stars()
        self.check_for_new_stars.start()
        logger.info("Initial check complete and periodic checks started")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("\nServers the bot is in:")
        
        # Register commands for each guild
        for guild in self.guilds:
            logger.info(f"- {guild.name} (ID: {guild.id})")
            logger.info("  Channels:")
            for channel in guild.channels:
                logger.info(f"  - {channel.name} (ID: {channel.id})")
            
            # Register commands for this guild
            guild_obj = discord.Object(id=guild.id)
            self.tree.clear_commands(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            logger.info(f"🔄 Cleared and syncing commands for guild {guild.id}")
            
            # Add commands specifically for this guild
            command = app_commands.Command(
                name="leaderboard",
                description="Show the current AoC leaderboard",
                callback=self.show_leaderboard
            )
            self.tree.add_command(command, guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            logger.info(f"✅ Added leaderboard command to guild {guild.id}")

            command = app_commands.Command(
                name="starsplz",
                description="Force check for new stars right now",
                callback=self.force_star_check
            )
            self.tree.add_command(command, guild=guild_obj)
            print(f"✅ Added starsplz command to guild {guild.id}")

        await self.change_presence(activity=discord.Game(name="Advent of Code 2024"))

    async def on_message(self, message):
        if message.author == self.user:  # Ignore messages from the bot itself
            return

        if message.content.lower() == "!aocstatus":
            await message.channel.send(
                f"🤖 Bot is online! Last check was at <t:{int(self.last_check_time)}:R>"
            )

        elif message.content.lower() == "!servers":
            server_list = "\n".join([f"• {guild.name}" for guild in self.guilds])
            await message.channel.send(f"I'm in these servers:\n{server_list}")

    @tasks.loop(minutes=15)  # Run every 15 minutes
    async def check_for_new_stars(self):
        logger.info(f"\nChecking for new stars at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        data = await self.leaderboard.fetch_data(force_fresh=True)
        if not data:
            logger.error("❌ Failed to fetch leaderboard data")
            return

        channel = self.get_channel(self.ANNOUNCEMENT_CHANNEL_ID)
        if not channel:
            logger.error("❌ Could not find announcement channel")
            return

        new_achievements = self.leaderboard.check_for_new_stars(data, self.last_check_time)
        
        if new_achievements:
            logger.info(f"Found {len(new_achievements)} new achievements!")
            messages = [achievement["message"] for achievement in new_achievements]
            
            # Split messages into chunks
            message_chunks = []
            current_chunk = []
            current_length = 0

            for message in messages:
                # If adding this message would exceed limit, start new chunk
                if current_length + len(message) + 1 > 1900:  # Leave some margin
                    message_chunks.append("\n".join(current_chunk))
                    current_chunk = [message]
                    current_length = len(message)
                else:
                    current_chunk.append(message)
                    current_length += len(message) + 1  # +1 for newline

            # Add the last chunk if it exists
            if current_chunk:
                message_chunks.append("\n".join(current_chunk))

            # Send each chunk
            for chunk in message_chunks:
                await self.send_message(channel, chunk)
                print(
                    f"{'🧪 Simulated' if self.TESTING_MODE else '✅'} message chunk of length {len(chunk)}"
                )
        else:
            logger.info("No new achievements found")

        # Update last check time and save it
        self.last_check_time = int(datetime.now().timestamp())
        self.save_last_check_time(self.last_check_time)

    @check_for_new_stars.before_loop
    async def before_check(self):
        """Wait until bot is ready before starting the task"""
        await self.wait_until_ready()

    def read_last_check_time(self):
        """Read last check time from file or return default"""
        try:
            with open(self.LAST_CHECK_FILE, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            # If file doesn't exist or has invalid content, return 15 minutes ago
            return int(datetime.now().timestamp()) - (15 * 60)

    def save_last_check_time(self, timestamp):
        """Save last check time to file"""
        with open(self.LAST_CHECK_FILE, "w") as f:
            f.write(str(timestamp))

    def get_discord_name(self, aoc_name):
        """Get Discord name from AoC username"""
        return self.user_mapping.get(aoc_name, aoc_name)

    async def send_message(self, channel, content):
        """Wrapper for sending messages that respects testing mode"""
        if self.TESTING_MODE:
            logger.info("\n🧪 Would have sent to Discord:")
            logger.info(f"Channel: {channel.name} ({channel.id})")
            logger.info(f"Message content:\n{content}")
            return None
        else:
            return await channel.send(content)

    async def show_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            data = await self.leaderboard.fetch_data()
            if not data:
                await interaction.followup.send("❌ Failed to fetch leaderboard data")
                return
            
            message = self.leaderboard.format_leaderboard(data)
            await interaction.followup.send(message)
                
        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}", exc_info=True)
            await interaction.followup.send("❌ An error occurred while fetching the leaderboard")

    async def force_star_check(self, interaction: discord.Interaction):
        """Force an immediate check for new stars"""
        await interaction.response.defer()
        
        try:
            logger.info(f"\n⭐ Forced star check requested by {interaction.user} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run the star check
            await self.check_for_new_stars()
            
            await interaction.followup.send("✅ Force-checked for new stars!")
            
        except Exception as e:
            logger.error(f"Error during forced star check: {e}", exc_info=True)
            await interaction.followup.send("❌ An error occurred while checking for stars")


# Create and run the bot
bot = AoCBot()
bot.run(TOKEN)
