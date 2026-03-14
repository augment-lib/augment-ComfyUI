# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import numpy as np
import torch
import json
from PIL import Image, ImageDraw


LINE_COLOR = (180, 180, 180)


class ConstructionLineOverlay:
    """Draws construction lines on an image from bounding box."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "x": ("INT", {"default": 0}),
                "y": ("INT", {"default": 0}),
                "width": ("INT", {"default": 100}),
                "height": ("INT", {"default": 100}),
            },
            "optional": {
                "show_bbox": ("BOOLEAN", {"default": True}),
                "show_centers": ("BOOLEAN", {"default": True}),
                "show_diagonals": ("BOOLEAN", {"default": True}),
                "dot_weight": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
                "dot_spacing": ("INT", {"default": 10, "min": 1, "max": 60, "step": 1}),
                "show_coords": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "json_result", "trigger")
    FUNCTION = "draw"
    CATEGORY = "Augment/Grid"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def draw(self, image, x, y, width, height,
             show_bbox=True, show_centers=True, show_diagonals=True,
             dot_weight=3, dot_spacing=10, show_coords=False):

        dot_weight = max(1, dot_weight)
        dot_spacing = max(3, dot_spacing)

        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        img_h, img_w = img_np.shape[:2]
        pil_img = Image.fromarray(img_np, "RGB")
        draw = ImageDraw.Draw(pil_img)

        x0, y0 = x, y
        x1, y1 = x + width - 1, y + height - 1
        cx, cy = x + width // 2, y + height // 2
        r = dot_weight / 2.0

        if show_diagonals:
            _draw_dotted_line_any(draw, (x0, y0), (x1, y1), LINE_COLOR, r, dot_spacing)
            _draw_dotted_line_any(draw, (x1, y0), (x0, y1), LINE_COLOR, r, dot_spacing)

        if show_centers:
            _draw_dotted_line_h(draw, 0, img_w, cy, LINE_COLOR, r, dot_spacing)
            _draw_dotted_line_v(draw, 0, img_h, cx, LINE_COLOR, r, dot_spacing)

        if show_bbox:
            _draw_dotted_line_h(draw, x0, x1, y0, LINE_COLOR, r, dot_spacing)
            _draw_dotted_line_h(draw, x0, x1, y1, LINE_COLOR, r, dot_spacing)
            _draw_dotted_line_v(draw, y0, y1, x0, LINE_COLOR, r, dot_spacing)
            _draw_dotted_line_v(draw, y0, y1, x1, LINE_COLOR, r, dot_spacing)

            if show_coords:
                _draw_label(draw, f"{width}px", (cx, y0 - 10), LINE_COLOR, align="center")
                _draw_label(draw, f"{height}px", (x1 + 8, cy), LINE_COLOR, align="left")

        result_np = np.array(pil_img).astype(np.float32) / 255.0
        result = torch.from_numpy(result_np).unsqueeze(0)

        json_result = json.dumps({
            "node": "ConstructionLineOverlay",
            "x": x, "y": y, "width": width, "height": height,
            "center": [cx, cy],
        })

        return (result, json_result, "done")


def _draw_dotted_line_h(draw, x_start, x_end, y_pos, color, r, spacing):
    """Horizontal dotted line using evenly spaced circles (matches grid.py)."""
    x = float(x_start)
    while x <= x_end:
        draw.ellipse([x - r, y_pos - r, x + r, y_pos + r], fill=color)
        x += spacing


def _draw_dotted_line_v(draw, y_start, y_end, x_pos, color, r, spacing):
    """Vertical dotted line using evenly spaced circles (matches grid.py)."""
    y = float(y_start)
    while y <= y_end:
        draw.ellipse([x_pos - r, y - r, x_pos + r, y + r], fill=color)
        y += spacing


def _draw_dotted_line_any(draw, p1, p2, color, r, spacing):
    """Diagonal dotted line using evenly spaced circles."""
    x0, y0 = p1
    x1, y1 = p2
    dx, dy = x1 - x0, y1 - y0
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos <= length:
        px = x0 + ux * pos
        py = y0 + uy * pos
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)
        pos += spacing


def _draw_label(draw, text, position, color, align="left"):
    """Draw a small coordinate label."""
    x, y = position
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    anchor = "rm" if align == "right" else ("mm" if align == "center" else "lm")
    draw.text((x, y), text, fill=color, font=font, anchor=anchor)