# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import hashlib
import secrets
import time
import json


class SHA256Node:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "encode": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("hash", "json", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, encode, trigger=None):
        h = hashlib.sha256(encode.encode("utf-8")).hexdigest()
        json_result = json.dumps({"node": "SHA-256 Hash", "input": encode, "hash": h, "algorithm": "sha256"})
        return {"ui": {"text": [h]}, "result": (h, json_result, "done")}


class RandomNumberNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("INT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("number", "json", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time()

    def execute(self, trigger=None):
        n = secrets.randbelow(1000000000)
        json_result = json.dumps({"node": "Random Number", "number": n, "max": 1000000000})
        return {"ui": {"text": [str(n)]}, "result": (n, json_result, "done")}


class UUIDNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("uuid", "json", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return time.time()

    def execute(self, trigger=None):
        u = secrets.token_hex(16)
        json_result = json.dumps({"node": "UUID Generator", "uuid": u, "length": 32})
        return {"ui": {"text": [u]}, "result": (u, json_result, "done")}


NODE_CLASS_MAPPINGS = {
    "SHA256Node": SHA256Node,
    "RandomNumberNode": RandomNumberNode,
    "UUIDNode": UUIDNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SHA256Node": "SHA-256 Hash",
    "RandomNumberNode": "Random Number",
    "UUIDNode": "UUID Generator",
}
