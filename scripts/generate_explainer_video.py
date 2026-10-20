"""Generate the DocuMind AI explainer video (30-45 seconds).

This is an asset-generation script, not part of the runtime application.
It renders frames with Pillow and encodes a real H.264 MP4 with
imageio + imageio-ffmpeg. Captions are burned into the video.

Usage:
    .venv/Scripts/python.exe scripts/generate_explainer_video.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 24
DURATION = 36.0
FADE = 0.35

BG = (244, 246, 251)
SURFACE = (255, 255, 255)
TEXT = (31, 36, 48)
MUTED = (107, 114, 128)
ACCENT = (79, 70, 229)
ACCENT_DARK = (67, 56, 202)
ACCENT_SOFT = (238, 242, 255)
BORDER = (227, 232, 240)
AMBER = (251, 191, 36)
AMBER_SOFT = (253, 230, 138)
GREEN = (6, 118, 71)
GREEN_SOFT = (236, 253, 243)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "frontend", "public")
OUT_VIDEO = os.path.join(OUT_DIR, "documind-explainer.mp4")
OUT_POSTER = os.path.join(OUT_DIR, "documind-explainer-poster.png")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_BRAND = load_font(22, True)
F_EYEBROW = load_font(20, True)
F_H1 = load_font(56, True)
F_H2 = load_font(46, True)
F_BODY = load_font(24)
F_BODY_SM = load_font(20)
F_SMALL = load_font(17)
F_CAPTION = load_font(24, True)
F_BTN = load_font(22, True)
F_LOGO = load_font(52, True)


def wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text_block(
    draw, text, xy, font, fill, max_width, line_gap=10, align="left"
) -> int:
    x, y = xy
    for line in wrap(draw, text, font, max_width):
        if align == "center":
            draw.text((x, y), line, font=font, fill=fill, anchor="ma")
        else:
            draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def background() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse([-220, -280, 540, 440], fill=(79, 70, 229, 20))
    d.ellipse([W - 480, -220, W + 220, 420], fill=(79, 70, 229, 14))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


BG_IMAGE = background()


def draw_brand(draw: ImageDraw.ImageDraw, x: int = 64, y: int = 48) -> None:
    draw_logo(draw, x + 20, y + 20, 40)
    draw.text((x + 50, y + 9), "DocuMind AI", font=F_BRAND, fill=TEXT)


def draw_logo(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float) -> None:
    half = size / 2
    draw.rounded_rectangle(
        [cx - half, cy - half, cx + half, cy + half],
        radius=size * 0.27,
        fill=ACCENT,
    )
    pad = size * 0.24
    draw.rounded_rectangle(
        [cx - half + pad, cy - half + pad * 0.9, cx + half - pad * 0.8, cy + half - pad * 0.9],
        radius=size * 0.06,
        fill=SURFACE,
    )
    line_x0 = cx - half + pad * 1.5
    line_x1 = cx + half - pad * 2.1
    for i, ly in enumerate((cy - size * 0.06, cy + size * 0.06, cy + size * 0.18)):
        draw.line(
            [(line_x0, ly), (line_x1 if i < 2 else line_x1 - size * 0.12, ly)],
            fill=ACCENT,
            width=max(2, int(size * 0.045)),
        )
    sparkle = [
        (cx + half * 0.52, cy - half * 0.86),
        (cx + half * 0.66, cy - half * 0.6),
        (cx + half * 0.92, cy - half * 0.46),
        (cx + half * 0.66, cy - half * 0.32),
        (cx + half * 0.52, cy - half * 0.06),
        (cx + half * 0.38, cy - half * 0.32),
        (cx + half * 0.12, cy - half * 0.46),
        (cx + half * 0.38, cy - half * 0.6),
    ]
    draw.polygon(sparkle, fill=AMBER)


def draw_caption(draw: ImageDraw.ImageDraw, text: str) -> None:
    box = [120, 636, W - 120, 692]
    draw.rounded_rectangle(box, radius=16, fill=(31, 36, 48))
    draw.text((W / 2, 664), text, font=F_CAPTION, fill=(255, 255, 255), anchor="mm")


def draw_progress(draw: ImageDraw.ImageDraw, t: float) -> None:
    draw.rectangle([0, H - 6, W, H], fill=(227, 232, 240))
    draw.rectangle([0, H - 6, W * (t / DURATION), H], fill=ACCENT)


def eyebrow(draw: ImageDraw.ImageDraw, text: str, y: int = 132) -> None:
    width = draw.textlength(text, font=F_EYEBROW) + 34
    draw.rounded_rectangle([80, y, 80 + width, y + 40], radius=20, fill=ACCENT_SOFT)
    draw.text((80 + width / 2, y + 20), text, font=F_EYEBROW, fill=ACCENT, anchor="mm")


def scene_problem(draw, t: float) -> None:
    eyebrow(draw, "THE PROBLEM")
    draw.text((80, 192), "Important answers are", font=F_H1, fill=TEXT)
    draw.text((80, 252), "buried in long documents.", font=F_H1, fill=TEXT)
    draw_text_block(
        draw,
        "Reading page by page is slow. Searching for keywords misses context.",
        (80, 336),
        F_BODY,
        MUTED,
        620,
        line_gap=8,
    )

    # Document stack
    for i, (dx, dy) in enumerate(((720, 180), (750, 200), (780, 220))):
        shade = SURFACE if i == 2 else (248, 250, 253)
        draw.rounded_rectangle(
            [dx, dy, dx + 330, dy + 360],
            radius=16,
            fill=shade,
            outline=BORDER,
            width=2,
        )
    for i in range(11):
        y = 250 + i * 27
        draw.rounded_rectangle([810, y, 810 + (240 if i % 3 else 190), y + 9], radius=4, fill=(226, 231, 240))
    draw.rounded_rectangle([812, 238, 1060, 260], radius=6, fill=(203, 213, 225))


def scene_upload(draw, t: float) -> None:
    eyebrow(draw, "STEP 1 · UPLOAD")
    draw.text((80, 192), "Drop in a PDF.", font=F_H1, fill=TEXT)
    draw_text_block(
        draw,
        "Text-based PDFs up to 20 MB. DocuMind extracts the text automatically.",
        (80, 268),
        F_BODY,
        MUTED,
        520,
        line_gap=8,
    )

    card = [80, 360, 640, 600]
    draw.rounded_rectangle(card, radius=18, fill=SURFACE, outline=BORDER, width=3)
    draw.ellipse([320, 390, 400, 470], fill=ACCENT_SOFT)
    draw.line([(360, 412), (360, 448)], fill=ACCENT, width=5)
    draw.line([(342, 430), (378, 430)], fill=ACCENT, width=5)
    draw.text((360, 495), "Drag and drop a PDF", font=F_BODY_SM, fill=TEXT, anchor="mm")
    draw.text((360, 524), "or click to browse", font=F_SMALL, fill=MUTED, anchor="mm")

    # File row with animated progress
    row = [700, 400, 1200, 540]
    draw.rounded_rectangle(row, radius=16, fill=SURFACE, outline=BORDER, width=2)
    draw.rounded_rectangle([724, 424, 768, 472], radius=8, fill=ACCENT_SOFT)
    draw.text((746, 448), "PDF", font=F_SMALL, fill=ACCENT, anchor="mm")
    draw.text((786, 428), "Security_Policy.pdf", font=F_BODY_SM, fill=TEXT)
    draw.text((786, 458), "PDF · 2.4 MB", font=F_SMALL, fill=MUTED)
    progress = min(1.0, max(0.0, (t - 1.0) / 3.2))
    draw.rounded_rectangle([724, 498, 1176, 510], radius=6, fill=(238, 241, 246))
    if progress > 0:
        draw.rounded_rectangle([724, 498, 724 + int(452 * progress), 510], radius=6, fill=ACCENT)
    draw.text((1176, 470), "Ready" if progress >= 1 else f"{int(progress * 100)}%", font=F_SMALL, fill=GREEN if progress >= 1 else MUTED, anchor="rm")


def scene_ask(draw, t: float) -> None:
    eyebrow(draw, "STEP 2 · ASK")
    draw.text((80, 192), "Ask in plain language.", font=F_H1, fill=TEXT)
    draw_text_block(
        draw,
        "No keywords, operators, or query syntax. Just ask what you want to know.",
        (80, 268),
        F_BODY,
        MUTED,
        520,
        line_gap=8,
    )

    window = [80, 360, 1200, 610]
    draw.rounded_rectangle(window, radius=18, fill=SURFACE, outline=BORDER, width=3)
    draw.text((112, 384), "Chat with your documents", font=F_BODY_SM, fill=TEXT)
    draw.line([(80, 422), (1200, 422)], fill=BORDER, width=2)

    draw.rounded_rectangle([760, 448, 1168, 520], radius=14, fill=ACCENT)
    draw_text_block(
        draw,
        "What does the policy say about VPN use?",
        (784, 468),
        F_BODY_SM,
        (255, 255, 255),
        360,
        line_gap=4,
    )

    draw.rounded_rectangle([112, 542, 640, 590], radius=14, fill=(246, 247, 251), outline=BORDER, width=2)
    dots = int(t * 4) % 4
    for i in range(3):
        cx = 148 + i * 24
        fill = ACCENT if i < dots else (203, 211, 225)
        draw.ellipse([cx - 6, 560, cx + 6, 572], fill=fill)


def scene_retrieve(draw, t: float) -> None:
    eyebrow(draw, "STEP 3 · RETRIEVE")
    draw.text((80, 192), "We find the relevant passages.", font=F_H1, fill=TEXT)
    draw_text_block(
        draw,
        "Your question becomes a vector. Qdrant returns the closest chunks.",
        (80, 268),
        F_BODY,
        MUTED,
        700,
        line_gap=8,
    )

    chunks = [
        (80, 360, "Chunk 1", "Employees must use the company VPN when accessing internal systems remotely.", False),
        (80, 452, "Chunk 2", "Passwords must be at least 12 characters and rotated every 90 days.", True),
        (80, 544, "Chunk 3", "Report suspected security incidents to the IT service desk within one hour.", False),
    ]
    for i, (x, y, label, text, active) in enumerate(chunks):
        appear = t > i * 0.35
        if not appear:
            continue
        outline = ACCENT if active else BORDER
        fill = ACCENT_SOFT if active else SURFACE
        width = 3 if active else 2
        draw.rounded_rectangle([x, y, x + 700, y + 76], radius=14, fill=fill, outline=outline, width=width)
        draw.text((x + 20, y + 14), label, font=F_SMALL, fill=ACCENT if active else MUTED)
        draw_text_block(draw, text, (x + 20, y + 38), F_SMALL, TEXT if active else MUTED, 650, line_gap=2)

    draw.line([(800, 490), (880, 490)], fill=ACCENT, width=4)
    draw.polygon([(880, 480), (900, 490), (880, 500)], fill=ACCENT)
    draw.rounded_rectangle([900, 430, 1200, 550], radius=18, fill=SURFACE, outline=BORDER, width=3)
    draw.text((1050, 462), "Qdrant", font=F_BTN, fill=TEXT, anchor="mm")
    draw.text((1050, 496), "vector search", font=F_SMALL, fill=MUTED, anchor="mm")
    draw.text((1050, 522), "top 5 chunks", font=F_SMALL, fill=ACCENT, anchor="mm")


def scene_answer(draw, t: float) -> None:
    eyebrow(draw, "STEP 4 · ANSWER")
    draw.text((80, 192), "A grounded answer, with sources.", font=F_H1, fill=TEXT)
    draw_text_block(
        draw,
        "KIE receives only the retrieved context and is instructed to answer from it.",
        (80, 268),
        F_BODY,
        MUTED,
        700,
        line_gap=8,
    )

    draw.rounded_rectangle([80, 360, 1200, 610], radius=18, fill=SURFACE, outline=BORDER, width=3)
    draw.text((112, 384), "DocuMind AI · gpt-5.6-terra", font=F_SMALL, fill=MUTED)
    draw.line([(80, 422), (1200, 422)], fill=BORDER, width=2)

    draw_text_block(
        draw,
        "Employees must use the company VPN when accessing internal systems remotely. The policy also requires multi-factor authentication for remote access.",
        (112, 452),
        F_BODY_SM,
        TEXT,
        1040,
        line_gap=8,
    )

    chip_y = 552
    for i, label in enumerate(("Security_Policy.pdf · p.1", "Access_Control.pdf · p.4")):
        x0 = 112 + i * 340
        draw.rounded_rectangle([x0, chip_y, x0 + 320, chip_y + 38], radius=19, fill=ACCENT_SOFT)
        draw.text((x0 + 16, chip_y + 19), label, font=F_SMALL, fill=ACCENT_DARK, anchor="lm")


def scene_closing(draw, t: float) -> None:
    draw_logo(draw, W / 2, 230, 120)
    draw.text((W / 2, 340), "DocuMind AI", font=F_LOGO, fill=TEXT, anchor="mm")
    draw.text(
        (W / 2, 408),
        "Chat with Your Documents. Find Answers Faster.",
        font=F_BODY,
        fill=MUTED,
        anchor="mm",
    )

    draw.rounded_rectangle([W / 2 - 120, 462, W / 2 + 120, 522], radius=30, fill=ACCENT)
    draw.text((W / 2, 492), "Get Started", font=F_BTN, fill=(255, 255, 255), anchor="mm")
    draw.text(
        (W / 2, 560),
        "Upload a PDF  →  Ask a question  →  Answer with sources",
        font=F_SMALL,
        fill=MUTED,
        anchor="mm",
    )


@dataclass
class Scene:
    start: float
    end: float
    caption: str
    render: Callable


SCENES = [
    Scene(0.0, 5.5, "Finding the right answer in a long PDF is slow.", scene_problem),
    Scene(5.5, 11.5, "Upload your PDF - the text is extracted automatically.", scene_upload),
    Scene(11.5, 17.5, "Ask a question in plain language.", scene_ask),
    Scene(17.5, 23.5, "DocuMind retrieves the most relevant passages.", scene_retrieve),
    Scene(23.5, 30.5, "KIE writes an answer grounded in those passages.", scene_answer),
    Scene(30.5, 36.0, "Start asking your documents today.", scene_closing),
]


def scene_frame(scene: Scene, local_time: float) -> Image.Image:
    frame = BG_IMAGE.copy()
    draw = ImageDraw.Draw(frame)
    draw_brand(draw)
    scene.render(draw, max(0.0, min(local_time, scene.end - scene.start)))
    draw_caption(draw, scene.caption)
    return frame


def frame_at(t: float) -> Image.Image:
    current = SCENES[0]
    for scene in SCENES:
        if scene.start <= t < scene.end:
            current = scene
            break
    else:
        current = SCENES[-1]

    frame = scene_frame(current, t - current.start)

    index = SCENES.index(current)
    if index > 0 and t - current.start < FADE:
        previous = SCENES[index - 1]
        prev_frame = scene_frame(previous, previous.end - previous.start)
        alpha = (t - current.start) / FADE
        frame = Image.blend(prev_frame, frame, alpha)

    draw = ImageDraw.Draw(frame)
    draw_progress(draw, t)
    return frame


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    total = int(DURATION * FPS)
    print(f"Rendering {total} frames at {W}x{H}, {FPS} fps -> {OUT_VIDEO}")

    writer = imageio.get_writer(
        OUT_VIDEO,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=None,
        output_params=["-movflags", "+faststart"],
    )
    try:
        for i in range(total):
            t = i / FPS
            frame = frame_at(t)
            writer.append_data(np.asarray(frame.convert("RGB")))
            if i % 96 == 0:
                print(f"  {i}/{total} frames")
    finally:
        writer.close()

    poster = frame_at(27.0)
    poster.save(OUT_POSTER, "PNG")
    print(f"Wrote poster: {OUT_POSTER}")

    size_mb = os.path.getsize(OUT_VIDEO) / (1024 * 1024)
    print(f"Done. Video: {OUT_VIDEO} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
