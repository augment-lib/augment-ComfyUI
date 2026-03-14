# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

import json


class GateNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("*",),
            },
        }

    RETURN_TYPES = ("TRIGGER", "*", "STRING")
    RETURN_NAMES = ("trigger", "value", "json")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, input):
        json_result = json.dumps({"node": "Convert Any", "type": type(input).__name__, "value": str(input)})
        return {"ui": {"text": [str(input)]}, "result": ("done", input, json_result)}


WAIT_DEFAULTS = {
    "INT": {"default": 0},
    "FLOAT": {"default": 0.0, "step": 0.01},
    "STRING": {"default": ""},
    "BOOLEAN": {"default": False},
}


def make_wait_node(type_name, type_str):
    class WaitNode:
        @classmethod
        def INPUT_TYPES(cls):
            has_widget = type_str in WAIT_DEFAULTS
            inputs = {
                "required": {},
                "optional": {
                    "trigger": ("TRIGGER",),
                },
            }
            if has_widget:
                inputs["required"]["value"] = (type_str, WAIT_DEFAULTS[type_str])
                inputs["optional"]["input"] = (type_str, {"forceInput": True})
            else:
                inputs["required"]["value"] = (type_str,)
            return inputs

        RETURN_TYPES = (type_str, "AUGMENT_JSON", "TRIGGER")
        RETURN_NAMES = ("value", "json", "trigger")
        OUTPUT_NODE = True
        FUNCTION = "execute"
        CATEGORY = "Augment/Utils"

        @classmethod
        def VALIDATE_INPUTS(cls, **kwargs):
            return True

        def execute(self, value=None, trigger=None, input=None):
            v = input if input is not None else value
            json_result = json.dumps({"node": type_str, "type": type_str.lower(), "value": str(v)})
            return {"ui": {"text": [str(v)]}, "result": (v, json_result, "done")}

    WaitNode.__name__ = f"Wait{type_name}Node"
    WaitNode.__qualname__ = f"Wait{type_name}Node"
    return WaitNode


WAIT_TYPES = {
    "Int":        "INT",
    "Float":      "FLOAT",
    "String":     "STRING",
    "Bool":       "BOOLEAN",
    "Image":      "IMAGE",
    "Latent":     "LATENT",
    "Condition":  "CONDITIONING",
    "VAE":        "VAE",
    "Model":      "MODEL",
    "Clip":       "CLIP",
    "Mask":       "MASK",
}

NODE_CLASS_MAPPINGS = {"GateNode": GateNode}
NODE_DISPLAY_NAME_MAPPINGS = {"GateNode": "Trigger"}

for name, type_str in WAIT_TYPES.items():
    cls_name = f"Wait{name}Node"
    node_cls = make_wait_node(name, type_str)
    NODE_CLASS_MAPPINGS[cls_name] = node_cls
    NODE_DISPLAY_NAME_MAPPINGS[cls_name] = f"{name} (Improved)"
