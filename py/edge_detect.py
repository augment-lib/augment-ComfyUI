# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

from .utils import compute_smart_edges
import json


class ShapeEdgeDetect:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
            },
            "optional": {
                "symmetry_threshold": ("FLOAT", {"default": 0.85, "min": 0.5, "max": 0.99, "step": 0.05}),
            },
        }

    RETURN_TYPES = ("EDGE_DATA", "AUGMENT_JSON", "TRIGGER")
    RETURN_NAMES = ("edges", "json_result", "trigger")
    FUNCTION = "detect"
    CATEGORY = "Augment/Grid"

    def detect(self, mask, symmetry_threshold=0.85):
        m = mask[0].cpu().numpy()
        edges = compute_smart_edges(m, symmetry_threshold)
        
        h_count = len(edges["h_lines"])
        v_count = len(edges["v_lines"])
        d45_count = len(edges["d45_lines"])
        d135_count = len(edges["d135_lines"])
        
        print(f"[augment] edges: {h_count}H / {v_count}V / {d45_count}d45 / {d135_count}d135")
        
        json_result = json.dumps({
            "node": "ShapeEdgeDetect",
            "h_lines": h_count,
            "v_lines": v_count,
            "d45_lines": d45_count,
            "d135_lines": d135_count,
        })
        
        return (edges, json_result, "done")