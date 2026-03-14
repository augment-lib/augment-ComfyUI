"""
Augment - ComfyUI Custom Node Pack
Resilient loader: each node imports independently so one failure won't block the rest.
"""

import traceback

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
_failed = []


def _register(module_path, imports, mappings):
    """
    Try to import `imports` from `module_path` and register each into the global dicts.
    
    imports:  list of (ClassName,)  — names to import from the module
    mappings: dict of { "NodeID": ("ClassName", "Display Name") }
    """
    try:
        mod = __import__(module_path, fromlist=[c for c in imports])
    except Exception as e:
        for node_id, (cls_name, display) in mappings.items():
            _failed.append((node_id, e))
            print(f"[augment] ⚠ {node_id} unavailable: {e}")
        return

    for node_id, (cls_name, display) in mappings.items():
        cls = getattr(mod, cls_name, None)
        if cls is None:
            _failed.append((node_id, f"{cls_name} not found in {module_path}"))
            print(f"[augment] ⚠ {node_id} unavailable: {cls_name} not found in {module_path}")
            continue
        NODE_CLASS_MAPPINGS[node_id] = cls
        NODE_DISPLAY_NAME_MAPPINGS[node_id] = display


# ── Executor Override (must import first to patch ComfyUI) ──
try:
    __import__("custom_nodes.augment.py.executor")
except Exception as e:
    print(f"[augment] ⚠ Executor patch unavailable: {e}")

# ── Image Processing & Cropping ──
_register("custom_nodes.augment.py.face_crop", ["FaceCrop"], {
    "AugmentFaceCrop": ("FaceCrop", "Face Crop"),
})

_register("custom_nodes.augment.py.image_crop", ["ImageCrop"], {
    "AugmentImageCrop": ("ImageCrop", "Image Crop"),
})
_register("custom_nodes.augment.py.image_place", ["ImagePlaceNode"], {
    "AugmentImagePlace": ("ImagePlaceNode", "Image Place"),
})
_register("custom_nodes.augment.py.invert_image", ["InvertImageNode"], {
    "AugmentInvertImage": ("InvertImageNode", "Invert Image"),
})
_register("custom_nodes.augment.py.image_rotate", ["ImageRotateNode"], {
    "AugmentImageRotate": ("ImageRotateNode", "Image Rotate"),
})
_register("custom_nodes.augment.py.image_flip", ["ImageFlipNode"], {
    "AugmentImageFlip": ("ImageFlipNode", "Image Flip"),
})
_register("custom_nodes.augment.py.logo_mask", ["LogoMask"], {
    "AugmentLogoMask": ("LogoMask", "Logo Mask"),
})
_register("custom_nodes.augment.py.mask_bounding_box", ["MaskBoundingBox"], {
    "AugmentMaskBoundingBox": ("MaskBoundingBox", "Mask Bounding Box"),
})
# ── Grid & Construction Lines ──
_register("custom_nodes.augment.py.grid", ["GridGenerator"], {
    "AugmentGridGenerator": ("GridGenerator", "Grid Generator"),
})
_register("custom_nodes.augment.py.grid_coords", ["GridCoordsNode"], {
    "AugmentGridCoords": ("GridCoordsNode", "Grid Coords"),
})
_register("custom_nodes.augment.py.draw_line", ["LineDrawNode"], {
    "AugmentLineDraw": ("LineDrawNode", "Line Draw"),
})
_register("custom_nodes.augment.py.circle_draw", ["CircleDrawNode"], {
    "AugmentCircleDraw": ("CircleDrawNode", "Circle Draw"),
})
_register("custom_nodes.augment.py.fib", ["FibonacciSpiralNode"], {
    "AugmentFibonacciSpiral": ("FibonacciSpiralNode", "Fibonacci Spiral"),
})
_register("custom_nodes.augment.py.construction_lines", ["ConstructionLineOverlay"], {
    "AugmentConstructionLineOverlay": ("ConstructionLineOverlay", "Construction Line Overlay"),
})
_register("custom_nodes.augment.py.edge_detect", ["ShapeEdgeDetect"], {
    "AugmentShapeEdgeDetect": ("ShapeEdgeDetect", "Shape Edge Detect"),
})

# ── Color & Effects ──
_register("custom_nodes.augment.py.recolor", ["RecolorNode"], {
    "AugmentRecolor": ("RecolorNode", "Recolor (Mask)"),
})
_register("custom_nodes.augment.py.blur_average", ["BlurAverageNode"], {
    "AugmentBlurAverage": ("BlurAverageNode", "Blur Average (Dominant Color)"),
})

# ── Primitives ──
_register("custom_nodes.augment.py.prim_node", ["IntNode", "FloatNode", "StringNode", "BoolNode"], {
    "AugmentIntPrim": ("IntNode", "Int"),
    "AugmentFloatPrim": ("FloatNode", "Float"),
    "AugmentStringPrim": ("StringNode", "String"),
    "AugmentBoolPrim": ("BoolNode", "Bool"),
})

# ── Variables ──
_register("custom_nodes.augment.py.variables", [
    "NumberVarSetNode", "NumberVarGetNode", "NumberVarIncrementNode",
    "NumberVarDecrementNode", "NumberVarResetNode",
    "StringVarSetNode", "StringVarGetNode", "StringVarDeleteNode",
], {
    "AugmentNumberVarSet": ("NumberVarSetNode", "Variable Set (Number)"),
    "AugmentNumberVarGet": ("NumberVarGetNode", "Variable Get (Number)"),
    "AugmentNumberVarIncrement": ("NumberVarIncrementNode", "Variable Increment (Number)"),
    "AugmentNumberVarDecrement": ("NumberVarDecrementNode", "Variable Decrement (Number)"),
    "AugmentNumberVarReset": ("NumberVarResetNode", "Variable Reset (Number)"),
    "AugmentStringVarSet": ("StringVarSetNode", "Variable Set (String)"),
    "AugmentStringVarGet": ("StringVarGetNode", "Variable Get (String)"),
    "AugmentStringVarDelete": ("StringVarDeleteNode", "Variable Delete (String)"),
})

# ── Flow Control ──
try:
    from .py.trigger import make_wait_node, WAIT_TYPES
    for _name, _type_str in WAIT_TYPES.items():
        _cls_name = f"AugmentWait{_name}"
        try:
            NODE_CLASS_MAPPINGS[_cls_name] = make_wait_node(_name, _type_str)
            NODE_DISPLAY_NAME_MAPPINGS[_cls_name] = f"{_name} (Improved)"
        except Exception as e:
            _failed.append((_cls_name, e))
            print(f"[augment] ⚠ {_cls_name} unavailable: {e}")
except Exception as e:
    _failed.append(("Wait nodes", e))
    print(f"[augment] ⚠ Flow control nodes unavailable: {e}")


# PAID

_register("custom_nodes.augment.py.svg_tools", ["AugmentSVGToPNG", "AugmentPNGToSVG"], {
    "AugmentSVGToPNG": ("AugmentSVGToPNG", "Augment SVG to PNG"),
    "AugmentPNGToSVG": ("AugmentPNGToSVG", "Augment PNG to SVG"),
})

# ── Crypto & Utilities ──
_register("custom_nodes.augment.py.crypto", ["SHA256Node", "RandomNumberNode", "UUIDNode"], {
    "AugmentSHA256": ("SHA256Node", "SHA-256 Hash"),
    "AugmentRandomNumber": ("RandomNumberNode", "Random Number"),
    "AugmentUUID": ("UUIDNode", "UUID Generator"),
})
_register("custom_nodes.augment.py.json_viewer", ["JsonViewerNode"], {
    "AugmentJsonViewer": ("JsonViewerNode", "JSON Viewer"),
})

_register("custom_nodes.augment.py.json_extract", ["JsonExtractNode"], {
    "AugmentJsonExtract": ("JsonExtractNode", "JSON Extract"),
})

# ── Preview & Save ──
_register("custom_nodes.augment.py.preview", ["AugmentPreviewImage", "AugmentSaveImage", "AugmentPreviewAny"], {
    "AugmentPreviewImage": ("AugmentPreviewImage", "Preview Image"),
    "AugmentSaveImage": ("AugmentSaveImage", "Save Image (Improved)"),
    "AugmentPreviewAny": ("AugmentPreviewAny", "Preview Any"),
})

_register("custom_nodes.augment.py.load_image", ["AugmentLoadImage"], {
    "AugmentLoadImage": ("AugmentLoadImage", "Load Image (Improved)"),
})

_register("custom_nodes.augment.py.switch", ["SwitchNode"], {
    "AugmentSwitchNode": ("SwitchNode", "Switch Improved"),
})

# ── Summary ──
WEB_DIRECTORY = "./web/js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

if _failed:
    print(f"[augment] ✓ Registered {len(NODE_CLASS_MAPPINGS)} nodes ({len(_failed)} failed)")
    for node_id, err in _failed:
        print(f"[augment]   ✗ {node_id}: {err}")
else:
    print(f"[augment] ✓ Registered {len(NODE_CLASS_MAPPINGS)} nodes")
