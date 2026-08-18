import subprocess
import sys
import os
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
VENV_PYTHON = str(BASE / "Env" / ("Scripts" if sys.platform == "win32" else "bin") / "python")

if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

# idk some Random Colors I chose 
C = "\033[36m"
B = "\033[34m"
M = "\033[35m"
G = "\033[32m"
Y = "\033[33m"
W = "\033[1;37m"
D = "\033[2m"
N = "\033[0m"

# Fricking Linux Hacks
def get_safe_env():
    env = os.environ.copy()
    if sys.platform.startswith("linux"):
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        if "XAUTHORITY" not in env:
            real_user = env.get("SUDO_USER") or env.get("USER")
            if real_user and real_user != "root":
                env["XAUTHORITY"] = f"/home/{real_user}/.Xauthority"
            else:
                env["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")
    return env


def run_cli():
    """CLI mode: run app.py then backend.py in the terminal."""
    print(f"{B}┌──────────────────────────────────────┐{N}")
    print(f"{B}│{N}  {C}CTRL + Click {N} → Capture screenshot  {B}│{N}")
    print(f"{B}│{N}  {C}CTRL + Enter {N} → Capture screenshot  {B}│{N}")
    print(f"{B}│{N}  {C}CTRL + Delete{N} → Del Last Screenshot {B}│{N}")
    print(f"{B}│{N}  {M}CTRL + Esc{N} → {Y}Done Recording{N}    {B}     │{N}")
    print(f"{B}└──────────────────────────────────────┘{N}")
    run_env = get_safe_env()

    print(f"\n{G}⏺{N}  {W}Phase 1{N} — Starting screenshot capture...\n")
    subprocess.call([VENV_PYTHON, str(BASE / "app.py")], cwd=str(BASE), env=run_env)

    print(f"\n{G}✓{N}  Recording complete!")
    title = input(f"{Y}⟩{N} Give a Title to your Guide: ").strip() or "Untitled Guide"
    run_env["CUE_GUIDE_TITLE"] = title

    print(f"\n{M}⚡{N} {W}Phase 2{N} — Generating guide from screenshots...\n")
    subprocess.call([VENV_PYTHON, str(BASE / "backend.py")], cwd=str(BASE), env=run_env)
    print(f"\n{G}✓{N}  Done! Your guide is at {C}Output/{title}.md{N}\n")


def run_gui():
    run_env = get_safe_env()
    subprocess.call([VENV_PYTHON, str(BASE / "gui_app.py")], cwd=str(BASE), env=run_env)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "cli"
    if mode == "gui":
        run_gui()
    else:
        run_cli()