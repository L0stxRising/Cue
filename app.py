import sys
import os
import asyncio
import time
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

st={"mc":False,"ctrl":False,"ks":False,"ent":False,"dl":False}

# cnt = 0
base_dir=Path(__file__).resolve().parent
tmp_dir=os.path.join(base_dir,"tmp")

if os.path.exists(tmp_dir):
    for f in os.listdir(tmp_dir):
        fp=os.path.join(tmp_dir,f)
        if os.path.isfile(fp):
            try:
                os.unlink(fp)
            except OSError:
                pass


def getD():
    if not hev:
        print("Evdev is not available.")
        return [],[]

    mice=[]
    kboard=[]
    for p in list_devices():
        try:
            dev=InputDevice(p)
        except Exception:
            continue
        caps=dev.capabilities()
        if ecodes.EV_KEY in caps:
            kc=caps[ecodes.EV_KEY]
            if ecodes.BTN_LEFT in kc:
                mice.append(dev)
            elif ecodes.KEY_A in kc:
                kboard.append(dev)
                
    return mice,kboard


if hasPyn:
    def opr(k):
        global st
        if k in(pk.Key.ctrl_l,pk.Key.ctrl_r): st["ctrl"]=True
        elif k==pk.Key.enter: st["ent"]=True
        elif k==pk.Key.esc: st["ks"]=True
        elif k==pk.Key.delete: st["dl"]=True

    def orl(k):
        global st
        if k in(pk.Key.ctrl_l,pk.Key.ctrl_r): st["ctrl"]=False
        elif k==pk.Key.enter: st["ent"]=False
        elif k==pk.Key.esc: st["ks"]=False
        elif k==pk.Key.delete: st["dl"]=False

    def ocl(x,y,btn,pressed):
        global st
        if btn==pm.Button.left:
            st["mc"]=pressed


async def ListenM(m):
    try:
        async for ev in m.async_read_loop():
            if ev.type==ecodes.EV_KEY and ev.code==ecodes.BTN_LEFT:
                st["mc"]=(ev.value==1 or ev.value==2)
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass


async def ListenK(kb):
    try:
        async for ev in kb.async_read_loop():
            if ev.type==ecodes.EV_KEY:
                v=(ev.value==1 or ev.value==2)
                if ev.code in(ecodes.KEY_LEFTCTRL,ecodes.KEY_RIGHTCTRL): st["ctrl"]=v
                elif ev.code==ecodes.KEY_ENTER: st["ent"]=v
                elif ev.code==ecodes.KEY_ESC: st["ks"]=v
                elif ev.code==ecodes.KEY_DELETE: st["dl"]=v
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass

# async def check_mouse_pos():
#     while True:
#         await asyncio.sleep(1)


async def check(kl):
    global st
    while not kl.is_set():
        if (st["mc"] or st["ent"]) and st["ctrl"]:
            print("Activation")
            fn=f"{time.time()}.png"
            take_sc(os.path.join(tmp_dir,fn))
            st["mc"]=False
            st["ent"]=False
            
        if st["dl"] and st["ctrl"]:
            scs=[f for f in glob.glob(os.path.join(tmp_dir,"*")) if os.path.isfile(f)]
            if len(scs)>0:
                lt=max(scs,key=os.path.getmtime)
                try:
                    os.remove(lt)
                    print("Deleted Last ScreenShot!")
                except Exception as e:
                    print(f"Failed deleting screenshot: {e}")
            else:
                print("No screenshots to delete.")
            st["dl"]=False
            
        if st["ks"] and st["ctrl"]:
            print("Recording Done! Saved the ScreenShots.")
            kl.set()
            break
            
        await asyncio.sleep(0.005)


def take_sc(op="screenshot.png"):
    ap=os.path.abspath(op)

    # if sys.platform == "win32":
    #     import mss
    #     with mss.mss() as sct:
    #         sct.shot(output=ap)
    #     return True
    try:
        import mss
        from PIL import Image,ImageDraw
        with mss.mss() as sct:
            mon=sct.monitors[0]
            si=sct.grab(mon)
            img=Image.frombytes("RGB",si.size,si.bgra,"raw","BGRX")
            mx,my=0,0
            
            if hasPyn==True:
                mc=pm.Controller()
                mx,my=mc.position
                
            dr=ImageDraw.Draw(img)
            r=8
            # dr.rectangle((mx-r, my-r, mx+r, my+r), fill="blue")
            dr.ellipse((mx-r,my-r,mx+r,my+r),fill="red",outline="white")
            img.save(ap)
            
        print(f"Standard screenshot saved -> {ap}")
    except ImportError:
        return False
            
    return True


async def main():
    m,k=getD()
    kl=asyncio.Event()
    lt=[]
    
    # ml,kl = pm.Listener(), pk.Listener()
    ml=None
    kl_l=None
    
    if len(m)>0 and len(k)>0:
        print("Started Listening For Activation")
        for dev in m: lt.append(asyncio.create_task(ListenM(dev)))
        for dev in k: lt.append(asyncio.create_task(ListenK(dev)))
        
    elif hasPyn==True:
        print("Started Listening For Activation")
        ml=pm.Listener(on_click=ocl)
        kl_l=pk.Listener(on_press=opr,on_release=orl)
        ml.start()
        kl_l.start()
        
    else:
        print("No devices found. Exiting.")
        sys.exit(1)
        
    await check(kl)
    print("Stopping input listeners...")
        
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