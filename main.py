"""
Cue — Single entry point for PyInstaller packaging.
Dispatches to capture (app.py), generate (backend.py), or GUI (gui_app.py).
"""
import sys
import os
import pathlib
import subprocess
import shutil

if getattr(sys, "frozen", False):
    BASE = pathlib.Path(sys.executable).resolve().parent
else:
    BASE = pathlib.Path(__file__).resolve().parent


TARGET_FOLDER = BASE / "tmp"
OUTPUT_FOLDER = BASE / "Output"

try:
    TARGET_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    print(f"Folder ready at: {TARGET_FOLDER}")
    print(f"Folder ready at: {OUTPUT_FOLDER}")
except PermissionError:
    print(f"[Error] Permission denied when trying to create folder at {TARGET_FOLDER}.")
    print("Make sure the executable is placed in a directory where the user has write permissions (e.g., Desktop or Documents, NOT Program Files).")


# ── Privilege escalation (Linux only) ─────────────────────────────────
# Global input capture via evdev requires root on Wayland.
# Re-launch via pkexec with display env vars forwarded.
def _needs_escalation():
    if sys.platform != "linux":
        return False
    if os.geteuid() == 0:
        return False
    # Only escalate for the main GUI / capture, not --generate
    if "--generate" in sys.argv:
        return False
    return True

def _escalate():
    pkexec = shutil.which("pkexec")
    if not pkexec:
        print("[Warning] pkexec not found — running without root. Global hotkeys may not work on Wayland.")
        return False
    exe = sys.executable if not getattr(sys, "frozen", False) else sys.argv[0]
    exe = os.path.abspath(exe)
    # Forward display environment variables so the GUI & screenshots work under root
    env_vars = []
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR",
                "XAUTHORITY", "XDG_CURRENT_DESKTOP", "DBUS_SESSION_BUS_ADDRESS",
                "HOME", "LANG"):
        val = os.environ.get(key)
        if val:
            env_vars.append(f"{key}={val}")
    user = os.environ.get("USER", "")
    env_vars.append(f"SUDO_USER={user}")
    cmd = [pkexec, "env"] + env_vars + [exe] + sys.argv[1:]
    os.execvp(pkexec, cmd)

# ── API key check ─────────────────────────────────────────────────────
def _ensure_api_key():
    dotenv_path = BASE / ".env"
    # Try loading existing .env
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
    except ImportError:
        pass
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return
    # Show tkinter dialog for API key
    try:
        import tkinter as tk
        from tkinter import simpledialog, messagebox
        root = tk.Tk()
        root.withdraw()
        key = simpledialog.askstring("Cue — API Key Required",
                                     "Enter your OpenRouter API key:",
                                     parent=root)
        root.destroy()
        if not key or not key.strip():
            print("No API key provided. Exiting.")
            sys.exit(1)
        key = key.strip()
        os.environ["OPENROUTER_API_KEY"] = key
        with open(dotenv_path, "w") as f:
            f.write(f"OPENROUTER_API_KEY={key}\n")
        print(f"API key saved to {dotenv_path}")
    except Exception as e:
        print(f"Could not show API key dialog: {e}")
        sys.exit(1)

# ── Dispatch ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    if _needs_escalation():
        _escalate()

    _ensure_api_key()

    if "--capture" in sys.argv:
        from app import main as capture_main
        import asyncio
        try:
            asyncio.run(capture_main())
        except KeyboardInterrupt:
            pass
    elif "--generate" in sys.argv:
        from backend import main as generate_main
        generate_main()
    else:
        from gui_app import CueApp
        CueApp().mainloop()
