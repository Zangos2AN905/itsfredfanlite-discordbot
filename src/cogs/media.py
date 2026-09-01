import discord
from discord import app_commands
from discord.ext import commands

from src.config import OVERLAY_PATH
from src.services.image import apply_overlay


class MediaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="previewtext",
        description="Add preview text overlay to an image or animated GIF.",
    )
    @app_commands.describe(image="The base image or GIF you want to overlay onto")
    @app_commands.choices(
        size=[
            app_commands.Choice(name="Full Overlay", value="full"),
            app_commands.Choice(name="150x150", value="150x150"),
        ]
    )
    async def previewtext(
        self,
        interaction: discord.Interaction,
        image: discord.Attachment,
        size: app_commands.Choice[str] = None,
    ):
        supported_types = ["image/png", "image/jpeg", "image/webp", "image/gif"]
        if image.content_type not in supported_types:
            await interaction.response.send_message(
                "Please upload a valid image (PNG, JPG, WEBP, or GIF).",
                ephemeral=True,
            )
            return

        if not OVERLAY_PATH.exists():
            await interaction.response.send_message(
                f"Server error: `{OVERLAY_PATH.name}` is missing.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        size_mode = size.value if size else "full"

        try:
            user_image_bytes = await image.read()
            output_buffer, output_filename = apply_overlay(user_image_bytes, size_mode)
            result_file = discord.File(output_buffer, filename=output_filename)
            await interaction.followup.send(file=result_file)

        except Exception as e:
            await interaction.followup.send(f"Failed to process image: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(MediaCog(bot))
