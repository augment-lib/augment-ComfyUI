# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import numpy as np
from PIL import Image, ImageDraw
import json
import math

PHI = 1.6180339887


class FibonacciSpiralNode:
    """
    Draw a Fibonacci/Golden Ratio spiral with optional subdivision rectangles.
    Each iteration subdivides the remaining golden rectangle and draws a quarter arc.
    Companion to Grid Generator and Grid Coords.
    """

    DIRECTIONS = ["top_right", "bottom_right", "bottom_left", "top_left"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 1}),
                "iterations": ("INT", {"default": 8, "min": 2, "max": 16, "step": 1}),
                "line_weight": ("INT", {"default": 2, "min": 1, "max": 20, "step": 1}),
                "line_color": ("STRING", {"default": "#FFFFFF"}),
                "draw_rectangles": ("BOOLEAN", {"default": False}),
                "draw_spiral": ("BOOLEAN", {"default": True}),
                "invert": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "mask", "json_result", "trigger")
    FUNCTION = "generate"
    CATEGORY = "Augment/Grid"

    @staticmethod
    def _hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))

    def generate(
        self,
        width,
        height,
        iterations,
        line_weight,
        line_color,
        draw_rectangles,
        draw_spiral,
        invert,
        trigger=None,
    ):
        color = self._hex_to_rgb(line_color)

        # --- Work at 2x resolution for anti-aliased arcs, then downscale ---
        ss = 2  # supersampling factor
        sw, sh = width * ss, height * ss
        slw = line_weight * ss

        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rectangle colors for subdivision boxes
        rect_colors = [
            (255, 80, 80, 160),    # red
            (80, 255, 80, 160),    # green
            (80, 80, 255, 160),    # blue
            (255, 200, 60, 160),   # yellow
            (200, 80, 255, 160),   # purple
            (80, 220, 220, 160),   # cyan
        ]

        # --- Subdivision logic ---
        # We track the remaining rectangle and which corner the spiral starts from.
        # Direction cycle: the square is carved from a rotating corner each step.
        #   0 = carve from RIGHT  (square on right side)
        #   1 = carve from BOTTOM (square on bottom)
        #   2 = carve from LEFT   (square on left side)
        #   3 = carve from TOP    (square on top)

        rx, ry, rw, rh = 0.0, 0.0, float(sw), float(sh)

        spiral_data = []
        arc_points = []

        for i in range(iterations):
            direction = i % 4

            if direction == 0:
                # Carve square from RIGHT
                sq_size = rh
                sq_x = rx + rw - sq_size
                sq_y = ry
                # Arc: bottom-left quarter (from bottom to left of square)
                # Center at bottom-left of square
                cx, cy = sq_x, sq_y + sq_size
                start_angle = 270
                end_angle = 360
                # Remaining rect
                new_rx, new_ry = rx, ry
                new_rw, new_rh = rw - sq_size, rh

            elif direction == 1:
                # Carve square from BOTTOM
                sq_size = rw
                sq_x = rx
                sq_y = ry + rh - sq_size
                # Center at top-left of square
                cx, cy = sq_x, sq_y
                start_angle = 0
                end_angle = 90
                # Remaining rect
                new_rx, new_ry = rx, ry
                new_rw, new_rh = rw, rh - sq_size

            elif direction == 2:
                # Carve square from LEFT
                sq_size = rh
                sq_x = rx
                sq_y = ry
                # Center at top-right of square
                cx, cy = sq_x + sq_size, sq_y
                start_angle = 90
                end_angle = 180
                # Remaining rect
                new_rx, new_ry = rx + sq_size, ry
                new_rw, new_rh = rw - sq_size, rh

            else:
                # Carve square from TOP
                sq_size = rw
                sq_x = rx
                sq_y = ry
                # Center at bottom-right of square
                cx, cy = sq_x + sq_size, sq_y + sq_size
                start_angle = 180
                end_angle = 270
                # Remaining rect
                new_rx, new_ry = rx, ry + sq_size
                new_rw, new_rh = rw, rh - sq_size

            radius = sq_size

            # Store data
            step_data = {
                "iteration": i,
                "square": {
                    "x": round(sq_x / ss),
                    "y": round(sq_y / ss),
                    "size": round(sq_size / ss),
                },
                "arc_center": {
                    "x": round(cx / ss),
                    "y": round(cy / ss),
                },
                "radius": round(radius / ss),
                "direction": self.DIRECTIONS[direction],
            }
            spiral_data.append(step_data)

            # Draw subdivision rectangle
            if draw_rectangles:
                rc = rect_colors[i % len(rect_colors)]
                draw.rectangle(
                    [sq_x, sq_y, sq_x + sq_size, sq_y + sq_size],
                    outline=rc,
                    width=slw,
                )

            # Draw arc
            if draw_spiral:
                bbox = [
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                ]
                draw.arc(
                    bbox,
                    start=start_angle,
                    end=end_angle,
                    fill=color + (255,),
                    width=slw,
                )

            # Move to remaining rectangle
            rx, ry, rw, rh = new_rx, new_ry, new_rw, new_rh

            if rw < 2 or rh < 2:
                break

        # --- Downsample to target resolution ---
        img = img.resize((width, height), Image.LANCZOS)

        # --- Build mask from alpha ---
        img_np = np.array(img)
        alpha = img_np[:, :, 3].astype(np.float32) / 255.0

        if invert:
            alpha = 1.0 - alpha

        # Convert image to RGB tensor [1, H, W, 3]
        rgb = img_np[:, :, :3].astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(rgb).unsqueeze(0)

        # Mask tensor [1, H, W]
        mask_tensor = torch.from_numpy(alpha).unsqueeze(0)

        # JSON output
        result = {
            "canvas": [width, height],
            "iterations": len(spiral_data),
            "phi": round(PHI, 6),
            "steps": spiral_data,
        }
        json_result = json.dumps(result, indent=2)

        return (image_tensor, mask_tensor, json_result, trigger)

