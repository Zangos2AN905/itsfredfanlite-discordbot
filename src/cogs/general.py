import discord
from discord import app_commands
from discord.ext import commands


class GeneralCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="version", description="Check current bot version status.")
    async def version(self, interaction: discord.Interaction):
        image_url = "https://i.pinimg.com/736x/c9/f7/12/c9f712fe42b39c5651b214ca8efdc6a3.jpg"
        embed = discord.Embed(title="Running on LITE", color=discord.Color.blue())
        embed.set_image(url=image_url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="version2", description="Information about version 2.")
    async def version2(self, interaction: discord.Interaction):
        image_url = "https://i.pinimg.com/736x/c9/f7/12/c9f712fe42b39c5651b214ca8efdc6a3.jpg"
        embed = discord.Embed(title="Version 2 is coming soon", color=discord.Color.blue())
        embed.set_image(url=image_url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="helpcommand", description="List available commands.")
    async def help_command(self, interaction: discord.Interaction):
        help_text = (
            "**/episode [topic] [turns] [model] [tts]** - Generate an AI parody script (Queued)\n"
            "**/queue** - Check position/length of the episode generation queue\n"
            "**/previewtext [image]** - Add preview text overlay to an image\n"
            "**/version** - Check bot version\n"
            "**/version2** - About version 2"
        )
        await interaction.response.send_message(help_text, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
