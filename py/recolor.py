# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json
import torch


class RecolorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "R": ("FLOAT", {"default": 255.0, "min": 0.0, "max": 255.0, "step": 1.0}),
                "G": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 255.0, "step": 1.0}),
                "B": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 255.0, "step": 1.0}),
            },
            "optional": {
                "hex_color": ("STRING", {"default": ""}),
                "preserve_luminance": ("BOOLEAN", {"default": True}),
                "blend": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("recolored_image", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Image"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, image, mask, R, G, B, hex_color="",
                preserve_luminance=True, blend=1.0, trigger=None):

        # --- Hex override (same pattern as WCAG node) ---
        h = hex_color.strip().lstrip("#")
        if len(h) == 6:
            try:
                R = float(int(h[0:2], 16))
                G = float(int(h[2:4], 16))
                B = float(int(h[4:6], 16))
            except ValueError:
                pass

        # --- Normalize target color to 0-1 ---
        t_r = R / 255.0
        t_g = G / 255.0
        t_b = B / 255.0

        # --- Work on clone ---
        img = image.clone()  # (batch, H, W, C)
        # Mask shape: (batch, H, W) or (H, W)
        m = mask.clone()
        if m.dim() == 2:
            m = m.unsqueeze(0)

        for i in range(img.shape[0]):
            frame = img[i]          # (H, W, C)
            frame_mask = m[i] if i < m.shape[0] else m[0]  # (H, W)
            frame_mask = frame_mask.unsqueeze(-1)  # (H, W, 1)

            # Clamp mask 0-1
            frame_mask = frame_mask.clamp(0.0, 1.0)

            if preserve_luminance:
                # BT.709 luminance from original pixel
                lum = (0.2126 * frame[:, :, 0]
                       + 0.7152 * frame[:, :, 1]
                       + 0.0722 * frame[:, :, 2])  # (H, W)

                # Target color scaled by luminance
                new_r = t_r * lum
                new_g = t_g * lum
                new_b = t_b * lum
                colored = torch.stack([new_r, new_g, new_b], dim=-1)  # (H, W, 3)
            else:
                # Flat color fill
                colored = torch.zeros_like(frame)
                colored[:, :, 0] = t_r
                colored[:, :, 1] = t_g
                colored[:, :, 2] = t_b

            # Blend: original → colored based on blend strength
            blended = frame * (1.0 - blend) + colored * blend

            # Apply via mask: masked areas get recolor, unmasked stay original
            img[i] = frame * (1.0 - frame_mask) + blended * frame_mask

        img = img.clamp(0.0, 1.0)

        json_result = json.dumps({
            "node": "RecolorNode",
            "R": int(R),
            "G": int(G),
            "B": int(B),
            "hex_color": hex_color if hex_color else f"#{int(R):02X}{int(G):02X}{int(B):02X}",
            "preserve_luminance": preserve_luminance,
            "blend": blend
        })

        return (img, json_result, "done")


NODE_CLASS_MAPPINGS = {
    "RecolorNode": RecolorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RecolorNode": "Recolor (Mask)",
}