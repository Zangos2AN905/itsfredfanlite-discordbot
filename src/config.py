import os
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

# --- Environment ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- General ---
EPISODE_EMOJI = "<:emoji_name:emoji_id>"
OVERLAY_FILENAME = "overlay.png"
# Absolute path to overlay.png (project root) - robust when cwd changes
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OVERLAY_PATH = PROJECT_ROOT / OVERLAY_FILENAME

DISABLED_MODELS: dict[str, str] = {}

CHARACTERS = {
    "Fred": {
        "name": "Fred Figglehorn",
        "avatar": "https://i.pinimg.com/1200x/72/60/08/726008f18672dfc798180d1185d977ae.jpg",
        "color": discord.Color.gold(),
        "voice": "en-GB-ThomasNeural",
    },
    "Kevin": {
        "name": "Kevin",
        "avatar": "https://wertigo.ru/api/shared_files/b7bef8c8-99fe-415f-a1d2-de1f758445eb/files/b7bef8c8-99fe-415f-a1d2-de1f758445eb/preview",
        "color": discord.Color.blue(),
        "voice": "en-US-AndrewNeural",
    },
    "Angry Fred": {
        "name": "Angry Fred",
        "avatar": "https://iili.io/CtW9xWX.jpg",
        "color": discord.Color.red(),
        "voice": "en-US-ChristopherNeural",
    },
}

MODEL_CHOICES = [
    app_commands.Choice(name="Gemini 3.1 Flash Lite (Fast, ratelimited)", value="gemini-3.1-flash-lite"),
    app_commands.Choice(name="Gemini 3.5 Flash Lite (Lightweight)", value="gemini-3.5-flash-lite"),
    app_commands.Choice(name="Gemini 3.7 Flash", value="gemini-3.7-flash"),
    app_commands.Choice(name="Gemini 3.5 Flash", value="gemini-3.5-flash"),
    app_commands.Choice(name="MiniMax M2.7 (free)", value="minimax/minimax-m2.7:free"),
    app_commands.Choice(name="MiniMax M3 (free)", value="minimax/minimax-m3:free"),
]
