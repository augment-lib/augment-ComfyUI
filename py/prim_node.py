# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json


class IntNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("INT", {"default": 0}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("INT", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("INT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("value", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, value, trigger=None, input=None):
        result = input if input is not None else value
        json_result = json.dumps({"node": "IntNode", "value": result, "type": "int"})
        return (result, json_result, "done")


class FloatNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {"default": 0.0, "step": 0.01}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("FLOAT", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("FLOAT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("value", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, value, trigger=None, input=None):
        result = input if input is not None else value
        json_result = json.dumps({"node": "FloatNode", "value": result, "type": "float"})
        return (result, json_result, "done")


class StringNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("STRING", {"default": ""}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("value", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, value, trigger=None, input=None):
        result = input if input is not None else value
        json_result = json.dumps({"node": "StringNode", "value": result, "type": "string"})
        return (result, json_result, "done")


class BoolNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("BOOLEAN", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("value", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, value, trigger=None, input=None):
        result = input if input is not None else value
        json_result = json.dumps({"node": "BoolNode", "value": result, "type": "boolean"})
        return (result, json_result, "done")


NODE_CLASS_MAPPINGS = {
    "IntPrimNode": IntNode,
    "FloatPrimNode": FloatNode,
    "StringPrimNode": StringNode,
    "BoolPrimNode": BoolNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IntPrimNode": "Int",
    "FloatPrimNode": "Float",
    "StringPrimNode": "String",
    "BoolPrimNode": "Bool",
}