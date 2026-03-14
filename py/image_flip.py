# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import json


class ImageFlipNode:
    """Flip an image horizontally, vertically, or both."""

    MODES = ["horizontal", "vertical", "both"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "direction": (cls.MODES, {"default": "horizontal"}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Image"

    def execute(self, image, direction, trigger=None):
        if direction == "horizontal":
            flipped = torch.flip(image, [2])
        elif direction == "vertical":
            flipped = torch.flip(image, [1])
        else:
            flipped = torch.flip(image, [1, 2])

        json_result = json.dumps({"node": "ImageFlipNode", "direction": direction, "shape": list(image.shape)})
        return (flipped, json_result, "done")
