import subprocess
import sys
import os
import pathlib

b=pathlib.Path(__file__).resolve().parent

vp=str(b/"Env"/("Scripts" if sys.platform=="win32" else "bin")/"python")


if not os.path.exists(vp):
    vp=sys.executable

def gse():
    e=os.environ.copy()
    if sys.platform.startswith("linux"):
        if "DISPLAY" not in e:
            e["DISPLAY"]=":0"
            
        # if "WAYLAND_DISPLAY" not in e:
        #     e["WAYLAND_DISPLAY"] = "wayland-0"
        if "XAUTHORITY" not in e:
            ru=e.get("SUDO_USER") or e.get("USER")
            if ru and ru!="root":
                e["XAUTHORITY"]=f"/home/{ru}/.Xauthority"
            else:
                e["XAUTHORITY"]=os.path.expanduser("~/.Xauthority")
    return e

def run_cli():
    print("Controls:")
    print("  CTRL + Click  - Capture screenshot")
    print("  CTRL + Enter  - Capture screenshot")
    print("  CTRL + Delete - Del Last Screenshot")
    print("  CTRL + Esc    - Done Recording")

    # print("press any key to start")

    re=gse()
    print("\nPhase 1 - Starting screenshot capture...\n")
    subprocess.call([vp,str(b/"app.py")],cwd=str(b),env=re)
    
    print("\nRecording complete!\n")
    
    t=input("Give a Title to your Guide: ").strip()
    if t=="":
        t="Untitled Guide"
    re["CUE_GUIDE_TITLE"]=t

    # notes=input("any notes? ")
    un=input("Enter custom instructions for AI (press Enter to skip): ").strip()
    re["CUE_USER_NOTES"]=un

    ic=input("Embed screenshots in the Markdown guide? [y/N]: ").strip().lower()
    
    if ic in ["y","yes","true","1"]:
        re["CUE_IMAGE_MODE"]="Yes"
    else:
        re["CUE_IMAGE_MODE"]="No"
    # re["CUE_IMAGE_MODE"] = "Yes"
    
    print("\nPhase 2 - Generating guide from screenshots...\n")
    subprocess.call([vp,str(b/"backend.py")],cwd=str(b),env=re)
    print(f"\nDone! Your guide is at Output/{t}/{t}.md\n")

def run_gui():
    re=gse()
    # subprocess.call([vp, str(b/"main.py")], cwd=str(b), env=re)
    subprocess.call([vp,str(b/"gui_app.py")],cwd=str(b),env=re)

if __name__=="__main__":
    md=sys.argv[1] if len(sys.argv)>1 else "cli"
    if md=="gui":
        run_gui()
    else:
        run_cli()