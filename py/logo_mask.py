# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json
import numpy as np
import torch
import cv2

class LogoMask:
    """Generates a filled mask from edge detection — ideal for logos, icons, and text."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "threshold_low": ("INT", {"default": 50, "min": 0, "max": 255, "step": 5}),
                "threshold_high": ("INT", {"default": 150, "min": 0, "max": 255, "step": 5}),
                "fill_holes": ("BOOLEAN", {"default": True}),
                "smooth": ("INT", {"default": 3, "min": 0, "max": 20, "step": 1}),
                "invert": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("MASK", "IMAGE", "IMAGE", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("mask", "mask_image", "masked_rgb", "json_result", "trigger")
    OUTPUT_NODE = False
    FUNCTION = "generate_mask"
    CATEGORY = "Augment/Image"

    def generate_mask(self, image, threshold_low=50, threshold_high=150,
                      fill_holes=True, smooth=3, invert=False):
        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # Detect background from corner pixels (10px sample from each corner)
        s = 10
        corners = np.concatenate([
            gray[:s, :s].flatten(),
            gray[:s, -s:].flatten(),
            gray[-s:, :s].flatten(),
            gray[-s:, -s:].flatten(),
        ])
        bg_mean = np.mean(corners)

        # threshold_low = tolerance (how far from bg a pixel must be to count as foreground)
        # Higher = stricter, lower = catches more
        if bg_mean > 127:
            # Light background — mask anything darker than (bg - tolerance)
            cutoff = max(0, bg_mean - threshold_low)
            _, mask = cv2.threshold(gray, int(cutoff), 255, cv2.THRESH_BINARY_INV)
        else:
            # Dark background — mask anything lighter than (bg + tolerance)
            cutoff = min(255, bg_mean + threshold_low)
            _, mask = cv2.threshold(gray, int(cutoff), 255, cv2.THRESH_BINARY)

        # Clean up noise
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_clean, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_clean, iterations=1)

        if fill_holes:
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy is not None:
                for i, cnt in enumerate(contours):
                    cv2.drawContours(mask, [cnt], 0, 255, cv2.FILLED)
        else:
            # Preserve negative space
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            filled = np.zeros_like(mask)
            if hierarchy is not None:
                for i, cnt in enumerate(contours):
                    if hierarchy[0][i][3] == -1:
                        cv2.drawContours(filled, [cnt], 0, 255, cv2.FILLED)
                for i, cnt in enumerate(contours):
                    if hierarchy[0][i][3] >= 0:
                        cv2.drawContours(filled, [cnt], 0, 0, cv2.FILLED)
            mask = filled

        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_clean, iterations=1)

        if smooth > 0:
            # Smooth contour geometry only — no pixel blurring
            smooth_mask = np.zeros_like(mask)
            contours_s, hierarchy_s = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy_s is not None:
                for i, cnt in enumerate(contours_s):
                    epsilon = smooth * 0.5
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    # Outer contours filled white, inner (holes) filled black
                    if hierarchy_s[0][i][3] == -1:
                        cv2.drawContours(smooth_mask, [approx], 0, 255, cv2.FILLED)
                if not fill_holes:
                    for i, cnt in enumerate(contours_s):
                        if hierarchy_s[0][i][3] >= 0:
                            epsilon = smooth * 0.5
                            approx = cv2.approxPolyDP(cnt, epsilon, True)
                            cv2.drawContours(smooth_mask, [approx], 0, 0, cv2.FILLED)
            mask = smooth_mask

        if invert:
            mask = cv2.bitwise_not(mask)

        # Bounding box of the mask content
        rows = np.any(mask > 0, axis=1)
        cols = np.any(mask > 0, axis=0)
        if rows.any():
            r = np.where(rows)[0]
            c = np.where(cols)[0]
            bx, by = int(c[0]), int(r[0])
            bw, bh = int(c[-1] - c[0] + 1), int(r[-1] - r[0] + 1)
        else:
            bx, by, bw, bh = 0, 0, mask.shape[1], mask.shape[0]

        total_contours = len(contours) if contours else 0
        coverage = float(np.sum(mask > 0) / mask.size * 100)
        print(f"[augment] LogoMask: {total_contours} contours, {coverage:.1f}% coverage")

        result = torch.from_numpy(mask.astype(np.float32) / 255.0).unsqueeze(0)

        # mask_image: mask as RGB (white on black)
        mask_rgb = np.stack([mask, mask, mask], axis=-1)  # (H, W, 3) 0-255
        mask_image = torch.from_numpy(mask_rgb.astype(np.float32) / 255.0).unsqueeze(0)  # (1, H, W, 3)

        # masked_rgb: original image with mask applied (black where mask is empty)
        mask_f = mask.astype(np.float32) / 255.0  # (H, W) 0-1
        masked = img_np.astype(np.float32) * mask_f[:, :, np.newaxis]  # (H, W, 3)
        masked_rgb = torch.from_numpy(masked / 255.0).unsqueeze(0)  # (1, H, W, 3)

        result_json = json.dumps({
            "node": "LogoMask",
            "x": bx, "y": by, "width": bw, "height": bh,
            "contours": total_contours, "coverage_pct": round(coverage, 1)
        })
        return (result, mask_image, masked_rgb, result_json, "done")
