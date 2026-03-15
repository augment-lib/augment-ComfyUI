# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json
import torch
import numpy as np
from PIL import Image
import folder_paths
import os


class BlurAverageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "FLOAT", "FLOAT", "FLOAT", "JSON", "TRIGGER")
    RETURN_NAMES = ("color_swatch","R", "G", "B", "json", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Augment/Image"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, image, trigger=None):
        # image tensor shape: (batch, height, width, channels) with values 0-1
        img = image[0]

        # Mean across all pixels
        r_avg = img[:, :, 0].mean().item()
        g_avg = img[:, :, 1].mean().item()
        b_avg = img[:, :, 2].mean().item()

        # Convert to 0-255
        r_255 = round(r_avg * 255)
        g_255 = round(g_avg * 255)
        b_255 = round(b_avg * 255)

        hex_color = "#{:02X}{:02X}{:02X}".format(r_255, g_255, b_255)

        # --- Generate swatch as IMAGE output (64x64) ---
        swatch = torch.zeros(1, 64, 64, 3)
        swatch[:, :, :, 0] = r_avg
        swatch[:, :, :, 1] = g_avg
        swatch[:, :, :, 2] = b_avg

        # --- Save temp image for in-node preview ---
        preview_img = Image.new("RGB", (64, 64), (r_255, g_255, b_255))
        temp_dir = folder_paths.get_temp_directory()
        os.makedirs(temp_dir, exist_ok=True)
        preview_filename = f"blur_avg_{hex_color.lstrip('#')}.png"
        preview_path = os.path.join(temp_dir, preview_filename)
        preview_img.save(preview_path)

        results = {
            "r": r_255,
            "g": g_255,
            "b": b_255,
            "hex": hex_color,
            "r_float": round(r_avg, 6),
            "g_float": round(g_avg, 6),
            "b_float": round(b_avg, 6),
        }

        return {
            "ui": {
                "images": [
                    {
                        "filename": preview_filename,
                        "subfolder": "",
                        "type": "temp",
                    }
                ]
            },
            "result": (swatch, float(r_255), float(g_255), float(b_255), json.dumps(results, indent=2), "done"),
        }


NODE_CLASS_MAPPINGS = {
    "BlurAverageNode": BlurAverageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BlurAverageNode": "Blur Average (Dominant Color)",
}

