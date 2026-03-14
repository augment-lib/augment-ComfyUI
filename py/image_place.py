# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import numpy as np
import json
from PIL import Image


class ImagePlaceNode:
    """
    Place an image onto a canvas at any x/y/w/h coordinates.
    Handles resizing, alpha compositing, and fit modes.
    Wire from Grid Coords, manual INTs, or any coordinate source.
    """

    FIT_MODES = ["fit", "fill", "stretch"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "canvas": ("IMAGE",),
                "image": ("IMAGE",),
                "x": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "y": ("INT", {"default": 0, "min": -8192, "max": 8192, "step": 1}),
                "width": ("INT", {"default": 512, "min": 1, "max": 8192, "step": 1}),
                "height": ("INT", {"default": 512, "min": 1, "max": 8192, "step": 1}),
                "fit": (cls.FIT_MODES, {"default": "fit"}),
            },
            "optional": {
                "mask": ("MASK",),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "mask", "json_result", "trigger")
    FUNCTION = "place"
    CATEGORY = "Augment/Image"

    @staticmethod
    def _tensor_to_pil(tensor):
        """Convert ComfyUI IMAGE tensor [B,H,W,C] to PIL RGBA."""
        img_np = tensor[0].cpu().numpy()
        img_np = np.clip(img_np * 255, 0, 255).astype(np.uint8)

        if img_np.shape[2] == 4:
            return Image.fromarray(img_np, "RGBA")
        else:
            return Image.fromarray(img_np, "RGB").convert("RGBA")

    @staticmethod
    def _pil_to_tensor(pil_img):
        """Convert PIL RGB image to ComfyUI IMAGE tensor [1,H,W,3]."""
        img_np = np.array(pil_img.convert("RGB")).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)

    @staticmethod
    def _resize_fit(pil_img, target_w, target_h):
        """Resize to fit inside target, preserving aspect ratio (letterbox)."""
        src_w, src_h = pil_img.size
        scale = min(target_w / src_w, target_h / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        resized = pil_img.resize((new_w, new_h), Image.LANCZOS)

        # Center on transparent canvas
        result = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        result.paste(resized, (offset_x, offset_y), resized)
        return result

    @staticmethod
    def _resize_fill(pil_img, target_w, target_h):
        """Resize to fill target, cropping excess (cover)."""
        src_w, src_h = pil_img.size
        scale = max(target_w / src_w, target_h / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        resized = pil_img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def _resize_stretch(pil_img, target_w, target_h):
        """Stretch to exact target size."""
        return pil_img.resize((target_w, target_h), Image.LANCZOS)

    def place(self, canvas, image, x, y, width, height, fit, mask=None, trigger=None):
        canvas_pil = self._tensor_to_pil(canvas)
        image_pil = self._tensor_to_pil(image)

        canvas_w, canvas_h = canvas_pil.size

        # Resize image to target region
        if fit == "fit":
            placed = self._resize_fit(image_pil, width, height)
        elif fit == "fill":
            placed = self._resize_fill(image_pil, width, height)
        else:
            placed = self._resize_stretch(image_pil, width, height)

        # Apply external mask to placed image's alpha if provided
        if mask is not None:
            mask_pil = Image.fromarray((mask[0].cpu().numpy() * 255).astype(np.uint8), "L")
            mask_resized = mask_pil.resize((placed.size[0], placed.size[1]), Image.LANCZOS)
            placed_alpha = placed.split()[3]
            combined_alpha = Image.fromarray(
                np.minimum(np.array(placed_alpha), np.array(mask_resized)).astype(np.uint8), "L"
            )
            placed.putalpha(combined_alpha)

        # Composite onto canvas
        result = canvas_pil.copy()
        result.paste(placed, (x, y), placed)

        # Build placement mask (white where image was placed, including alpha)
        mask_img = Image.new("L", (canvas_w, canvas_h), 0)
        placed_alpha = placed.split()[3]
        mask_img.paste(placed_alpha, (x, y))

        # Convert outputs
        result_tensor = self._pil_to_tensor(result)
        mask_np = np.array(mask_img).astype(np.float32) / 255.0
        mask_tensor = torch.from_numpy(mask_np).unsqueeze(0)

        json_result = json.dumps({"node": "ImagePlaceNode", "x": x, "y": y, "width": width, "height": height, "fit": fit, "canvas_size": [canvas_w, canvas_h]})
        return (result_tensor, mask_tensor, json_result, trigger)