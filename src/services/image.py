## Image overlay system

import io

from PIL import Image, ImageSequence

from src.config import OVERLAY_PATH


def apply_overlay(
    base_image_bytes: bytes,
    size_mode: str = "full",
) -> tuple[io.BytesIO, str]:
    """
    Apply the overlay.png onto a base image/GIF.
    Returns (output_buffer, filename).
    """
    user_image_stream = io.BytesIO(base_image_bytes)
    output_buffer = io.BytesIO()

    with Image.open(user_image_stream) as base_img, Image.open(OVERLAY_PATH) as foreground:
        is_animated = getattr(base_img, "is_animated", False)
        bg_width, bg_height = base_img.size

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

            background.paste(foreground_rgba, (0, 0), mask=foreground_rgba)

            background.save(output_buffer, format="PNG")
            output_filename = "preview_result.png"

        output_buffer.seek(0)

    return output_buffer, output_filename
