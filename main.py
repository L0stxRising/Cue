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

def _needs_escalation():
    if sys.platform != "linux":
        return False
    if os.geteuid() == 0:
        return False
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

def _ensure_api_key():
    dotenv_path = BASE / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
    except ImportError:
        pass
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return
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
