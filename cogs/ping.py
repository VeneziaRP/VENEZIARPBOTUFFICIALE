import discord
from discord.ext import commands
from discord import app_commands

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Test: risponde con Pong.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Pong! ({self.bot.latency*1000:.0f} ms)", ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))