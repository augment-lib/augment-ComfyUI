# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

from comfy_execution.graph_utils import ExecutionBlocker


class SwitchNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("BOOLEAN", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("TRIGGER", "TRIGGER", "TRIGGER")
    RETURN_NAMES = ("on_true", "on_false", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Augment/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, input):
        on_true = "done" if input else ExecutionBlocker(None)
        on_false = ExecutionBlocker(None) if input else "done"
        ui_text = f"Input: {input}\nPath: {'on_true' if input else 'on_false'}"
        return {"ui": {"text": [ui_text]}, "result": (on_true, on_false, "done")}
