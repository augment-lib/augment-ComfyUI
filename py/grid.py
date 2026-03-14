# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import numpy as np
import torch
import json
from PIL import Image, ImageDraw

from .utils import compute_all_edges

class GridGenerator:
    """Generates a grid image with configurable rows, columns, and line weight."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "rows": ("INT", {"default": 8, "min": 1, "max": 128, "step": 1}),
                "cols": ("INT", {"default": 8, "min": 1, "max": 128, "step": 1}),
                "line_weight": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
            },
            "optional": {
                "invert": ("BOOLEAN", {"default": False}),
                "dotted": ("BOOLEAN", {"default": False}),
                "dotted_line_weight": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
                "dotted_spacing": ("INT", {"default": 10, "min": 3, "max": 60, "step": 1}),
                "line_color": ("STRING", {"default": "#000000"}),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT", "INT", "INT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "mask", "rows", "cols", "width", "height", "json_result", "trigger")
    FUNCTION = "generate"
    CATEGORY = "Augment/Grid"

    def generate(self, rows, cols, line_weight, width, height, invert=False, dotted=False, dotted_line_weight=3, dotted_spacing=10, line_color="#000000", trigger=None):
        fg = _hex_to_rgb(line_color)
        if invert:
            bg = fg
            fg = (255 - bg[0], 255 - bg[1], 255 - bg[2])
        else:
            bg = (255, 255, 255)

        pil_img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(pil_img)

        if dotted:
            r = dotted_line_weight / 2.0
            cell_w = width / cols
            cell_h = height / rows
            dots_per_cell_x = max(1, round(cell_w / dotted_spacing))
            dots_per_cell_y = max(1, round(cell_h / dotted_spacing))
            sx = cell_w / dots_per_cell_x
            sy = cell_h / dots_per_cell_y

            for row in range(1, rows):
                y_pos = int(round(row * height / rows))
                x = 0.0
                while x < width:
                    draw.ellipse([x - r, y_pos - r, x + r, y_pos + r], fill=fg)
                    x += sx
            for col in range(1, cols):
                x_pos = int(round(col * width / cols))
                y = 0.0
                while y < height:
                    draw.ellipse([x_pos - r, y - r, x_pos + r, y + r], fill=fg)
                    y += sy
        else:
            for row in range(1, rows):
                y_pos = int(round(row * height / rows))
                draw.line([(0, y_pos), (width - 1, y_pos)], fill=fg, width=line_weight)
            for col in range(1, cols):
                x_pos = int(round(col * width / cols))
                draw.line([(x_pos, 0), (x_pos, height - 1)], fill=fg, width=line_weight)

        img_np = np.array(pil_img).astype(np.float32) / 255.0
        result_image = torch.from_numpy(img_np).unsqueeze(0)

        mask_val = img_np[:, :, 0]
        result_mask = torch.from_numpy(mask_val).unsqueeze(0)

        json_result = json.dumps({
            "node": "GridGenerator",
            "rows": rows,
            "cols": cols,
            "width": width,
            "height": height,
            "line_weight": line_weight,
            "dotted": dotted,
            "line_color": line_color
        })

        return (result_image, result_mask, rows, cols, width, height, json_result, "done")


def _hex_to_rgb(hex_str):
    """Convert a hex color string like '#ff0000' to an (R, G, B) tuple."""
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) != 6:
        return (0, 0, 0)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))