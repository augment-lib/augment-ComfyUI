# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json as json_module


class JsonExtractNode:
    """Extract a specific value from JSON data by name."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json": ("AUGMENT_JSON",),
                "field_name": ("STRING", {"default": "value"}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("extracted_value", "json", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "extract"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def extract(self, json, field_name, trigger=None):
        try:
            data = json_module.loads(json)

            if "value" in data and field_name not in data:
                inner = data["value"]
                if isinstance(inner, str):
                    try:
                        inner = json_module.loads(inner)
                    except (json_module.JSONDecodeError, TypeError):
                        pass
                if isinstance(inner, dict) and field_name in inner:
                    data = inner

            fields = field_name.split(".")
            value = data
            for field in fields:
                value = value[field]

            result = str(value) if not isinstance(value, str) else value
            ui_text = f"Field: {field_name}\nValue: {result}"
        except (json_module.JSONDecodeError, KeyError, TypeError):
            result = ""
            ui_text = f"Field: {field_name}\nError: Could not find field or invalid JSON"

        return {
            "ui": {"text": [ui_text]},
            "result": (result, json, "done")
        }
