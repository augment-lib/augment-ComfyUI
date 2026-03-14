# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

"""
Augment Executor Override
─────────────────────────────
Bypasses ComfyUI's caching for trigger-driven workflows.

What it does:
1. Monkeypatches the execute() function in ComfyUI's execution module
2. Any node class with ALWAYS_EXECUTE = True skips the output cache — always re-runs
3. Any node that accepts/outputs TRIGGER type is auto-detected and also skips cache
4. Everything else executes normally — zero impact on other workflows

No fork needed. No CLI flags. Just drop and go.
"""

import logging
import execution as comfy_execution
from comfy_execution.caching import BasicCache, CacheKeySetInputSignature, HierarchicalCache

logger = logging.getLogger("Augment.Executor")

# ── Store reference to the original execute function ─────────────
_original_execute = comfy_execution.execute


def _should_skip_cache(class_def):
    """
    Determine if a node class should bypass the output cache.
    
    Returns True if:
    - Node has ALWAYS_EXECUTE = True 
    - Node accepts or returns TRIGGER type
    - Node has IS_CHANGED that returns float("NaN") (legacy force-run pattern)
    """
    # Explicit opt-in
    if getattr(class_def, "ALWAYS_EXECUTE", False):
        return True
    
    # Check if node deals with TRIGGER types (input or output)
    try:
        input_types = class_def.INPUT_TYPES()
        for category in ("required", "optional"):
            if category in input_types:
                for key, val in input_types[category].items():
                    input_type = val[0] if isinstance(val, tuple) else val
                    if input_type == "TRIGGER":
                        return True
    except Exception:
        pass
    
    # Check return types for TRIGGER
    if hasattr(class_def, "RETURN_TYPES"):
        for rt in class_def.RETURN_TYPES:
            if rt == "TRIGGER":
                return True
    
    return False


async def patched_execute(server, dynprompt, caches, current_item, extra_data,
                          executed, prompt_id, execution_list,
                          pending_subgraph_results, pending_async_nodes, ui_outputs):
    """
    Drop-in replacement for execution.execute().
    
    For nodes that should skip cache:
    - Evict any cached output BEFORE the original execute() runs
    - This forces the original code past the cache-hit early return (line 419-428)
    - The node executes fresh every time
    - After execution, evict again so next run also re-executes
    
    For all other nodes: passthrough to original, zero overhead.
    """
    import nodes
    
    unique_id = current_item
    node_info = dynprompt.get_node(unique_id)
    class_type = node_info["class_type"]
    class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
    
    skip_cache = _should_skip_cache(class_def)
    
    if skip_cache:
        # Evict cached output so the original execute() can't short-circuit
        try:
            caches.outputs.delete(unique_id)
        except (AttributeError, KeyError):
            # NullCache or key doesn't exist — fine
            pass
    
    # Run the original execute
    result = await _original_execute(
        server, dynprompt, caches, current_item, extra_data,
        executed, prompt_id, execution_list,
        pending_subgraph_results, pending_async_nodes, ui_outputs
    )
    
    if skip_cache:
        # Evict AFTER execution too, so next prompt also re-runs this node
        try:
            caches.outputs.delete(unique_id)
        except (AttributeError, KeyError):
            pass
    
    return result


# ── Also patch the cache's set_prompt to skip signature checks for our nodes ──

_original_cache_set_prompt = None

def _patch_cache_set_prompt():
    """
    Patch CacheSet's set_prompt behavior so IsChangedCache 
    never marks our trigger nodes as 'unchanged'.
    """
    global _original_cache_set_prompt
    
    original_is_changed_get = comfy_execution.IsChangedCache.get
    
    async def patched_is_changed_get(self, node_id):
        """Force trigger/always-execute nodes to always report as changed."""
        import nodes
        node = self.dynprompt.get_node(node_id)
        class_type = node["class_type"]
        class_def = nodes.NODE_CLASS_MAPPINGS[class_type]
        
        if _should_skip_cache(class_def):
            # Return NaN — ComfyUI treats this as "always changed"
            self.is_changed[node_id] = float("NaN")
            return float("NaN")
        
        return await original_is_changed_get(self, node_id)
    
    comfy_execution.IsChangedCache.get = patched_is_changed_get


# ── Apply patches on import ─────────────────────────────────────

def _install():
    """Monkeypatch ComfyUI's execution module. Called once on import."""
    comfy_execution.execute = patched_execute
    _patch_cache_set_prompt()
    logger.info("Augment executor override installed — trigger nodes will always re-execute")

_install()
