import sys
import os
import asyncio
import time
import subprocess
import glob
from pathlib import Path
# import pyautogui
# import threading

try:
    from evdev import InputDevice,list_devices,ecodes
    hev=True
except ImportError:
    hev=False
    
try:
    from pynput import mouse as pm
    from pynput import keyboard as pk
    hasPyn=True
except ImportError:
    hasPyn=False

try:
    import pwd
except ImportError:
    pwd=None

st={"mc":False,"ctrl":False,"ks":False,"ent":False,"dl":False}

# cnt = 0

base_dir=Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent
tmp_dir=os.path.join(base_dir,"tmp")

if os.path.exists(tmp_dir):
    for f in os.listdir(tmp_dir):
        fp=os.path.join(tmp_dir,f)
        if os.path.isfile(fp):
            try:
                os.unlink(fp)
            except OSError:
                pass


def getDevices():
    if not hev:
        print("Evdev is not available.")
        return [],[]

    mice=[]
    kboard=[]
    for path in list_devices():
        try:
            device=InputDevice(path)
        except Exception:
            continue
        caps=device.capabilities()
        if ecodes.EV_KEY in caps:
            kc=caps[ecodes.EV_KEY]
            if ecodes.BTN_LEFT in kc:
                mice.append(device)
            elif ecodes.KEY_A in kc:
                kboard.append(device)
    return mice,kboard


if hasPyn:
    def opr(key):
        global st
        if key in(pk.Key.ctrl_l,pk.Key.ctrl_r):
            st["ctrl"]=True
        elif key==pk.Key.enter:
            st["ent"]=True
        elif key==pk.Key.esc:
            st["ks"]=True
        elif key==pk.Key.delete:
            st["dl"]=True

    def orl(key):
        global st
        if key in(pk.Key.ctrl_l,pk.Key.ctrl_r):
            st["ctrl"]=False
        elif key==pk.Key.enter:
            st["ent"]=False
        elif key==pk.Key.esc:
            st["ks"]=False
        elif key==pk.Key.delete:
            st["dl"]=False

    def ocl(x,y,button,pressed):
        global st
        if button==pm.Button.left:
            st["mc"]=pressed


async def ListenM(mouse):
    try:
        async for ev in mouse.async_read_loop():
            if ev.type==ecodes.EV_KEY and ev.code==ecodes.BTN_LEFT:
                st["mc"]=(ev.value==1 or ev.value==2)
                
            await asyncio.sleep(0)
        
    except asyncio.CancelledError:
        pass


async def ListenK(kboard):
    try:
        async for ev in kboard.async_read_loop():
            if ev.type==ecodes.EV_KEY:
                v=(ev.value==1 or ev.value==2)
                if ev.code in(ecodes.KEY_LEFTCTRL,ecodes.KEY_RIGHTCTRL):
                    st["ctrl"]=v
                elif ev.code==ecodes.KEY_ENTER:
                    st["ent"]=v
                elif ev.code==ecodes.KEY_ESC:
                    st["ks"]=v
                elif ev.code==ecodes.KEY_DELETE:
                    st["dl"]=v
                
            await asyncio.sleep(0)
    
    except asyncio.CancelledError:
        pass

# async def check_mouse_pos():
#     while True:
#         await asyncio.sleep(1)


async def chk(kl):
    global st
    while not kl.is_set():
        if (st["mc"] or st["ent"]) and st["ctrl"]:
            print("Activation")
            take_sc(os.path.join(tmp_dir,f"{time.time()}.png"))
            st["mc"]=False
            st["ent"]=False
            
        if st["dl"] and st["ctrl"]:
            scs=[f for f in glob.glob(os.path.join(tmp_dir,"*")) if os.path.isfile(f)]
            if scs:
                lt=max(scs,key=os.path.getmtime)
                try:
                    os.remove(lt)
                    print("Deleted Last ScreenShot!")
                except Exception as e:
                    print(f"Failed deleting screenshot: {e}")
            st["dl"]=False
            
        if st["ks"] and st["ctrl"]:
            print("Recording Done! Saved the ScreenShots.")
            kl.set()
            break
            
        await asyncio.sleep(0.005)

# THIS function was Made my AI help
def take_sc(output_path="screenshot.png"):
    abs_path=os.path.abspath(output_path)
    is_root=hasattr(os,'geteuid') and os.geteuid()==0
    real_user=os.environ.get("SUDO_USER") or os.environ.get("USER")
    uid="1000"
    
    if pwd and real_user:
        try:
            uid=str(pwd.getpwnam(real_user).pw_uid)
        except KeyError:
            uid="1000"

    ws=f"/run/user/{uid}/wayland-0"
    is_w="WAYLAND_DISPLAY" in os.environ or os.path.exists(ws)
    w_d=os.environ.get("WAYLAND_DISPLAY","wayland-0")

    # if sys.platform == "win32":
    #     import mss
    #     with mss.mss() as sct:
    #         sct.shot(output=abs_path)
    #     return True

    if sys.platform.startswith("linux") and is_w:
        cpx=[]
        re=os.environ.copy()
        if is_root:
            re["XDG_RUNTIME_DIR"]=f"/run/user/{uid}"
            re["DBUS_SESSION_BUS_ADDRESS"]=f"unix:path=/run/user/{uid}/bus"
            re["WAYLAND_DISPLAY"]=w_d
            cpx=["sudo","-u",real_user,"env",
                 f"XDG_RUNTIME_DIR=/run/user/{uid}",
                 f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
                 f"WAYLAND_DISPLAY={w_d}"]
        
        dk=os.environ.get("XDG_CURRENT_DESKTOP","GNOME").lower()
        try:
            if "gnome" in dk or "unity" in dk:
                cm=cpx+["gnome-screenshot","-p","-f",abs_path]
            elif "kde" in dk:
                cm=cpx+["spectacle","-b","-n","-o",abs_path]
            elif any(e in dk for e in ["sway","hyprland","wlroots"]):
                cm=cpx+["grim",abs_path]
            else:
                cm=cpx+["gnome-screenshot","-p","-f",abs_path]
                
            os.makedirs(tmp_dir,exist_ok=True)
            subprocess.run(cm,env=re,check=True)
            print(f"Wayland screenshot saved -> {abs_path}")
        except subprocess.CalledProcessError as e:
            print(f"Wayland screenshot failed: {e}")
            return False
        
    else:
        try:
            import mss
            from PIL import Image,ImageDraw
            with mss.mss() as sct:
                monitor=sct.monitors[0]
                si=sct.grab(monitor)
                img=Image.frombytes("RGB",si.size,si.bgra,"raw","BGRX")
                mx,my=0,0
                
                if hasPyn:
                    ctrl=pm.Controller()
                    mx,my=ctrl.position
                    
                dr=ImageDraw.Draw(img)
                r=8
                # dr.rectangle((mx-r, my-r, mx+r, my+r), fill="blue")
                dr.ellipse((mx-r,my-r,mx+r,my+r),fill="red",outline="white")
                img.save(abs_path)
                
            print(f"Standard screenshot saved -> {abs_path}")
        except ImportError:
            print("[Error] Missing libraries! Run: pip install mss Pillow pynput")
            return False

    if is_root and os.path.exists(abs_path) and pwd:
        try:
            ui=pwd.getpwnam(real_user)
            os.chown(abs_path,ui.pw_uid,ui.pw_gid)
        except(KeyError,AttributeError,OSError):
            pass
            
    return True


async def main():
    m,k=getDevices()
    kl=asyncio.Event()
    lt=[]
    ml=None
    kl_l=None
    
    if m and k:
        print("Started Listening For Activation (Linux)")
        for dv in m:
            lt.append(asyncio.create_task(ListenM(dv)))
        for dv in k:
            lt.append(asyncio.create_task(ListenK(dv)))
    elif hasPyn:
        print("Started Listening For Activation (Windows/Mac/Xorg)")
        ml=pm.Listener(on_click=ocl)
        kl_l=pk.Listener(on_press=opr,on_release=orl)
        ml.start()
        kl_l.start()
    else:
        print("No devices found. Exiting.")
        sys.exit(1)
        
    await chk(kl)
    print("Stopping input listeners...")
    
    if lt:
        for t in lt:
            t.cancel()
        await asyncio.gather(*lt,return_exceptions=True)
        
    if ml:
        ml.stop()
    if kl_l:
        kl_l.stop()
        
    # print("all listeners stopped")
    print("ShutDown Complete!!")


if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # print("KeyboardInterrupt caught in app.py")
        pass
