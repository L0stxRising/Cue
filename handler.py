import subprocess
import sys
import os
import pathlib

base_dir = pathlib.Path(__file__).resolve().parent

if sys.platform == "win32":
    python_bin = str(base_dir / "Env" / "Scripts" / "python.exe")
else:
    python_bin = str(base_dir / "Env" / "bin" / "python")
if not os.path.exists(python_bin):
    python_bin = sys.executable


def setup_env():
    env = os.environ.copy()

    if sys.platform.startswith("linux"):
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        if "XAUTHORITY" not in env:
            user = env.get("SUDO_USER") or env.get("USER")
            if user and user != "root":
                env["XAUTHORITY"] = f"/home/{user}/.Xauthority"
            else:
                env["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")

    return env


def run_cli():
    print("Controls:")
    print("  CTRL + Click  - Capture screenshot")
    print("  CTRL + Enter  - Capture screenshot")
    print("  CTRL + Delete - Del Last Screenshot")
    print("  CTRL + Esc    - Done Recording")
    env = setup_env()
    print("\nPhase 1 - Starting screenshot capture...\n")

    subprocess.call([python_bin, str(base_dir / "app.py")], cwd=str(base_dir), env=env)

    print("\nRecording complete!\n")

    title = input("Give a Title to your Guide: ").strip()
    if not title:
        title = "Untitled Guide"
    env["CUE_GUIDE_TITLE"] = title

    # notes = input("any notes? ")
    notes = input("Enter custom instructions for AI (press Enter to skip): ").strip()
    env["CUE_USER_NOTES"] = notes

    choice = input("Embed screenshots in the Markdown guide? [y/N]: ").strip().lower()
    if choice in ["y", "yes", "true", "1"]:
        env["CUE_IMAGE_MODE"] = "Yes"
    else:
        env["CUE_IMAGE_MODE"] = "No"
    print("\nPhase 2 - Generating guide from screenshots...\n")
    subprocess.call([python_bin, str(base_dir / "backend.py")], cwd=str(base_dir), env=env)

    print(f"\nDone! Your guide is at Output/{title}/{title}.md\n")


def run_gui():
    env = setup_env()
    subprocess.call([python_bin, str(base_dir / "gui_app.py")], cwd=str(base_dir), env=env)


if __name__ == "__main__":
    mode = "cli"
    if len(sys.argv) > 1:
        mode = sys.argv[1].strip()

    if mode == "gui":
        run_gui()
    else:
        run_cli()
