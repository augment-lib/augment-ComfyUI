# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Paid Node, credit values may change. 
# Augmentstudio.app

import io
import json
import os
import requests
import time
import folder_paths
import numpy as np
import torch
from PIL import Image


NODE_ID = "svg_to_png"
API_URL = "https://augmentstudio.app/api"

UPLOAD_DIR = folder_paths.get_input_directory()


class AugmentSVGToPNG:
    @classmethod
    def INPUT_TYPES(cls):
        files = sorted([
            f for f in os.listdir(UPLOAD_DIR)
            if f.lower().endswith(".svg")
        ])
        return {
            "required": {
                "svg_file": (files, {"image_upload": True}),
                "api_key": ("STRING", {"default": ""}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "TRIGGER")
    RETURN_NAMES = ("image", "alpha", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Vector"

    @classmethod
    def IS_CHANGED(cls, svg_file="", **kwargs):
        path = os.path.join(UPLOAD_DIR, svg_file)
        if os.path.isfile(path):
            return os.path.getmtime(path)
        return float("nan")

    @classmethod
    def VALIDATE_INPUTS(cls, svg_file="", **kwargs):
        path = os.path.join(UPLOAD_DIR, svg_file)
        if not os.path.isfile(path):
            return f"File not found: {svg_file}"
        return True

    def execute(self, svg_file, api_key, trigger=None):
        api_url = API_URL.rstrip("/")
        auth = {"Authorization": f"Bearer {api_key}"}

        path = os.path.join(UPLOAD_DIR, svg_file)
        with open(path, "rb") as f:
            svg_bytes = f.read()

        print(f"[Augment API] Submitting SVG: {svg_file} ({len(svg_bytes)} bytes)")
        try:
            r = requests.post(
                f"{api_url}/process",
                files={"image": (svg_file, svg_bytes, "image/svg+xml")},
                data={"node_id": NODE_ID},
                headers=auth,
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(f"[Augment API] Submit failed: {e}")
            raise

        if r.status_code != 200:
            raise RuntimeError(f"Submit error {r.status_code}: {r.text[:500]}")

        request_id = r.json().get("request_id")
        if not request_id:
            raise RuntimeError(f"No request_id: {r.text[:500]}")

        print(f"[Augment API] Job submitted: {request_id}")

        max_wait = 60
        elapsed = 0
        job_status = "unknown"

        while elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
            try:
                status_r = requests.get(
                    f"{api_url}/job/{request_id}/status",
                    headers=auth, timeout=10,
                )
                job_status = status_r.json().get("status", "unknown")
            except Exception as e:
                print(f"[Augment API] Poll error: {e}")
                continue

            if job_status == "done":
                break
            elif job_status == "error":
                raise RuntimeError(f"Job failed: {status_r.json().get('error')}")

        if job_status != "done":
            raise RuntimeError(f"Timed out after {max_wait}s")

        img_r = requests.get(
            f"{api_url}/job/{request_id}/image",
            headers=auth, timeout=60,
        )
        if img_r.status_code != 200:
            raise RuntimeError(f"Image fetch error: {img_r.status_code}")

        img = Image.open(io.BytesIO(img_r.content)).convert("RGBA")
        arr = np.array(img).astype(np.float32) / 255.0

        image_tensor = torch.from_numpy(arr[:, :, :3]).unsqueeze(0)
        mask_tensor = torch.from_numpy(arr[:, :, 3]).unsqueeze(0)

        print(f"[Augment API] Done! {img.size[0]}x{img.size[1]}")
        return (image_tensor, mask_tensor, "done")

class AugmentPNGToSVG:
    @classmethod
    def INPUT_TYPES(cls):
        files = sorted([
            f for f in os.listdir(UPLOAD_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ])
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
            },
            "optional": {
                "image": ("IMAGE",),
                "image_file": (files, {"image_upload": True}),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("SVG", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("svg", "json", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Vector"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time()

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, api_key, image=None, image_file=None, trigger=None):
        api_url = API_URL.rstrip("/")
        auth = {"Authorization": f"Bearer {api_key}"}

        if image is not None:
            from PIL import Image as PILImage
            img_np = (image[0].cpu().numpy() * 255).astype(np.uint8)
            pil_img = PILImage.fromarray(img_np, "RGB")
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            source_name = "image_input.png"
            mime = "image/png"
        elif image_file:
            path = os.path.join(UPLOAD_DIR, image_file)
            with open(path, "rb") as f:
                img_bytes = f.read()
            source_name = image_file
            ext = os.path.splitext(image_file)[1].lower()
            mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
            mime = mime_types.get(ext, "image/png")
        else:
            raise RuntimeError("No image provided — connect an image input or select a file")

        print(f"[Augment API] Submitting image: {source_name} ({len(img_bytes)} bytes)")
        try:
            r = requests.post(
                f"{api_url}/process",
                files={"image": (source_name, img_bytes, mime)},
                data={"node_id": "png_to_svg"},
                headers=auth,
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            print(f"[Augment API] Submit failed: {e}")
            raise

        if r.status_code != 200:
            raise RuntimeError(f"Submit error {r.status_code}: {r.text[:500]}")

        request_id = r.json().get("request_id")
        if not request_id:
            raise RuntimeError(f"No request_id: {r.text[:500]}")

        print(f"[Augment API] Job submitted: {request_id}")

        max_wait = 60
        elapsed = 0
        job_status = "unknown"

        while elapsed < max_wait:
            time.sleep(1)
            elapsed += 1
            try:
                status_r = requests.get(
                    f"{api_url}/job/{request_id}/status",
                    headers=auth, timeout=10,
                )
                job_status = status_r.json().get("status", "unknown")
            except Exception as e:
                print(f"[Augment API] Poll error: {e}")
                continue

            if job_status == "done":
                break
            elif job_status == "error":
                raise RuntimeError(f"Job failed: {status_r.json().get('error')}")

        if job_status != "done":
            raise RuntimeError(f"Timed out after {max_wait}s")

        svg_r = requests.get(
            f"{api_url}/job/{request_id}/image",
            headers=auth, timeout=60,
        )
        if svg_r.status_code != 200:
            raise RuntimeError(f"SVG fetch error: {svg_r.status_code}")

        from comfy_api.latest._util.image_types import SVG
        svg_bytes = io.BytesIO(svg_r.content)
        size = svg_bytes.getbuffer().nbytes
        print(f"[Augment API] Done! Received SVG ({size} bytes)")
        json_result = json.dumps({"node": "AugmentPNGToSVG", "size_bytes": size})
        return {"ui": {"text": [svg_r.text[:500]]}, "result": (SVG([svg_bytes]), json_result, "done")}


NODE_CLASS_MAPPINGS = {
    "AugmentSVGToPNG": AugmentSVGToPNG,
    "AugmentPNGToSVG": AugmentPNGToSVG,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AugmentSVGToPNG": "Augment SVG to PNG",
    "AugmentPNGToSVG": "Augment PNG to SVG",
}

