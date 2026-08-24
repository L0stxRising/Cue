import tkinter as tk
from tkinter import scrolledtext
import os
import subprocess, threading, pathlib, glob
import sys
import requests
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
TMP = BASE / "tmp"
PY = str(BASE / "Env" / ("Scripts" if sys.platform == "win32" else "bin") / "python")
if not os.path.exists(PY): PY = sys.executable

BG, FG, BTN, ACT, ENT, OK = "#1a1a2e", "#e0e0e0", "#16213e", "#533483", "#0f3460", "#00d2ff"
F = lambda s=10, b=False: ("Helvetica", s, "bold") if b else ("Helvetica", s)


def btn(p, txt, bg, cmd, state="normal", w=20):
    return tk.Button(p, text=txt, width=w, font=F(11, True), bg=bg, fg=FG,
activebackground=ACT, activeforeground=FG, relief="flat",
bd=0, state=state, command=cmd)


def lbl(p, var=None, txt=None, size=10, fg=FG):
    kw = {"textvariable": var} if var else {"text": txt}
    return tk.Label(p, font=F(size), bg=BG, fg=fg, **kw)


class CueApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cue — Screenshot Guide Maker")
        self.geometry("620x600")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.process = None
        lbl(self, txt="✦ CUE", size=22, fg=OK).pack(pady=(18, 0))
        lbl(self, txt="Screenshot → Guide", fg="#888").pack()
        cf = tk.Frame(self, bg=BG); cf.pack(pady=14)
        self.record_btn = btn(cf, "⏺  Start Recording", BTN, self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=6)
        self.stop_btn = btn(cf, "⏹  Stop Recording", "#6a040f", self.stop_recording, "disabled")
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.status_var = tk.StringVar(value="Ready")
        lbl(self, var=self.status_var, fg=OK).pack(pady=(4, 2))
        self.count_var = tk.StringVar(value="Screenshots: 0")
        lbl(self, var=self.count_var, size=9, fg="#888").pack()

        tf = tk.Frame(self, bg=BG); tf.pack(pady=10)
        lbl(tf, txt="Guide Title:").grid(row=0, column=0, padx=4)
        self.title_entry = tk.Entry(tf, width=30, font=F(), bg=ENT, fg=FG,insertbackground=FG, relief="flat", bd=4)
        self.title_entry.grid(row=0, column=1, padx=4)

        nf = tk.Frame(self, bg=BG); nf.pack(pady=(0, 6))
        lbl(nf, txt="Notes for AI:").grid(row=0, column=0, padx=4)
        self.notes_entry = tk.Entry(nf, width=40, font=F(), bg=ENT, fg=FG,insertbackground=FG, relief="flat", bd=4)
        self.notes_entry.grid(row=0, column=1, padx=4)

        of = tk.Frame(self, bg=BG); of.pack(pady=(0, 6))
        self.img_var = tk.BooleanVar(value=False)
        tk.Checkbutton(of, text="Embed screenshots in guide", variable=self.img_var,font=F(9), bg=BG, fg=FG, selectcolor=BG,
                activebackground=BG, activeforeground=FG).pack(side="left", padx=4)
        self.gen_btn = btn(of, "⚡ Generate", ACT, self.generate_guide, "disabled", 12)
        self.gen_btn.pack(side="left", padx=10)

        self.log = scrolledtext.ScrolledText(self, width=72, height=13, bg="#0d1117",
        fg="#c9d1d9", font=("Courier", 9),
        relief="flat", bd=6, insertbackground=FG)
        self.log.pack(padx=14, pady=(6, 14))
        self.log.configure(state="disabled")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def update_count(self):
        self.count_var.set(f"Screenshots: {len(glob.glob(str(TMP / '*.png')))}")

    def _spawn(self, script, env=None):
        return subprocess.Popen([PY, "-u", str(BASE / script)], cwd=str(BASE),
        env=env or os.environ.copy(), stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True)

    def start_recording(self):
        self.record_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.gen_btn.configure(state="disabled")
        self.status_var.set("⏺ Recording — CTRL+Click/ENTER to capture, CTRL+DEL to delete last, CTRL+ESC to stop")
        self.log_msg("Starting screenshot capture...")

        def run():
            self.process = self._spawn("app.py")
            for line in self.process.stdout:
                self.after(0, self.log_msg, line.rstrip())
                self.after(0, self.update_count)
            ret = self.process.wait()
            self.after(0, self.on_recording_done, ret)

        threading.Thread(target=run, daemon=True).start()

    def stop_recording(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def on_recording_done(self, ret=0):
        self.stop_btn.configure(state="disabled")
        self.gen_btn.configure(state="normal")
        self.update_count()
        self.status_var.set("✓ Recording complete — enter a title and generate"
        if ret == 0 else f"⚠ Recording ended with error ({ret})")
        self.log_msg("Recording finished.")

    def generate_guide(self):
        title = self.title_entry.get().strip() or "Untitled Guide"
        self.gen_btn.configure(state="disabled")
        self.status_var.set("⚡ Generating guide...")
        self.log_msg(f'\nGenerating guide: "{title}"...')

        def run():
            env = os.environ.copy()
            env["CUE_GUIDE_TITLE"] = title
            env["CUE_USER_NOTES"] = self.notes_entry.get().strip()
            env["CUE_IMAGE_MODE"] = "Yes" if self.img_var.get() else "No"
            proc = self._spawn("backend.py", env)
            for line in proc.stdout:
                self.after(0, self.log_msg, line.rstrip())
            ret = proc.wait()
            self.after(0, self.on_generate_done, ret, title)

        threading.Thread(target=run, daemon=True).start()

    def on_generate_done(self, ret, title):
        self.record_btn.configure(state="normal")
        self.status_var.set(f"✓ Guide saved → Output/{title}.md" if ret == 0
        else f"⚠ Guide generation failed ({ret})")
        self.log_msg("DOne Guide generation complete!" if ret == 0 else "Error Guide generation failed.")

    def on_close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.destroy()


if __name__ == "__main__":
    CueApp().mainloop()