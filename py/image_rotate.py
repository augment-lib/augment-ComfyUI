# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import numpy as np
import json
from PIL import Image


class ImageRotateNode:
    """Rotate an image by preset or custom angle."""

    PRESETS = ["0", "90", "180", "270", "custom"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "angle": (cls.PRESETS, {"default": "90"}),
                "custom_angle": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.5}),
                "expand": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Image"

    def execute(self, image, angle, custom_angle, expand, trigger=None):
        deg = custom_angle if angle == "custom" else float(angle)

        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_np)

        rotated = pil_img.rotate(-deg, resample=Image.BICUBIC, expand=expand, fillcolor=(0, 0, 0))

        result_np = np.array(rotated).astype(np.float32) / 255.0
        result_tensor = torch.from_numpy(result_np).unsqueeze(0)

        h, w = result_np.shape[:2]
        json_result = json.dumps({"node": "ImageRotateNode", "angle": deg, "expand": expand, "size": [w, h]})
        return (result_tensor, json_result, "done")
