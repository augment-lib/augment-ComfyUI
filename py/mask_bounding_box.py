# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import numpy as np
import torch
import json


class MaskBoundingBox:
    """Finds the bounding box of non-zero mask content and outputs the cropped mask + coordinates."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "padding": ("INT", {"default": 0, "min": 0, "max": 512, "step": 1}),
                "invert": ("BOOLEAN", {"default": False}),
                "threshold": ("FLOAT", {"default": 0.10, "min": 0.01, "max": 1.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("MASK", "INT", "INT", "INT", "INT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("mask", "x", "y", "width", "height", "json_result", "trigger")
    FUNCTION = "find_bounds"
    CATEGORY = "Augment/Image"

    def find_bounds(self, mask, padding, invert, threshold):
        m = mask[0].cpu().numpy()
        img_h, img_w = m.shape

        if invert:
            m = 1.0 - m

        rows = np.any(m > threshold, axis=1)
        cols = np.any(m > threshold, axis=0)

        if not rows.any():
            x_min, y_min, out_w, out_h = 0, 0, img_w, img_h
        else:
            row_indices = np.where(rows)[0]
            col_indices = np.where(cols)[0]
            y_min, y_max = int(row_indices[0]), int(row_indices[-1])
            x_min, x_max = int(col_indices[0]), int(col_indices[-1])

            x_min = max(x_min - padding, 0)
            y_min = max(y_min - padding, 0)
            x_max = min(x_max + padding, img_w - 1)
            y_max = min(y_max + padding, img_h - 1)

            out_w = x_max - x_min + 1
            out_h = y_max - y_min + 1

        cropped_mask = mask[:, y_min:y_min + out_h, x_min:x_min + out_w]

        print(f"[augment] bounds: x={x_min} y={y_min} w={out_w} h={out_h}")

        json_result = json.dumps({
            "node": "MaskBoundingBox",
            "x": x_min,
            "y": y_min,
            "width": out_w,
            "height": out_h,
            "padding": padding,
            "invert": invert,
        })

        return (cropped_mask, x_min, y_min, out_w, out_h, json_result, "done")
