## Used for the episode command.

import re

import discord

from src.config import CHARACTERS, EPISODE_EMOJI
from src.services.llm import request_openrouter_script
from src.services.tts import generate_tts_audio


async def run_episode_job(
    interaction: discord.Interaction,
    topic: str,
    turns: int,
    chosen_model: str,
    tts: bool,
):
    await interaction.edit_original_response(content="Generating episode script... [10%]")

    script_prompt = f"""
    Write a short parody episode script.
    Topic: {topic}
    
    Characters available: Fred, Kevin, Angry Fred
    Strict limit: Exactly {turns} total dialogue turns. Ensure every character speaks at least once.
    Format strictly as (DO NOT put brackets around character names):
    Fred: [dialogue]
    Kevin: [dialogue]
    Angry Fred: [dialogue]
    """

    try:
        await interaction.edit_original_response(
            content=f"Requesting script via {chosen_model}... [30%]"
        )
        raw_script = await request_openrouter_script(script_prompt, chosen_model)

        if not raw_script:
            await interaction.followup.send("Content blocked or empty response.")
            return

    except Exception as e:
        await interaction.followup.send(f"Failed to generate script ({chosen_model}): {e}")
        return

    await interaction.edit_original_response(content="Formatting script embeds... [60%]")

    embeds = []
    files = []

    header_embed = discord.Embed(
        title=f"{EPISODE_EMOJI} EPISODE: {topic.upper()}",
        description=f"*A {turns}-turn parody scene starring Fred, Kevin, and Angry Fred.*",
        color=discord.Color.dark_embed(),
    )
    embeds.append(header_embed)

    script_lines = [l.strip() for l in raw_script.split("\n") if l.strip()]
    total_lines = len(script_lines)
    line_count = 0

    for idx, line in enumerate(script_lines):
        match = re.match(r"^([^:]+)\s*:\s*(.*)$", line)
        if match:
            # Strip brackets [ ] and extra whitespace from speaker name
            speaker_key = re.sub(r"[\[\]]", "", match.group(1)).strip()
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

            if tts and len(files) < 15:
                line_count += 1
                progress = 60 + int((idx / max(total_lines, 1)) * 30)
                await interaction.edit_original_response(
                    content=f"Generating audio line {line_count}/{total_lines}... [{progress}%]"
                )
                try:
                    audio_stream = await generate_tts_audio(dialogue, speaker_voice)
                    files.append(
                        discord.File(
                            audio_stream, filename=f"line_{line_count}_{speaker_key}.mp3"
                        )
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

    await interaction.edit_original_response(content="Episode generation complete!")
