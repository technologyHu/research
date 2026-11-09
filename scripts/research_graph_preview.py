"""Deterministic Pillow rendering of the same real nodes used by the web graph."""
from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 640
BG = (9, 15, 29)
TEXT = (228, 237, 248)
MUTED = (139, 157, 182)


def font(size):
    candidates = [os.environ.get("GRAPH_FONT", ""),
                  "C:/Windows/Fonts/msyh.ttc",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                  "/System/Library/Fonts/PingFang.ttc"]
    for path in candidates:
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Chinese font required. Install fonts-noto-cjk or set GRAPH_FONT to a local font file.")


def rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def blend(color, ratio):
    return tuple(int(BG[i] + (color[i] - BG[i]) * ratio) for i in range(3))


def fit(text, face, width):
    if face.getlength(text) <= width:
        return text
    while text and face.getlength(text + "…") > width:
        text = text[:-1]
    return text + "…"


def two_lines(text, face, width):
    first = ""
    while text and face.getlength(first + text[0]) <= width:
        first, text = first + text[0], text[1:]
    return [first] + ([fit(text, face, width)] if text else [])


def render_preview(graph, output: Path):
    fonts = {size: font(size) for size in (12, 13, 14, 16, 18, 20, 30)}
    base = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((1, 1, WIDTH - 2, HEIGHT - 2), radius=22, outline=(33, 48, 70), width=2)
    draw.text((38, 25), "RESEARCH  /  CONSTELLATION", font=fonts[12], fill=(101, 216, 201))
    draw.text((36, 51), "调研知识星图", font=fonts[30], fill=TEXT)
    draw.text((38, 103), "主题、类型与具体调研工作", font=fonts[14], fill=MUTED)
    branch = "BRANCH  " + graph["branch"]
    draw.text((WIDTH - 39 - fonts[13].getlength(branch), 36), branch, font=fonts[13], fill=MUTED)
    stats = graph["stats"]
    stats_text = f"{stats['themes']} 主题     {stats['types']} 类型     {stats['objects']} 项调研工作"
    draw.text((WIDTH - 39 - fonts[16].getlength(stats_text), 85), stats_text, font=fonts[16], fill=TEXT)
    draw.line((38, 145, WIDTH - 38, 145), fill=(33, 48, 70))
    rng = random.Random(73)
    for _ in range(140 if graph["nodes"] else 0):
        x, y = rng.randint(40, 832), rng.randint(166, 548)
        draw.ellipse((x, y, x + 1, y + 1), fill=(31, 43, 64))
    draw.line((868, 168, 868, 552), fill=(33, 48, 70))
    draw.text((894, 174), "类型图例", font=fonts[18], fill=TEXT)
    for i, (type_id, label) in enumerate(graph["types"].items()):
        top = 226 + i * 49
        draw.ellipse((897, top + 8, 905, top + 16), fill=rgb(graph["colors"][type_id]))
        draw.text((920, top), label, font=fonts[14], fill=MUTED)
    if not graph["nodes"]:
        draw.text((330, 315), "暂无调研工作", font=fonts[20], fill=TEXT)
        draw.text((177, 360), "新增调研计划或报告并纳入 Git 后，这里会自动更新。", font=fonts[14], fill=MUTED)
    draw.line((38, 576, WIDTH - 38, 576), fill=(33, 48, 70))
    for x, kind, label in [(43, "theme", "主题"), (117, "object", "对象 = 具体调研工作")]:
        radius = 4 if kind != "small" else 2
        shape = (x - radius, 606 - radius, x + radius, 606 + radius)
        draw.ellipse(shape, fill=(176, 160, 255) if kind == "theme" else MUTED)
        draw.text((x + 11, 596), label, font=fonts[13], fill=MUTED)
    caption = "点击进入交互图谱  ↗"
    draw.text((WIDTH - 39 - fonts[14].getlength(caption), 593), caption, font=fonts[14], fill=(101, 216, 201))
    nodes = graph["nodes"]
    indexed = {n["id"]: n for n in nodes}
    frames = []
    # A bounded preview stays readable as the full interactive graph grows.
    order = {"theme": 0, "object": 1}
    selected = {n["id"] for n in sorted(nodes, key=lambda n: (order[n["kind"]], n["id"]))[:85]}
    if len(nodes) > len(selected):
        draw.text((44, 166), f"预览 {len(selected)}/{len(nodes)} 个节点 · 完整图谱见交互页面", font=fonts[12], fill=MUTED)
    for frame_index in range(48 if nodes else 1):
        frame = base.copy()
        pen = ImageDraw.Draw(frame)
        phase = math.tau * frame_index / 48
        positions = {}
        for n in nodes:
            seed = int(hashlib.sha256(n["id"].encode()).hexdigest()[:8], 16) / 0xffffffff * math.tau
            amplitude = 0 if n["kind"] == "theme" else 2.5
            positions[n["id"]] = (44 + n["x"] * 780 + amplitude * math.cos(phase + seed),
                                    172 + n["y"] * 366 + amplitude * math.sin(phase + seed))
        for edge in graph["edges"]:
            if edge["source"] not in selected or edge["target"] not in selected:
                continue
            start, end = positions[edge["source"]], positions[edge["target"]]
            color = blend(rgb(indexed[edge["target"]]["color"]), 0.27)
            if edge["relation"] == "depends":
                for segment in range(0, 16, 2):
                    p1 = tuple(start[k] + (end[k] - start[k]) * segment / 16 for k in range(2))
                    p2 = tuple(start[k] + (end[k] - start[k]) * (segment + 1) / 16 for k in range(2))
                    pen.line((p1, p2), fill=(109, 118, 144), width=1)
            else:
                pen.line((start, end), fill=color, width=1)
        label_boxes = []
        for n in sorted(nodes, key=lambda n: n["kind"] != "theme"):
            if n["id"] not in selected:
                continue
            x, y = positions[n["id"]]
            radius = {"theme": 11, "object": 5}[n["kind"]]
            color = rgb(n["color"])
            if n["kind"] == "theme":
                pulse = (1 + math.sin(phase)) / 2
                halo = radius + 7 + pulse * 5
                pen.ellipse((x - halo, y - halo, x + halo, y + halo), outline=blend(color, 0.12 + pulse * 0.1))
            pen.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
            display_label = n.get("displayLabel") or n.get("taskId") or n["label"]
            if n["kind"] == "theme":
                label = fit(display_label, fonts[13], 240)
                tx = min(840 - fonts[13].getlength(label), max(40, x - fonts[13].getlength(label) / 2))
                pen.text((tx, y + radius + 9), label, font=fonts[13], fill=TEXT,
                         stroke_width=2, stroke_fill=BG)
                label_boxes.append((tx - 3, y + radius + 7, tx + fonts[13].getlength(label) + 3, y + radius + 29))
            elif len(selected) <= 35:
                label = fit(display_label, fonts[13], 178)
                label_width = fonts[13].getlength(label)
                label_height = 20
                candidates = [(x + 10, y - 10), (x - label_width / 2, y + 13),
                              (x - label_width / 2, y - label_height - 10), (x - label_width - 10, y - 10)]
                for tx, ty in candidates:
                    tx = min(841 - label_width, max(40, tx))
                    box = (tx - 3, ty - 2, tx + label_width + 3, ty + label_height)
                    if box[1] < 175 or box[3] > 557:
                        continue
                    if any(box[0] < b[2] and box[2] > b[0] and box[1] < b[3] and box[3] > b[1] for b in label_boxes):
                        continue
                    pen.text((tx, ty), label, font=fonts[13], fill=TEXT, stroke_width=2, stroke_fill=BG)
                    label_boxes.append(box)
                    break
        frames.append(frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    frames[0].convert("RGB").save(output / "preview.png", optimize=True)
    frames[0].save(output / "preview.gif", save_all=True, append_images=frames[1:],
                   duration=80, loop=0, optimize=False, disposal=2)
