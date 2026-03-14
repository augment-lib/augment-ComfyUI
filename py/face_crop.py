# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json
import numpy as np
import torch
import cv2
import os

class FaceCrop:
    """Fast face crop using OpenCV. Image in, cropped image + coordinates out."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "padding": ("INT", {"default": 20, "min": 0, "max": 512, "step": 5}),
                "square": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "INT", "INT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("cropped", "x", "y", "width", "height", "json", "trigger")
    OUTPUT_NODE = False
    FUNCTION = "detect_and_crop"
    CATEGORY = "Augment/Image"

    def detect_and_crop(self, image, padding=20, square=True):
        img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
        img_h, img_w = img_np.shape[:2]

        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        # Try multiple paths to find the Haar cascade file
        cascade_file = None
        
        # Try cv2.data path first (if available)
        if hasattr(cv2, 'data'):
            try:
                cascade_file = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
                if os.path.exists(cascade_file):
                    pass  # Found it
                else:
                    cascade_file = None
            except:
                cascade_file = None
        
        # Try other common paths
        if not cascade_file:
            cascade_paths = [
                os.path.join(cv2.__path__[0], "data", "haarcascade_frontalface_alt2.xml"),
                "/usr/share/opencv4/haarcascades/haarcascade_frontalface_alt2.xml",
                "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_alt2.xml",
                "haarcascade_frontalface_alt2.xml",  # System path fallback
            ]
            
            for path in cascade_paths:
                if os.path.exists(path):
                    cascade_file = path
                    break
        
        if not cascade_file:
            cascade_file = "haarcascade_frontalface_alt2.xml"
        
        cascade = cv2.CascadeClassifier(cascade_file)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))

        face_count = len(faces) if isinstance(faces, np.ndarray) else 0

        if face_count == 0:
            print("[augment] FaceCrop: no faces detected")
            result_json = json.dumps({"node": "FaceCrop", "x": 0, "y": 0, "width": img_w, "height": img_h})
            return (image, 0, 0, img_w, img_h, result_json, "done")

        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        fx, fy, fw, fh = [int(v) for v in faces[0]]

        cx, cy = fx + fw // 2, fy + fh // 2
        fw += padding * 2
        fh += padding * 2

        if square:
            side = max(fw, fh)
            fw, fh = side, side

        x0 = max(0, cx - fw // 2)
        y0 = max(0, cy - fh // 2)
        x1 = min(img_w, x0 + fw)
        y1 = min(img_h, y0 + fh)

        out_x, out_y = int(x0), int(y0)
        out_w, out_h = int(x1 - x0), int(y1 - y0)

        print(f"[augment] FaceCrop: {face_count} face(s), crop x={out_x} y={out_y} w={out_w} h={out_h}")

        cropped = image[:, out_y:out_y + out_h, out_x:out_x + out_w, :]
        result_json = json.dumps({"node": "FaceCrop", "x": out_x, "y": out_y, "width": out_w, "height": out_h})
        return (cropped, out_x, out_y, out_w, out_h, result_json, "done")
