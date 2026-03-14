# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import hashlib
import json
import os
import numpy as np
import torch
from PIL import Image, ImageOps, ImageSequence

import folder_paths
import node_helpers


class AugmentLoadImage:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
            },
            "optional": {
                "image_override": ("IMAGE",),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT", "MASK", "MASK", "MASK", "MASK", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("image", "width", "height", "alpha", "red", "green", "blue", "json", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "load_image"
    CATEGORY = "Augment/Image"

    def load_image(self, image, image_override=None, trigger=None):
        if image_override is not None:
            output_image = image_override
            h, w = output_image.shape[1], output_image.shape[2]
            has_alpha = False
            output_mask = torch.zeros((1, h, w), dtype=torch.float32)
            source_name = "override"
        else:
            image_path = folder_paths.get_annotated_filepath(image)
            img = node_helpers.pillow(Image.open, image_path)

            output_images = []
            output_masks = []
            for i in ImageSequence.Iterator(img):
                i = node_helpers.pillow(ImageOps.exif_transpose, i)
                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                has_alpha = 'A' in i.getbands()
                rgba = i.convert("RGBA")
                rgb = i.convert("RGB")

                image_tensor = torch.from_numpy(np.array(rgb).astype(np.float32) / 255.0)[None,]
                output_images.append(image_tensor)

                if has_alpha:
                    mask = 1.0 - torch.from_numpy(np.array(rgba.getchannel('A')).astype(np.float32) / 255.0)
                else:
                    mask = torch.zeros((rgb.size[1], rgb.size[0]), dtype=torch.float32)
                output_masks.append(mask.unsqueeze(0))

                if img.format == "MPO":
                    break

            if len(output_images) > 1:
                output_image = torch.cat(output_images, dim=0)
                output_mask = torch.cat(output_masks, dim=0)
            else:
                output_image = output_images[0]
                output_mask = output_masks[0]

            w = output_image.shape[2]
            h = output_image.shape[1]
            source_name = image

        img_np = output_image[0].numpy()
        red = torch.from_numpy(img_np[:, :, 0]).unsqueeze(0)
        green = torch.from_numpy(img_np[:, :, 1]).unsqueeze(0)
        blue = torch.from_numpy(img_np[:, :, 2]).unsqueeze(0)

        w = output_image.shape[2]
        h = output_image.shape[1]
        json_result = json.dumps({
            "node": "Load Image",
            "file": source_name,
            "width": w,
            "height": h,
            "has_alpha": has_alpha,
        })

        return {
            "ui": {"text": [f"{source_name}\n{w}x{h}"]},
            "result": (output_image, w, h, output_mask, red, green, blue, json_result, "done"),
        }

    @classmethod
    def IS_CHANGED(cls, image, image_override=None, trigger=None):
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(cls, image, image_override=None, trigger=None):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)
        return True
