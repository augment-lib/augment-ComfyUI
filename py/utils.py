# "Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
# Augmentstudio.app

"""
Smart shape-edge detection for construction lines.
Extracts meaningful structural lines, not boundary noise.
"""
import numpy as np

try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def compute_all_edges(mask_2d, edge_min=None, merge_tol=None):
    """
    Main entry point — replaces the old boundary-tracing approach.
    edge_min and merge_tol are kept for API compatibility but ignored.
    """
    return compute_smart_edges(mask_2d)


def compute_smart_edges(mask, symmetry_threshold=0.85):
    """
    Extract meaningful construction lines from a mask.
    Returns structural lines, not boundary noise.
    """
    binary = (mask > 0.5).astype(np.uint8)
    
    if binary.sum() == 0:
        return {
            "h_lines": [],
            "v_lines": [],
            "d45_lines": [],
            "d135_lines": [],
        }
    
    ys, xs = np.where(binary)
    
    # === BOUNDING BOX ===
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    
    bbox_w = x_max - x_min
    bbox_h = y_max - y_min
    
    # === CENTERS ===
    center_x = (x_min + x_max) // 2
    center_y = (y_min + y_max) // 2
    
    # === CENTER OF MASS ===
    if HAS_SCIPY:
        com_y, com_x = ndimage.center_of_mass(binary)
        com_x, com_y = int(com_x), int(com_y)
    else:
        com_x, com_y = center_x, center_y
    
    # === BUILD LINES ===
    h_lines = [y_min, y_max]
    v_lines = [x_min, x_max]
    
    # Add geometric center
    if bbox_h > 20:
        h_lines.append(center_y)
    if bbox_w > 20:
        v_lines.append(center_x)
    
    # Add center of mass if different from geometric center
    if bbox_h > 40 and abs(com_y - center_y) > bbox_h * 0.05:
        h_lines.append(com_y)
    if bbox_w > 40 and abs(com_x - center_x) > bbox_w * 0.05:
        v_lines.append(com_x)
    
    # === DENSITY-BASED DIVISIONS ===
    # Find where the shape has significant internal gaps
    h_divisions = _find_density_divisions(binary, axis='horizontal', min_gap=max(8, bbox_h // 20))
    v_divisions = _find_density_divisions(binary, axis='vertical', min_gap=max(8, bbox_w // 20))
    
    for y in h_divisions:
        if y not in h_lines and y_min < y < y_max:
            h_lines.append(y)
    
    for x in v_divisions:
        if x not in v_lines and x_min < x < x_max:
            v_lines.append(x)
    
    # === DIAGONALS (only for symmetric shapes) ===
    d45_lines = []
    d135_lines = []
    
    if _is_roughly_square(bbox_w, bbox_h, tolerance=0.25):
        # Check for diagonal symmetry
        crop = binary[y_min:y_max+1, x_min:x_max+1]
        
        d45_score = _diagonal_symmetry_score(crop, axis='d45')
        d135_score = _diagonal_symmetry_score(crop, axis='d135')
        
        if d45_score > symmetry_threshold:
            d45_lines.append(center_x - center_y)
        
        if d135_score > symmetry_threshold:
            d135_lines.append(center_x + center_y)
    
    # === CORNER DIAGONALS (useful for any shape) ===
    # Lines from bbox corners through center
    if bbox_w > 50 and bbox_h > 50:
        # Only add if the shape has significant diagonal extent
        diag_coverage_45 = _check_diagonal_coverage(binary, x_min, y_min, x_max, y_max, direction=45)
        diag_coverage_135 = _check_diagonal_coverage(binary, x_min, y_min, x_max, y_max, direction=135)
        
        if diag_coverage_45 > 0.3:
            d45_lines.append(x_min - y_min)  # top-left to bottom-right
            d45_lines.append(x_max - y_max)  # if different
        
        if diag_coverage_135 > 0.3:
            d135_lines.append(x_min + y_max)  # bottom-left to top-right
            d135_lines.append(x_max + y_min)  # if different
    
    # === CLEANUP ===
    h_lines = sorted(set(h_lines))
    v_lines = sorted(set(v_lines))
    d45_lines = sorted(set(d45_lines))
    d135_lines = sorted(set(d135_lines))
    
    # Merge lines that are too close
    h_lines = _merge_close(h_lines, min_dist=max(5, bbox_h // 30))
    v_lines = _merge_close(v_lines, min_dist=max(5, bbox_w // 30))
    d45_lines = _merge_close(d45_lines, min_dist=10)
    d135_lines = _merge_close(d135_lines, min_dist=10)
    
    return {
        "h_lines": h_lines,
        "v_lines": v_lines,
        "d45_lines": d45_lines,
        "d135_lines": d135_lines,
    }


def _find_density_divisions(binary, axis='horizontal', min_gap=8):
    """
    Find lines where pixel density drops significantly.
    These indicate structural divisions (baselines, gaps between elements, etc.)
    """
    divisions = []
    
    if axis == 'horizontal':
        density = binary.sum(axis=1).astype(float)
    else:
        density = binary.sum(axis=0).astype(float)
    
    if len(density) < 10:
        return divisions
    
    max_d = density.max()
    if max_d == 0:
        return divisions
    
    density = density / max_d
    
    # Find valleys (low density regions)
    threshold = 0.15
    in_gap = False
    gap_start = 0
    
    for i, d in enumerate(density):
        if d < threshold and not in_gap:
            in_gap = True
            gap_start = i
        elif d >= threshold and in_gap:
            in_gap = False
            gap_size = i - gap_start
            if gap_size >= min_gap:
                divisions.append(gap_start + gap_size // 2)
    
    return divisions


def _diagonal_symmetry_score(binary, axis='d45'):
    """Check how symmetric a shape is along a diagonal."""
    h, w = binary.shape
    if h != w:
        # Pad to square for comparison
        size = max(h, w)
        padded = np.zeros((size, size), dtype=binary.dtype)
        padded[:h, :w] = binary
        binary = padded
    
    if axis == 'd45':
        flipped = binary.T
    else:  # d135
        flipped = np.flipud(np.fliplr(binary)).T
    
    intersection = np.logical_and(binary, flipped).sum()
    union = np.logical_or(binary, flipped).sum()
    
    if union == 0:
        return 0.0
    
    return intersection / union


def _is_roughly_square(w, h, tolerance=0.25):
    """Check if aspect ratio is close to 1:1"""
    if w == 0 or h == 0:
        return False
    ratio = min(w, h) / max(w, h)
    return ratio > (1 - tolerance)


def _check_diagonal_coverage(binary, x_min, y_min, x_max, y_max, direction=45):
    """
    Check what fraction of a diagonal line through the bbox is covered by the shape.
    """
    samples = 20
    hits = 0
    
    for i in range(samples):
        t = i / (samples - 1)
        
        if direction == 45:
            x = int(x_min + t * (x_max - x_min))
            y = int(y_min + t * (y_max - y_min))
        else:  # 135
            x = int(x_min + t * (x_max - x_min))
            y = int(y_max - t * (y_max - y_min))
        
        if 0 <= y < binary.shape[0] and 0 <= x < binary.shape[1]:
            if binary[y, x]:
                hits += 1
    
    return hits / samples


def _merge_close(lines, min_dist=5):
    """Merge lines that are within min_dist of each other."""
    if len(lines) <= 1:
        return lines
    
    result = [lines[0]]
    for line in lines[1:]:
        if line - result[-1] >= min_dist:
            result.append(line)
        else:
            # Keep the average? Or just skip? Let's keep first.
            pass
    
    return result


# === LEGACY API (kept for compatibility) ===

def build_alpha_grid(mask_2d):
    return (mask_2d > 0).astype(np.uint8)