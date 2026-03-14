# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import torch
import numpy as np
import json

PHI = 1.6180339887  # Golden ratio


class GridCoordsNode:
    """
    Design layout engine. Pick a layout preset (golden_ratio, thirds, halves, quadrants)
    and a region name (top_left, center, etc.) — get back pixel coordinates.

    Companion node to Grid Generator.
    """

    LAYOUTS = ["golden_ratio", "thirds", "halves", "quadrants"]
    REGIONS = [
        "top_left", "top_center", "top_right",
        "center_left", "center", "center_right",
        "bottom_left", "bottom_center", "bottom_right",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "canvas_w": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
                "canvas_h": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
                "layout": (cls.LAYOUTS, {"default": "golden_ratio"}),
                "region": (cls.REGIONS, {"default": "center"}),
                "padding": ("INT", {"default": 0, "min": 0, "max": 1024, "step": 1}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "INT", "INT", "AUGMENT_JSON", "MASK", "TRIGGER")
    RETURN_NAMES = ("x", "y", "width", "height", "center_x", "center_y", "json_result", "mask", "trigger")
    FUNCTION = "calculate"
    CATEGORY = "Augment/Grid"

    # ------------------------------------------------------------------ #
    #  Split helpers — return the two split points for each axis
    # ------------------------------------------------------------------ #

    @staticmethod
    def _splits(size, layout, padding):
        """Return (split1, split2) pixel positions for a given axis length."""
        inner = size - 2 * padding
        p = padding

        if layout == "golden_ratio":
            s1 = p + int(inner / PHI)           # ~61.8 %
            s2 = p + int(inner - inner / PHI)    # ~38.2 %  (mirrored)
            # Ensure s1 < s2
            if s1 > s2:
                s1, s2 = s2, s1
            return (s1, s2)

        if layout == "thirds":
            third = inner / 3
            return (p + int(third), p + int(third * 2))

        if layout == "halves":
            half = inner // 2
            mid = p + half
            return (mid, mid)  # single split

        if layout == "quadrants":
            half = inner // 2
            mid = p + half
            return (mid, mid)

        return (p, size - p)

    # ------------------------------------------------------------------ #
    #  Region → bounding box
    # ------------------------------------------------------------------ #

    def _region_box(self, canvas_w, canvas_h, layout, region, padding):
        """
        Returns (x, y, w, h) for the named region.
        """
        sx1, sx2 = self._splits(canvas_w, layout, padding)
        sy1, sy2 = self._splits(canvas_h, layout, padding)
        p = padding
        cw = canvas_w - padding
        ch = canvas_h - padding

        # Build column boundaries  [left_edge, split1, split2, right_edge]
        # For halves/quadrants split1 == split2, giving us 2 zones per axis
        cols = sorted(set([p, sx1, sx2, cw]))
        rows = sorted(set([p, sy1, sy2, ch]))

        # Map region name → (col_index, row_index)
        region_map_3x3 = {
            "top_left":      (0, 0),
            "top_center":    (1, 0),
            "top_right":     (2, 0),
            "center_left":   (0, 1),
            "center":        (1, 1),
            "center_right":  (2, 1),
            "bottom_left":   (0, 2),
            "bottom_center": (1, 2),
            "bottom_right":  (2, 2),
        }

        # For 2-zone layouts (halves, quadrants) we collapse to 2x2
        region_map_2x2 = {
            "top_left":      (0, 0),
            "top_center":    (0, 0),  # collapse to top_left
            "top_right":     (1, 0),
            "center_left":   (0, 0),  # collapse to top_left
            "center":        (0, 0),  # collapse to top_left
            "center_right":  (1, 0),  # collapse to top_right
            "bottom_left":   (0, 1),
            "bottom_center": (0, 1),  # collapse to bottom_left
            "bottom_right":  (1, 1),
        }

        is_2zone = len(cols) <= 3 and len(rows) <= 3

        if is_2zone and len(cols) == 2:
            # True 2-col layout
            ci, ri = region_map_2x2[region]
        elif is_2zone and len(cols) == 3:
            # 3 boundaries but middle is duplicate — still pick properly
            ci, ri = region_map_2x2[region]
        else:
            ci, ri = region_map_3x3[region]

        # Clamp indices
        ci = min(ci, len(cols) - 2)
        ri = min(ri, len(rows) - 2)

        x = int(cols[ci])
        y = int(rows[ri])
        w = int(cols[ci + 1] - cols[ci])
        h = int(rows[ri + 1] - rows[ri])

        return x, y, w, h

    # ------------------------------------------------------------------ #
    #  Main
    # ------------------------------------------------------------------ #

    def calculate(self, canvas_w, canvas_h, layout, region, padding, trigger=None):
        x, y, w, h = self._region_box(canvas_w, canvas_h, layout, region, padding)

        center_x = x + w // 2
        center_y = y + h // 2

        # -- Normalized values --
        norm_x = round(x / canvas_w, 4) if canvas_w else 0
        norm_y = round(y / canvas_h, 4) if canvas_h else 0
        norm_w = round(w / canvas_w, 4) if canvas_w else 0
        norm_h = round(h / canvas_h, 4) if canvas_h else 0
        norm_cx = round(center_x / canvas_w, 4) if canvas_w else 0
        norm_cy = round(center_y / canvas_h, 4) if canvas_h else 0

        # -- All split lines for this layout (useful for LLM to understand full grid) --
        sx1, sx2 = self._splits(canvas_w, layout, padding)
        sy1, sy2 = self._splits(canvas_h, layout, padding)

        result = {
            "layout": layout,
            "region": region,
            "canvas": [canvas_w, canvas_h],
            "padding": padding,
            "box": {
                "x": x, "y": y, "w": w, "h": h,
                "right": x + w, "bottom": y + h,
                "center_x": center_x, "center_y": center_y,
            },
            "normalized": {
                "x": norm_x, "y": norm_y,
                "w": norm_w, "h": norm_h,
                "center_x": norm_cx, "center_y": norm_cy,
            },
            "splits": {
                "x": [sx1, sx2],
                "y": [sy1, sy2],
            },
        }

        json_result = json.dumps(result, indent=2)

        # -- Mask output: white rectangle at region on black canvas --
        mask = np.zeros((canvas_h, canvas_w), dtype=np.float32)
        mask[y : y + h, x : x + w] = 1.0
        mask_tensor = torch.from_numpy(mask).unsqueeze(0)

        return (int(x), int(y), int(w), int(h), int(center_x), int(center_y), json_result, mask_tensor, trigger)

