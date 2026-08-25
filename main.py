import io
import os
import re
import sys
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image, ImageSequence
import edge_tts

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

EPISODE_EMOJI = "<:emoji_name:emoji_id>"

OVERLAY_FILENAME = "overlay.png"

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


class ParodyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced successfully.")


bot = ParodyBot()


@bot.event
async def on_ready():
    activity = discord.Game(name="made with Python!")
    

    await bot.change_presence(status=discord.Status.online, activity=activity)


    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

async def generate_tts_audio(text: str, voice: str) -> io.BytesIO:
    communicate = edge_tts.Communicate(text, voice)
    audio_data = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.write(chunk["data"])
    audio_data.seek(0)
    return audio_data

@bot.tree.command(name="restart", description="Restart the bot (Bot owner only).")
async def restart(interaction: discord.Interaction):
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message(
            "Only the bot owner can use this command.", ephemeral=True
        )
        return

    await interaction.response.send_message("Restarting bot...", ephemeral=True)
    await bot.close()
    os.execv(sys.executable, [sys.executable] + sys.argv)

@bot.tree.command(name="shutdown", description="Shutdown the bot (Bot owner only).")
async def shutdown(interaction: discord.Interaction):
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message(
            "Only the bot owner can use this command.", ephemeral=True
        )
        return

    await interaction.response.send_message("Shutting down bot...", ephemeral=True)
    await bot.close()
    sys.exit(0)

@bot.tree.command(name="episode", description="Generate an AI parody episode.")
@app_commands.describe(
    topic="The topic for the episode",
    turns="Number of dialogue turns (3 to 10)",
    model="choose gemini models",
    tts="Generate audio?",
)
@app_commands.choices(
    model=[
        app_commands.Choice(name="Gemini 3.1 Flash Lite (Fast, ratelimited)", value="gemini-3.1-flash-lite"),
        app_commands.Choice(name="Gemini 3.5 Flash Lite (Lightweight)", value="gemini-3.5-flash-lite"),
        app_commands.Choice(name="Gemini 3.7 Flash", value="gemini-3.7-flash"),
        app_commands.Choice(name="Gemini 3.5 Flash", value="gemini-3.5-flash"),
        app_commands.Choice(name="Gemini 3.5", value="gemini-3.5-flash"),
    ]
)
async def episode(
    interaction: discord.Interaction,
    topic: str,
    turns: app_commands.Range[int, 3, 10] = 6,
    model: app_commands.Choice[str] = None,
    tts: bool = False,
):
    if not gemini_client:
        await interaction.response.send_message(
            "Gemini API key is missing.", ephemeral=True
        )
        return

    await interaction.response.defer()
    await interaction.edit_original_response(content="Generating episode script... [10%]")

    chosen_model = model.value if model else "gemini-3.5-flash-lite"

    script_prompt = f"""
    Write a short episode script.
    Topic: {topic}
    
    Characters available: Fred, Kevin, Angry Fred
    Strict limit: Exactly {turns} total dialogue turns. Ensure every character speaks at least once.
    Format strictly as:
    Fred: [dialogue]
    Kevin: [dialogue]
    Angry Fred: [dialogue]
    """

    safety_settings = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
    ]

    try:
        await interaction.edit_original_response(content="Requesting script from Gemini... [30%]")
        response = gemini_client.models.generate_content(
            model=chosen_model,
            contents=script_prompt,
            config=types.GenerateContentConfig(
                safety_settings=safety_settings,
                temperature=0.7,
            ),
        )

        if not response.text:
            await interaction.followup.send(
                "Content blocked or empty response due to safety filters."
            )
            return

        raw_script = response.text.strip()
    except Exception as e:
        await interaction.followup.send(f"Failed to generate script ({chosen_model}): {e}")
        return

    await interaction.edit_original_response(content="Formatting script embeds... [60%]")

    embeds = []
    files = []
    
    # Custom Emoji Header Embed
    header_embed = discord.Embed(
        title=f"{EPISODE_EMOJI} EPISODE: {topic.upper()}",
        description=f"*A {turns}-turn parody scene starring Fred, Kevin, and Evil Fred.*",
        color=discord.Color.dark_embed(),
    )
    embeds.append(header_embed)

    script_lines = [l.strip() for l in raw_script.split("\n") if l.strip()]
    total_lines = len(script_lines)
    line_count = 0

    for idx, line in enumerate(script_lines):
        match = re.match(r"^([^:]+)\s*:\s*(.*)$", line)
        if match:
            speaker_key = match.group(1).strip()
            dialogue = match.group(2).strip()

            char_data = CHARACTERS.get(
                speaker_key,
                {
                    "name": speaker_key,
                    "avatar": None,
                    "color": discord.Color.light_grey(),
                    "voice": "en-GB-ThomasNeural",
                },
            )

            speaker_voice = char_data.get("voice", "en-GB-ThomasNeural")

            line_embed = discord.Embed(
                description=dialogue, color=char_data.get("color", discord.Color.light_grey())
            )
            line_embed.set_author(
                name=char_data.get("name", speaker_key),
                icon_url=char_data.get("avatar"),
            )
            embeds.append(line_embed)

            # Generate TTS audio if enabled
            if tts and len(files) < 15:
                line_count += 1
                progress = 60 + int((idx / max(total_lines, 1)) * 30)
                await interaction.edit_original_response(content=f"Generating audio line {line_count}/{total_lines}... [{progress}%]")
                try:
                    audio_stream = await generate_tts_audio(dialogue, speaker_voice)
                    files.append(
                        discord.File(audio_stream, filename=f"line_{line_count}_{speaker_key}.mp3")
                    )
                except Exception as tts_err:
                    print(f"TTS generation failed for line {line_count}: {tts_err}")

    if len(embeds) > 10:
        embeds = embeds[:10]

    if len(embeds) <= 1:
        await interaction.followup.send("Script generation produced no dialogue.")
        return

    await interaction.edit_original_response(content="Uploading episode... [95%]")

    if files:
        await interaction.followup.send(embeds=embeds, files=files)
    else:
        await interaction.followup.send(embeds=embeds)

    # Clean up status message upon completion
    await interaction.edit_original_response(content="Episode generation complete!")


@bot.tree.command(
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

    if not os.path.exists(OVERLAY_FILENAME):
        await interaction.response.send_message(
            f"Server error: `{OVERLAY_FILENAME}` is missing.",
            ephemeral=True,
        )
        return

    await interaction.response.defer()

    size_mode = size.value if size else "full"

    try:
        user_image_bytes = await image.read()
        user_image_stream = io.BytesIO(user_image_bytes)

        with Image.open(user_image_stream) as base_img, Image.open(OVERLAY_FILENAME) as foreground:
            is_animated = getattr(base_img, "is_animated", False)
            output_buffer = io.BytesIO()

            bg_width, bg_height = base_img.size

            # Determine target canvas size
            if size_mode == "150x150":
                target_w, target_h = 150, 150
            else:
                target_w, target_h = bg_width, bg_height

            foreground_rgba = foreground.convert("RGBA").resize(
                (target_w, target_h), Image.Resampling.LANCZOS
            )

            if is_animated:
                processed_frames = []
                durations = []

                for frame in ImageSequence.Iterator(base_img):
                    frame_rgba = frame.convert("RGBA")
                    
                    # Force resize base frame if target size differs
                    if (bg_width, bg_height) != (target_w, target_h):
                        frame_rgba = frame_rgba.resize(
                            (target_w, target_h), Image.Resampling.LANCZOS
                        )

                    frame_rgba.paste(foreground_rgba, (0, 0), mask=foreground_rgba)
                    processed_frames.append(
                        frame_rgba.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE)
                    )
                    durations.append(frame.info.get("duration", 100))

                loop = base_img.info.get("loop", 0)

                processed_frames[0].save(
                    output_buffer,
                    format="GIF",
                    save_all=True,
                    append_images=processed_frames[1:],
                    duration=durations,
                    loop=loop,
                    optimize=False,
                )
                output_filename = "preview_result.gif"
            else:
                background = base_img.convert("RGBA")
                
                if (bg_width, bg_height) != (target_w, target_h):
                    background = background.resize(
                        (target_w, target_h), Image.Resampling.LANCZOS
                    )

                background.paste(
                    foreground_rgba, (0, 0), mask=foreground_rgba
                )

                background.save(output_buffer, format="PNG")
                output_filename = "preview_result.png"

            output_buffer.seek(0)

        result_file = discord.File(output_buffer, filename=output_filename)
        await interaction.followup.send(file=result_file)

    except Exception as e:
        await interaction.followup.send(f"Failed to process image: {e}")


@bot.tree.command(name="version", description="Check current bot version status.")
async def version(interaction: discord.Interaction):
    image_url = "https://i.pinimg.com/736x/c9/f7/12/c9f712fe42b39c5651b214ca8efdc6a3.jpg"
    embed = discord.Embed(title="Running on LITE", color=discord.Color.blue())
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="version2", description="Information about version 2.")
async def version2(interaction: discord.Interaction):
    image_url = "https://i.pinimg.com/736x/c9/f7/12/c9f712fe42b39c5651b214ca8efdc6a3.jpg"
    embed = discord.Embed(title="Version 2 is coming soon", color=discord.Color.blue())
    embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="helpcommand", description="List available commands.")
async def help_command(interaction: discord.Interaction):
    help_text = (
        "**/episode [topic] [turns] [model] [tts]** - Generate an AI parody script\n"
        "**/previewtext [image]** - adding preview text \n"
        "**/version** - Check bot version\n"
        "**/version2** - About version 2"
    )
    await interaction.response.send_message(help_text, ephemeral=True)


if __name__ == "__main__":
    if not DISCORD_TOKEN or not GEMINI_API_KEY:
        print("Error: DISCORD_TOKEN or GEMINI_API_KEY is missing from .env.")
    else:
        bot.run(DISCORD_TOKEN)
