# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import json


class InvertImageNode:
    """Invert an image's colors (1 - pixel value). Alpha passes through untouched."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "alpha": ("MASK",),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "MASK", "MASK", "MASK", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "alpha", "red", "green", "blue", "json", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Image"

    def execute(self, image, alpha=None, trigger=None):
        inverted = 1.0 - image
        h, w = image.shape[1], image.shape[2]

        if alpha is not None and alpha.shape[-2:] == (h, w) and alpha.any():
            has_alpha = True
            alpha_out = alpha
        else:
            has_alpha = False
            alpha_out = torch.zeros((1, h, w), dtype=torch.float32)

        img_np = inverted[0].cpu().numpy()
        red = torch.from_numpy(img_np[:, :, 0]).unsqueeze(0)
        green = torch.from_numpy(img_np[:, :, 1]).unsqueeze(0)
        blue = torch.from_numpy(img_np[:, :, 2]).unsqueeze(0)

        json_result = json.dumps({
            "node": "InvertImageNode",
            "width": w,
            "height": h,
            "has_alpha": has_alpha,
        })
        return (inverted, alpha_out, red, green, blue, json_result, "done")
