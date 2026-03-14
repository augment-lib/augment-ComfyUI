# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import numpy as np
from PIL import Image, ImageDraw
import json
import math


class LineDrawNode:
    """
    Draw a line from point A to point B.
    Outputs image overlay and mask. Supersampled 2x for clean anti-aliased lines.
    """

    PRESETS = [
        "custom",
        "vertical_center",
        "horizontal_center",
        "diagonal_left",
        "diagonal_right",
        "outline",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 1}),
                "preset": (cls.PRESETS, {"default": "diagonal_left"}),
                "x1": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y1": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "x2": ("INT", {"default": 1024, "min": -8192, "max": 8192, "step": 1}),
                "y2": ("INT", {"default": 1024, "min": -8192, "max": 8192, "step": 1}),
                "line_weight": ("INT", {"default": 2, "min": 1, "max": 20, "step": 1}),
                "line_color": ("STRING", {"default": "#FFFFFF"}),
                "extend": ("BOOLEAN", {"default": False}),
                "invert": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "mask", "json_result", "trigger")
    FUNCTION = "draw"
    CATEGORY = "Augment/Grid"

    @staticmethod
    def _hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _extend_line(x1, y1, x2, y2, w, h):
        """Extend line to canvas edges."""
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return x1, y1, x2, y2

        # Find parameter t where line hits each edge
        # line: (x1 + t*dx, y1 + t*dy)
        t_values = []

        if dx != 0:
            # Left edge: x = 0
            t = -x1 / dx
            y_at = y1 + t * dy
            if 0 <= y_at <= h:
                t_values.append(t)
            # Right edge: x = w
            t = (w - x1) / dx
            y_at = y1 + t * dy
            if 0 <= y_at <= h:
                t_values.append(t)

        if dy != 0:
            # Top edge: y = 0
            t = -y1 / dy
            x_at = x1 + t * dx
            if 0 <= x_at <= w:
                t_values.append(t)
            # Bottom edge: y = h
            t = (h - y1) / dy
            x_at = x1 + t * dx
            if 0 <= x_at <= w:
                t_values.append(t)

        if len(t_values) < 2:
            return x1, y1, x2, y2

        t_min = min(t_values)
        t_max = max(t_values)

        ex1 = int(x1 + t_min * dx)
        ey1 = int(y1 + t_min * dy)
        ex2 = int(x1 + t_max * dx)
        ey2 = int(y1 + t_max * dy)

        return ex1, ey1, ex2, ey2

    def draw(self, width, height, preset, x1, y1, x2, y2, line_weight, line_color, extend, invert, trigger=None):
        color = self._hex_to_rgb(line_color)

        # Resolve preset into coordinates
        lines = []  # list of (x1, y1, x2, y2) — outline draws 4 lines

        if preset == "vertical_center":
            mx = width // 2
            lines = [(mx, 0, mx, height)]
        elif preset == "horizontal_center":
            my = height // 2
            lines = [(0, my, width, my)]
        elif preset == "diagonal_left":
            lines = [(0, 0, width, height)]
        elif preset == "diagonal_right":
            lines = [(width, 0, 0, height)]
        elif preset == "outline":
            lines = [
                (0, 0, width - 1, 0),
                (width - 1, 0, width - 1, height - 1),
                (width - 1, height - 1, 0, height - 1),
                (0, height - 1, 0, 0),
            ]
        else:
            # custom — use raw x1/y1/x2/y2
            lines = [(x1, y1, x2, y2)]

        # Supersampling
        ss = 2
        sw, sh = width * ss, height * ss
        slw = line_weight * ss

        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        drawn_lines = []
        for lx1, ly1, lx2, ly2 in lines:
            sx1, sy1, sx2, sy2 = lx1 * ss, ly1 * ss, lx2 * ss, ly2 * ss

            if extend and preset == "custom":
                sx1, sy1, sx2, sy2 = self._extend_line(sx1, sy1, sx2, sy2, sw, sh)

            draw.line([(sx1, sy1), (sx2, sy2)], fill=color + (255,), width=slw)

            # Track actual coords for JSON
            ax1, ay1, ax2, ay2 = sx1 // ss, sy1 // ss, sx2 // ss, sy2 // ss
            dx = ax2 - ax1
            dy = ay2 - ay1
            length = math.sqrt(dx * dx + dy * dy)
            angle = math.degrees(math.atan2(dy, dx))

            drawn_lines.append({
                "a": {"x": ax1, "y": ay1},
                "b": {"x": ax2, "y": ay2},
                "midpoint": {"x": (ax1 + ax2) // 2, "y": (ay1 + ay2) // 2},
                "length": round(length, 2),
                "angle": round(angle, 2),
            })

        # Downsample
        img = img.resize((width, height), Image.LANCZOS)

        result = {
            "preset": preset,
            "canvas": [width, height],
            "lines": drawn_lines,
        }

        if extend and preset == "custom":
            ex1, ey1, ex2, ey2 = self._extend_line(x1, y1, x2, y2, width, height)
            result["extended"] = {
                "a": {"x": ex1, "y": ey1},
                "b": {"x": ex2, "y": ey2},
            }

        json_result = json.dumps(result, indent=2)

        # Convert
        img_np = np.array(img)
        alpha = img_np[:, :, 3].astype(np.float32) / 255.0
        if invert:
            alpha = 1.0 - alpha

        rgb = img_np[:, :, :3].astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(rgb).unsqueeze(0)
        mask_tensor = torch.from_numpy(alpha).unsqueeze(0)

        return (image_tensor, mask_tensor, json_result, trigger)