import discord
from discord import app_commands
from discord.ext import commands

from src.config import DISABLED_MODELS, GEMINI_API_KEY, MODEL_CHOICES, OPENROUTER_API_KEY
from src.services.llm import gemini_client
from src.services.episode import run_episode_job


class EpisodeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="episode", description="Generate an AI parody episode.")
    @app_commands.describe(
        topic="The topic for the episode",
        turns="Number of dialogue turns (3 to 10)",
        model="Choose AI Model provider and version",
        tts="Generate Edge-TTS audio?",
    )
    @app_commands.choices(model=MODEL_CHOICES)
    async def episode(
        self,
        interaction: discord.Interaction,
        topic: str,
        turns: app_commands.Range[int, 3, 10] = 6,
        model: app_commands.Choice[str] = None,
        tts: bool = False,
    ):
        chosen_model = model.value if model else "gemini-3.5-flash-lite"

        # Check if the requested model has been disabled by owner
        if chosen_model in DISABLED_MODELS:
            reason = DISABLED_MODELS[chosen_model]
            await interaction.response.send_message(
                f"The selected model (`{chosen_model}`) is currently disabled.\n**Reason:** {reason}",
                ephemeral=True,
            )
            return

        if chosen_model.startswith("gemini-") and not gemini_client:
            await interaction.response.send_message(
                "Gemini API key is missing.", ephemeral=True
            )
            return

        if (
            chosen_model.startswith("meta-llama")
            or chosen_model.startswith("openrouter")
            or chosen_model.startswith("minimax")
        ) and not OPENROUTER_API_KEY:
            await interaction.response.send_message(
                "OpenRouter API key is missing in environment variables.", ephemeral=True
            )
            return

        await interaction.response.defer()

        queue_position = self.bot.episode_queue.qsize() + 1
        if queue_position > 1:
            await interaction.edit_original_response(
                content=f"Queued! Position in line: {queue_position - 1}"
            )
        else:
            await interaction.edit_original_response(content="Starting episode generation...")

        async def job(inter):
            await run_episode_job(inter, topic, turns, chosen_model, tts)

        await self.bot.episode_queue.put((job, interaction))

    @app_commands.command(name="queue", description="Check the current status of the episode queue.")
    async def show_queue(self, interaction: discord.Interaction):
        qsize = self.bot.episode_queue.qsize()
        if qsize == 0:
            await interaction.response.send_message("The episode queue is currently empty!")
        else:
            await interaction.response.send_message(
                f"There are currently **{qsize}** episode(s) waiting in queue."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(EpisodeCog(bot))
