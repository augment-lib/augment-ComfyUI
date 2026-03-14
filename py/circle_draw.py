# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import numpy as np
from PIL import Image, ImageDraw
import json
import math

PHI = 1.6180339887


class CircleDrawNode:
    """
    Draw construction circles. Three modes:
    - fibonacci: reads spiral JSON and draws circles at each subdivision step
    - single: one circle from manual center_x/center_y/radius
    - concentric: multiple circles from center, scaled by golden ratio
    """

    MODES = ["fibonacci", "single", "concentric"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 632, "min": 64, "max": 8192, "step": 1}),
                "mode": (cls.MODES, {"default": "fibonacci"}),
                "center_x": ("INT", {"default": 512, "min": -8192, "max": 8192, "step": 1}),
                "center_y": ("INT", {"default": 316, "min": -8192, "max": 8192, "step": 1}),
                "radius": ("INT", {"default": 200, "min": 1, "max": 8192, "step": 1}),
                "rings": ("INT", {"default": 5, "min": 1, "max": 12, "step": 1}),
                "line_weight": ("INT", {"default": 1, "min": 1, "max": 20, "step": 1}),
                "line_color": ("STRING", {"default": "#FFFFFF"}),
                "dotted": ("BOOLEAN", {"default": False}),
                "invert": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "spiral_json": ("AUGMENT_JSON",),
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
    def _draw_circle(draw, cx, cy, r, color, weight, dotted=False):
        """Draw a single circle, optionally dotted."""
        if r < 1:
            return

        bbox = [cx - r, cy - r, cx + r, cy + r]

        if not dotted:
            draw.ellipse(bbox, outline=color, width=weight)
        else:
            # Draw dotted circle using small arcs
            steps = max(36, int(r * 0.5))
            gap = 360 / steps
            for i in range(0, steps, 2):
                start = i * gap
                end = start + gap
                draw.arc(bbox, start=start, end=end, fill=color, width=weight)

    def draw(
        self,
        width,
        height,
        mode,
        center_x,
        center_y,
        radius,
        rings,
        line_weight,
        line_color,
        dotted,
        invert,
        spiral_json=None,
        trigger=None,
    ):
        color = self._hex_to_rgb(line_color)

        # Supersampling
        ss = 2
        sw, sh = width * ss, height * ss
        slw = line_weight * ss

        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        circles_data = []

        if mode == "fibonacci" and spiral_json:
            # Parse spiral JSON and draw circles at each step
            if isinstance(spiral_json, str):
                spiral = json.loads(spiral_json)
            else:
                spiral = spiral_json

            steps = spiral.get("steps", [])
            for step in steps:
                cx = step["arc_center"]["x"] * ss
                cy = step["arc_center"]["y"] * ss
                r = step["radius"] * ss

                self._draw_circle(draw, cx, cy, r, color + (255,), slw, dotted)

                # Also draw small crosshair at center
                ch_size = max(4, slw * 2)
                draw.line([(cx - ch_size, cy), (cx + ch_size, cy)], fill=color + (120,), width=max(1, slw // 2))
                draw.line([(cx, cy - ch_size), (cx, cy + ch_size)], fill=color + (120,), width=max(1, slw // 2))

                circles_data.append({
                    "center": {"x": step["arc_center"]["x"], "y": step["arc_center"]["y"]},
                    "radius": step["radius"],
                    "iteration": step["iteration"],
                })

        elif mode == "concentric":
            # Draw rings scaling by golden ratio from center
            cx = center_x * ss
            cy = center_y * ss
            r = radius * ss

            for i in range(rings):
                current_r = int(r)
                self._draw_circle(draw, cx, cy, current_r, color + (255,), slw, dotted)

                # Crosshair at center (only on first)
                if i == 0:
                    ch_size = max(6, slw * 3)
                    draw.line([(cx - ch_size, cy), (cx + ch_size, cy)], fill=color + (120,), width=max(1, slw // 2))
                    draw.line([(cx, cy - ch_size), (cx, cy + ch_size)], fill=color + (120,), width=max(1, slw // 2))

                circles_data.append({
                    "center": {"x": center_x, "y": center_y},
                    "radius": int(current_r // ss),
                    "ring": i,
                    "scale": round(1 / (PHI ** i), 4),
                })

                r = r / PHI

        else:
            # Single circle
            cx = center_x * ss
            cy = center_y * ss
            r = radius * ss

            self._draw_circle(draw, cx, cy, int(r), color + (255,), slw, dotted)

            # Crosshair
            ch_size = max(6, slw * 3)
            draw.line([(cx - ch_size, cy), (cx + ch_size, cy)], fill=color + (120,), width=max(1, slw // 2))
            draw.line([(cx, cy - ch_size), (cx, cy + ch_size)], fill=color + (120,), width=max(1, slw // 2))

            circles_data.append({
                "center": {"x": center_x, "y": center_y},
                "radius": radius,
            })

        # Downsample
        img = img.resize((width, height), Image.LANCZOS)

        # Build output
        result = {
            "mode": mode,
            "canvas": [width, height],
            "circles": circles_data,
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

