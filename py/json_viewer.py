# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json as json_module


class JsonViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json": ("AUGMENT_JSON", {"forceInput": True}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("json", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, json, trigger=None):
        try:
            parsed = json_module.loads(json)
            pretty = json_module.dumps(parsed, indent=2)
        except (json_module.JSONDecodeError, TypeError):
            pretty = str(json)

        return {
            "ui": {"text": [pretty]},
            "result": (json, "done")
        }
