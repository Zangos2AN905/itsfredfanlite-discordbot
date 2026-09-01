"""Entry point - thin launcher that boots the bot from src/."""
from src.bot import ParodyBot
from src.config import DISCORD_TOKEN, GEMINI_API_KEY

if __name__ == "__main__":
    if not DISCORD_TOKEN or not GEMINI_API_KEY:
        print("Error: DISCORD_TOKEN or GEMINI_API_KEY is missing from .env.")
    else:
        bot = ParodyBot()
        bot.run(DISCORD_TOKEN)
