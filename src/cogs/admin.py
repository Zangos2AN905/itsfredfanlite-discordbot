import os
import sys

import discord
from discord import app_commands
from discord.ext import commands

from src.config import DISABLED_MODELS, MODEL_CHOICES


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="restart", description="Restart the bot (Bot owner only).")
    async def restart(self, interaction: discord.Interaction):
        app_info = await self.bot.application_info()
        if interaction.user.id != app_info.owner.id:
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        await interaction.response.send_message("Restarting bot...", ephemeral=True)
        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @app_commands.command(name="shutdown", description="Shutdown the bot (Bot owner only).")
    async def shutdown(self, interaction: discord.Interaction):
        app_info = await self.bot.application_info()
        if interaction.user.id != app_info.owner.id:
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        await interaction.response.send_message("Shutting down bot...", ephemeral=True)
        await self.bot.close()
        sys.exit(0)

    @app_commands.command(name="disable_model", description="Disable a model from being used in /episode (Owner only).")
    @app_commands.describe(
        model="Select the model to disable",
        reason="The reason for disabling this model",
    )
    @app_commands.choices(model=MODEL_CHOICES)
    async def disable_model(
        self,
        interaction: discord.Interaction,
        model: app_commands.Choice[str],
        reason: str = "Maintenance / Temporarily disabled.",
    ):
        app_info = await self.bot.application_info()
        if interaction.user.id != app_info.owner.id:
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        DISABLED_MODELS[model.value] = reason
        await interaction.response.send_message(
            f"Disabled model `{model.name}` (`{model.value}`).\n**Reason:** {reason}",
            ephemeral=True,
        )

    @app_commands.command(name="enable_model", description="Re-enable a disabled model (Owner only).")
    @app_commands.describe(model="Select the model to enable")
    @app_commands.choices(model=MODEL_CHOICES)
    async def enable_model(
        self,
        interaction: discord.Interaction,
        model: app_commands.Choice[str],
    ):
        app_info = await self.bot.application_info()
        if interaction.user.id != app_info.owner.id:
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        if model.value in DISABLED_MODELS:
            del DISABLED_MODELS[model.value]
            await interaction.response.send_message(
                f"Re-enabled model `{model.name}` (`{model.value}`).",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"Model `{model.name}` is not currently disabled.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
