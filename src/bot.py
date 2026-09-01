import asyncio

import discord
from discord.ext import commands


class ParodyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.episode_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None

    async def setup_hook(self):
        # Load all cogs (commands are grouped by feature inside src/cogs/)
        for ext in ("src.cogs.admin", "src.cogs.episode", "src.cogs.media", "src.cogs.general"):
            try:
                await self.load_extension(ext)
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")
        await self.tree.sync()
        print("Slash commands synced successfully.")
        # Start the sequential background queue for episode generation
        self.worker_task = asyncio.create_task(self.episode_queue_worker())

    async def episode_queue_worker(self):
        """Processes episode creation requests sequentially in the background."""
        while True:
            task_func, interaction = await self.episode_queue.get()
            try:
                await task_func(interaction)
            except Exception as e:
                print(f"Error processing episode task: {e}")
                try:
                    await interaction.followup.send(
                        f"An error occurred during episode processing: {e}"
                    )
                except Exception:
                    pass
            finally:
                self.episode_queue.task_done()

    async def on_ready(self):
        activity = discord.Game(name="made with Python!")
        await self.change_presence(status=discord.Status.online, activity=activity)
        print(f"Logged in as {self.user} (ID: {self.user.id})")
