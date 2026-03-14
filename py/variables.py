# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import os
import json


VARS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input")
VARS_FILE = os.path.join(VARS_DIR, "vars.txt")


def load_vars():
    if os.path.exists(VARS_FILE):
        try:
            with open(VARS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_vars(data):
    os.makedirs(VARS_DIR, exist_ok=True)
    with open(VARS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def vars_summary():
    data = load_vars()
    if not data:
        return "(no variables saved)"
    return "\n".join(f"{k}: {v}" for k, v in data.items())


# ── SET ──────────────────────────────────────────────
class NumberVarSetNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "my_variable"}),
                "value": ("FLOAT", {"default": 0.0, "step": 0.01}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("FLOAT", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("FLOAT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("number", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, value, trigger=None, input=None):
        v = input if input is not None else value
        data = load_vars()
        data[variable_name] = v
        save_vars(data)
        json_result = json.dumps({"node": "NumberVarSetNode", "variable": variable_name, "value": v, "type": "number"})
        return {"ui": {"text": [vars_summary()]}, "result": (v, json_result, "done")}


# ── GET ──────────────────────────────────────────────
class NumberVarGetNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "my_variable"}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("FLOAT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("number", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, trigger=None):
        data = load_vars()
        value = data.get(variable_name, 0.0)
        json_result = json.dumps({"node": "NumberVarGetNode", "variable": variable_name, "value": value, "type": "number"})
        return {"ui": {"text": [vars_summary()]}, "result": (value, json_result, "done")}


# ── INCREMENT ────────────────────────────────────────
class NumberVarIncrementNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "my_variable"}),
                "amount": ("FLOAT", {"default": 1.0, "step": 0.01}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("FLOAT", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("FLOAT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("number", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, amount, trigger=None, input=None):
        data = load_vars()
        current = input if input is not None else data.get(variable_name, 0.0)
        new_value = current + amount
        data[variable_name] = new_value
        save_vars(data)
        json_result = json.dumps({"node": "NumberVarIncrementNode", "variable": variable_name, "value": new_value, "amount": amount, "type": "number"})
        return {"ui": {"text": [vars_summary()]}, "result": (new_value, json_result, "done")}


# ── DECREMENT ────────────────────────────────────────
class NumberVarDecrementNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "my_variable"}),
                "amount": ("FLOAT", {"default": 1.0, "step": 0.01}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("FLOAT", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("FLOAT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("number", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, amount, trigger=None, input=None):
        data = load_vars()
        current = input if input is not None else data.get(variable_name, 0.0)
        new_value = current - amount
        data[variable_name] = new_value
        save_vars(data)
        json_result = json.dumps({"node": "NumberVarDecrementNode", "variable": variable_name, "value": new_value, "amount": amount, "type": "number"})
        return {"ui": {"text": [vars_summary()]}, "result": (new_value, json_result, "done")}


# ── RESET ────────────────────────────────────────────
class NumberVarResetNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "my_variable"}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("FLOAT", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("number", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, trigger=None):
        data = load_vars()
        data[variable_name] = 0.0
        save_vars(data)
        json_result = json.dumps({"node": "NumberVarResetNode", "variable": variable_name, "value": 0.0, "type": "number"})
        return {"ui": {"text": [vars_summary()]}, "result": (0.0, json_result, "done")}


# ── STRING SET ────────────────────────────────────────
class StringVarSetNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "api_key"}),
                "value": ("STRING", {"default": ""}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
                "input": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("text", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, value, trigger=None, input=None):
        v = input if input is not None else value
        data = load_vars()
        data[variable_name] = v
        save_vars(data)
        masked = _masked_summary(load_vars())
        json_result = json.dumps({"node": "StringVarSetNode", "variable": variable_name, "value": v, "type": "string"})
        return {"ui": {"text": [masked]}, "result": (v, json_result, "done")}


# ── STRING GET ────────────────────────────────────────
class StringVarGetNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "api_key"}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("text", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, trigger=None):
        data = load_vars()
        value = data.get(variable_name, "")
        masked = _masked_summary(data)
        json_result = json.dumps({"node": "StringVarGetNode", "variable": variable_name, "value": value, "type": "string"})
        return {"ui": {"text": [masked]}, "result": (value, json_result, "done")}


# ── STRING DELETE ─────────────────────────────────────
class StringVarDeleteNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "variable_name": ("STRING", {"default": "api_key"}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("STRING", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("text", "json_result", "trigger")
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, variable_name, trigger=None):
        data = load_vars()
        removed = data.pop(variable_name, "")
        save_vars(data)
        json_result = json.dumps({"node": "StringVarDeleteNode", "variable": variable_name, "deleted_value": removed, "type": "string"})
        return {"ui": {"text": [vars_summary()]}, "result": (removed, json_result, "done")}


# ── helpers ──────────────────────────────────────────
def _masked_summary(data):
    """Mask string values that look like keys/secrets in the UI."""
    lines = []
    for k, v in data.items():
        if isinstance(v, str) and len(v) > 12:
            lines.append(f"{k}: {v[:4]}...{v[-4:]}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) if lines else "(no variables saved)"


NODE_CLASS_MAPPINGS = {
    "NumberVarSetNode": NumberVarSetNode,
    "NumberVarGetNode": NumberVarGetNode,
    "NumberVarIncrementNode": NumberVarIncrementNode,
    "NumberVarDecrementNode": NumberVarDecrementNode,
    "NumberVarResetNode": NumberVarResetNode,
    "StringVarSetNode": StringVarSetNode,
    "StringVarGetNode": StringVarGetNode,
    "StringVarDeleteNode": StringVarDeleteNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NumberVarSetNode": "Variable Set (Number)",
    "NumberVarGetNode": "Variable Get (Number)",
    "NumberVarIncrementNode": "Variable Increment (Number)",
    "NumberVarDecrementNode": "Variable Decrement (Number)",
    "NumberVarResetNode": "Variable Reset (Number)",
    "StringVarSetNode": "Variable Set (String)",
    "StringVarGetNode": "Variable Get (String)",
    "StringVarDeleteNode": "Variable Delete (String)",
}