import sys
import asyncio
import os
import subprocess
import time
from pathlib import Path
import glob
try:
    from evdev import InputDevice, list_devices, ecodes
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False
try:
    from pynput import mouse as pynput_mouse
    from pynput import keyboard as pynput_keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
try:
    import pwd
except ImportError:
    pwd = None


state = {
    "M_CLICK": False,
    "CTRL_PRESSED": False,
    "KILL_SWITCH" : False,
    "ENTER_PRESSED" : False,
    "DEL_PRESSED":False
}
if getattr(sys, "frozen", False):
    BASE_PATH=Path(sys.executable).resolve().parent
else:
    BASE_PATH=Path(__file__).resolve().parent
TMP_PATH=os.path.join(BASE_PATH,"tmp")
os.makedirs(TMP_PATH, exist_ok=True)
if os.path.exists(TMP_PATH):
    for filename in os.listdir(TMP_PATH):
        file_path = os.path.join(TMP_PATH, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

def get_mouse_devices():
    if not HAS_EVDEV:
        print("[Warning] evdev is not available.")
        return [], []
        
    devices = [InputDevice(path) for path in list_devices()]
    mice = []
    kboard = []
    for path in list_devices():
        try:
            device=InputDevice(path)
        except: continue
        capabilities = device.capabilities()
        if ecodes.EV_KEY in capabilities:
            if ecodes.BTN_LEFT in capabilities[ecodes.EV_KEY]:
                mice.append(device)
            elif ecodes.KEY_A in capabilities[ecodes.EV_KEY]:
                kboard.append(device)
    return mice, kboard

if HAS_PYNPUT:
    def on_press(key):
        global state
        if key in (pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r):
            state["CTRL_PRESSED"] = True
        elif key == pynput_keyboard.Key.enter:
            state["ENTER_PRESSED"] = True
        elif key == pynput_keyboard.Key.esc:
            state["KILL_SWITCH"] = True
        elif key == pynput_keyboard.Key.delete:
            state["DEL_PRESSED"] = True

    def on_release(key):
        global state
        if key in (pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r):
            state["CTRL_PRESSED"] = False
        elif key == pynput_keyboard.Key.enter:
            state["ENTER_PRESSED"] = False
        elif key == pynput_keyboard.Key.esc:
            state["KILL_SWITCH"] = False
        elif key == pynput_keyboard.Key.delete:
            state["DEL_PRESSED"] = False

    def on_click(x, y, button, pressed):
        global state
        if button == pynput_mouse.Button.left:
            state["M_CLICK"] = pressed
# ------------------------------------------------------------------------

async def ListenM(mouse):
    try:
        async for event in mouse.async_read_loop():
            if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_LEFT:
                state["M_CLICK"]=(event.value==1 or event.value==2)
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass
async def ListenK(kboard):
    try:
        async for event in kboard.async_read_loop():
            if event.type == ecodes.EV_KEY:
                if event.code in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL):
                    state["CTRL_PRESSED"] = (event.value == 1 or event.value == 2)
                if event.code == ecodes.KEY_ENTER:
                    state["ENTER_PRESSED"] = (event.value == 1 or event.value == 2)
                if event.code == ecodes.KEY_ESC:
                    state["KILL_SWITCH"] = (event.value == 1 or event.value == 2)
                if event.code == ecodes.KEY_DELETE:
                    state["DEL_PRESSED"] = (event.value == 1 or event.value == 2)
            await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass
async def CheckActivation(kill):
    global state
    while not kill.is_set():
        if state["M_CLICK"] and state["CTRL_PRESSED"]:
            print("Activation")
            take_screenshot(os.path.join(TMP_PATH, f"{time.time()}.png"))
            state["M_CLICK"]=False
        if state["ENTER_PRESSED"] and state["CTRL_PRESSED"]:
            print("Activation")
            take_screenshot(os.path.join(TMP_PATH, f"{time.time()}.png"))
            state["ENTER_PRESSED"]=False
        if state["DEL_PRESSED"] and state["CTRL_PRESSED"]:
            SCs=[f for f in glob.glob(os.path.join(TMP_PATH, "*")) if os.path.isfile(f)]
            if SCs:
                latest_file = max(SCs, key=os.path.getmtime)
                os.remove(latest_file)
            print("Deleted Last ScreenShot!")
            state["DEL_PRESSED"]=False
        if state["KILL_SWITCH"] and state["CTRL_PRESSED"]:
            print("Recording Done! Saved the ScreenShots.")
            kill.set()
            break
        await asyncio.sleep(0.005)


def take_screenshot(output_path="screenshot.png"):
    abs_path = os.path.abspath(output_path)
    is_root = hasattr(os, 'geteuid') and os.geteuid() == 0
    real_user = os.environ.get("SUDO_USER") or os.environ.get("USER")
    uid = None
    if pwd and real_user:
        try:
            uid = str(pwd.getpwnam(real_user).pw_uid)
        except KeyError:
            uid = "1000"
    else:
        uid = "1000"
    wayland_socket = f"/run/user/{uid}/wayland-0"
    is_wayland = "WAYLAND_DISPLAY" in os.environ or os.path.exists(wayland_socket)
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
    if sys.platform.startswith("linux") and is_wayland:
        cmd_prefix = []
        run_env = os.environ.copy()
        if is_root:
            run_env["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"
            run_env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path=/run/user/{uid}/bus"
            run_env["WAYLAND_DISPLAY"] = wayland_display
            
            cmd_prefix = ["sudo", "-u", real_user, "env", 
                f"XDG_RUNTIME_DIR=/run/user/{uid}", 
                f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
                f"WAYLAND_DISPLAY={wayland_display}"]
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "GNOME").lower()
        try:
            if "gnome" in desktop or "unity" in desktop:
                cmd = cmd_prefix + ["gnome-screenshot", "-p", "-f", abs_path]
            elif "kde" in desktop:
                cmd = cmd_prefix + ["spectacle", "-b", "-n", "-o", abs_path]
            elif any(env in desktop for env in ["sway", "hyprland", "wlroots"]):
                cmd = cmd_prefix + ["grim", abs_path]
            else:
                cmd = cmd_prefix + ["gnome-screenshot", "-p", "-f", abs_path]
            if not os.path.exists(TMP_PATH):
                mkCMD=cmd_prefix+["mkdir", TMP_PATH]
                subprocess.run(mkCMD,env=run_env, check=True)
            subprocess.run(cmd, env=run_env, check=True)
            print(f"[Success] Wayland screenshot saved -> {abs_path}")

        except subprocess.CalledProcessError as e:
            print(f"[Error] Wayland screenshot failed: {e}")
            return False
    else:
        try:
            import mss
            from PIL import Image, ImageDraw
            
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                mouse_x, mouse_y = 0, 0
                if HAS_PYNPUT:
                    m_controller = pynput_mouse.Controller()
                    mouse_x, mouse_y = m_controller.position
                draw = ImageDraw.Draw(img)
                r = 8
                draw.ellipse(
                    (mouse_x - r, mouse_y - r, mouse_x + r, mouse_y + r), 
                    fill="red", 
                    outline="white"
                )
                img.save(abs_path)
            print(f"[Success] Standard screenshot saved -> {abs_path}")
        except ImportError:
            print("[Error] Missing libraries! Run: pip install mss Pillow pynput")
            return False

    if is_root and os.path.exists(abs_path) and pwd:
        try:
            user_info = pwd.getpwnam(real_user)
            os.chown(abs_path, user_info.pw_uid, user_info.pw_gid)
        except (KeyError, AttributeError, OSError):
            pass

    return True
        
async def main():
    mice, kboard = get_mouse_devices()
    kill = asyncio.Event()
    listener_tasks = []
    m_listener = None
    k_listener = None
    if mice and kboard:
        print("Started Listening For Activation (Linux)")
        for device in mice:
            listener_tasks.append(asyncio.create_task(ListenM(device)))
        for device in kboard:
            listener_tasks.append(asyncio.create_task(ListenK(device)))
    elif HAS_PYNPUT:
        print("Started Listening For Activation (Windows/Mac/Xorg)")
        m_listener = pynput_mouse.Listener(on_click=on_click)
        k_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        m_listener.start()
        k_listener.start()
    else:
        print("No devices found. Exiting.")
        sys.exit(1)
    await CheckActivation(kill)
    print("Stopping input listeners...")
    if listener_tasks:
        for task in listener_tasks:
            task.cancel()
        await asyncio.gather(*listener_tasks, return_exceptions=True)
    if m_listener:
        m_listener.stop()
    if k_listener:
        k_listener.stop()
    print("ShutDown Complete!!")

    
if __name__=="__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass