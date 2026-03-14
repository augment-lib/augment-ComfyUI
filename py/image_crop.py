# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json
import numpy as np
import torch
import cv2

class ImageCrop:
    """Simple image crop. Accepts x, y, width, height — wires to any node outputting INT."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "x": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "y": ("INT", {"default": 0, "min": 0, "max": 8192, "step": 1}),
                "width": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 256, "min": 1, "max": 8192, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT", "INT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "x", "y", "width", "height", "json_result", "trigger")
    OUTPUT_NODE = False
    FUNCTION = "crop"
    CATEGORY = "Augment/Image"

    def crop(self, image, x, y, width, height):
        img_h, img_w = image.shape[1], image.shape[2]

        # Clamp to image bounds
        x0 = max(0, min(x, img_w - 1))
        y0 = max(0, min(y, img_h - 1))
        x1 = min(img_w, x0 + width)
        y1 = min(img_h, y0 + height)

        out_w = int(x1 - x0)
        out_h = int(y1 - y0)
        out_x = int(x0)
        out_y = int(y0)

        cropped = image[:, out_y:out_y + out_h, out_x:out_x + out_w, :]

        print(f"[augment] ImageCrop: x={out_x} y={out_y} w={out_w} h={out_h}")

        result_json = json.dumps({"node": "ImageCrop", "x": out_x, "y": out_y, "width": out_w, "height": out_h})
        return (cropped, out_x, out_y, out_w, out_h, result_json, "done")