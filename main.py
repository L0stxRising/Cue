import sys
import os
import pathlib
import subprocess
import shutil
# import time

if getattr(sys, "frozen", False) == True:
    BASE = pathlib.Path(sys.executable).resolve().parent
else:
    BASE = pathlib.Path(__file__).resolve().parent


tf = BASE / "tmp"
of = BASE / "Output"

try:
    tf.mkdir(parents=True, exist_ok=True)
    of.mkdir(parents=True, exist_ok=True)
    
    print(f"Folder ready at: {tf}")
    print(f"Folder ready at: {of}")
except PermissionError:
    print(f"Permission denied when trying to create folder at {tf}.")
    
    print("Make sure the the user has write permissions.")


# def check_root():
#     return os.geteuid() == 0

def _needs_escalation():
    if sys.platform != "linux":
        return False
    
    if os.geteuid() == 0:
        return False
    if "--generate" in sys.argv:
        return False
    return True

def _escalate():
    pk = shutil.which("pkexec")
    if pk is None:
        return False

    if getattr(sys,  "frozen",  False) == True:
        ex = sys.argv[0]
    else:
        ex = sys.executable
    ex = os.path.abspath(ex)

    ev = []
    for k in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR",
                "XAUTHORITY", "XDG_CURRENT_DESKTOP", "DBUS_SESSION_BUS_ADDRESS",
                "HOME",  "LANG"):
        v = os.environ.get(k)
        if v:
            ev.append(f"{k}={v}")

    u = os.environ.get("USER", "")
    ev.append(f"SUDO_USER={u}")

    # cmd = [pk, "env"] + ev + [ex, "--gui"]
    cmd = [pk, "env"] + ev + [ex] + sys.argv[1:]
    os.execvp(pk,  cmd)

def _ensure_api_key():
    dp = BASE / ".env"

    try:
        from dotenv import load_dotenv
        load_dotenv(dp)
    except ImportError:
        pass

    k = os.environ.get("OPENROUTER_API_KEY",  "").strip()
    if len(k) > 0:
        return

    try:
        import tkinter as tk
        from tkinter import simpledialog,  messagebox
        rt = tk.Tk()
        rt.withdraw()
        k = simpledialog.askstring("Cue — API Key Required",
                                     "Enter your OpenRouter API key:",
                                     parent=rt)
        
        rt.destroy()
        if not k or k.strip() == "":
            print("No API key provided. Exiting.")
            sys.exit(1)
        k = k.strip()
        os.environ["OPENROUTER_API_KEY"] = k

        # print("Api key checked!!!")
        f = open(dp,  "w")
        f.write(f"OPENROUTER_API_KEY={k}\n")
        f.close()
        print(f"API key saved to {dp}")
    except Exception as e:
        print(f"Could not show API key dialog: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if _needs_escalation():
        _escalate()
    # else:
    #     None
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