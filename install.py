"""
Auto-install dependencies for Augment nodes.
ComfyUI will run this automatically when the node pack is loaded.
"""

import subprocess
import sys
import os

def install():
    """Install required packages."""
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(requirements_path):
        print("[augment] No requirements.txt found, skipping dependency install")
        return
    
    print("[augment] Checking dependencies...")
    
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path, "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        print("[augment] ✓ Dependencies installed/verified")
    except subprocess.CalledProcessError as e:
        print(f"[augment] ⚠ Warning: Could not install dependencies: {e}")
        print("[augment] Please manually run: pip install -r requirements.txt")

if __name__ == "__main__":
    install()
