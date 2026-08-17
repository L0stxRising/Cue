"""
gui_app.py — Cue Graphical Interface

A minimal dark-themed Tkinter GUI for the Cue pipeline.
Phase 1: Record screenshots (runs app.py in background)
Phase 2: Enter title → Generate guide (runs backend.py)
"""

import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
import sys
import pathlib
import glob

BASE = pathlib.Path(__file__).resolve().parent
TMP = BASE / "tmp"
VENV_PYTHON = str(BASE / "Env" / ("Scripts" if sys.platform == "win32" else "bin") / "python")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

# ── Colors ──
BG = "#1a1a2e"
FG = "#e0e0e0"
ACCENT = "#0f3460"
BTN_BG = "#16213e"
BTN_ACTIVE = "#533483"
ENTRY_BG = "#0f3460"
SUCCESS = "#00d2ff"


class CueApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cue — Screenshot Guide Maker")
        self.geometry("620x520")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.process = None

        # ── Header ──
        tk.Label(self, text="✦ CUE", font=("Helvetica", 22, "bold"),
                 bg=BG, fg=SUCCESS).pack(pady=(18, 0))
        tk.Label(self, text="Screenshot → Guide", font=("Helvetica", 10),
                 bg=BG, fg="#888").pack()

        # ── Controls frame ──
        cf = tk.Frame(self, bg=BG)
        cf.pack(pady=14)

        self.record_btn = tk.Button(cf, text="⏺  Start Recording", width=20,
                                    font=("Helvetica", 11, "bold"),
                                    bg=BTN_BG, fg=FG, activebackground=BTN_ACTIVE,
                                    activeforeground=FG, relief="flat", bd=0,
                                    command=self.start_recording)
        self.record_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(cf, text="⏹  Stop Recording", width=20,
                                  font=("Helvetica", 11, "bold"),
                                  bg="#6a040f", fg=FG, activebackground="#9d0208",
                                  activeforeground=FG, relief="flat", bd=0,
                                  state="disabled", command=self.stop_recording)
        self.stop_btn.grid(row=0, column=1, padx=6)

        # ── Status ──
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self, textvariable=self.status_var,
                                     font=("Helvetica", 10), bg=BG, fg=SUCCESS)
        self.status_label.pack(pady=(4, 2))

        self.count_var = tk.StringVar(value="Screenshots: 0")
        tk.Label(self, textvariable=self.count_var, font=("Helvetica", 9),
                 bg=BG, fg="#888").pack()

        # ── Title + Generate ──
        tf = tk.Frame(self, bg=BG)
        tf.pack(pady=10)
        tk.Label(tf, text="Guide Title:", font=("Helvetica", 10),
                 bg=BG, fg=FG).grid(row=0, column=0, padx=4)
        self.title_entry = tk.Entry(tf, width=30, font=("Helvetica", 10),
                                    bg=ENTRY_BG, fg=FG, insertbackground=FG,
                                    relief="flat", bd=4)
        self.title_entry.grid(row=0, column=1, padx=4)

        self.gen_btn = tk.Button(tf, text="⚡ Generate", font=("Helvetica", 10, "bold"),
                                 bg="#533483", fg=FG, activebackground=BTN_ACTIVE,
                                 activeforeground=FG, relief="flat", bd=0,
                                 state="disabled", command=self.generate_guide)
        self.gen_btn.grid(row=0, column=2, padx=6)

        # ── Log ──
        self.log = scrolledtext.ScrolledText(self, width=72, height=14,
                                             bg="#0d1117", fg="#c9d1d9",
                                             font=("Courier", 9),
                                             relief="flat", bd=6,
                                             insertbackground=FG)
        self.log.pack(padx=14, pady=(6, 14))
        self.log.configure(state="disabled")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def log_msg(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def update_count(self):
        n = len(glob.glob(str(TMP / "*.png")))
        self.count_var.set(f"Screenshots: {n}")

    def start_recording(self):
        self.record_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.gen_btn.configure(state="disabled")
        self.status_var.set("⏺ Recording — CTRL+Click to capture, CTRL+DEL to stop")
        self.log_msg("[Phase 1] Starting screenshot capture...")

        def run():
            self.process = subprocess.Popen(
                [VENV_PYTHON, str(BASE / "app.py")],
                cwd=str(BASE),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in self.process.stdout:
                self.after(0, self.log_msg, line.strip())
                self.after(0, self.update_count)
            self.process.wait()
            self.after(0, self.on_recording_done)

        threading.Thread(target=run, daemon=True).start()
        self._poll_count()

    def _poll_count(self):
        if self.process and self.process.poll() is None:
            self.update_count()
            self.after(1000, self._poll_count)

    def stop_recording(self):
        if self.process:
            self.process.terminate()
            self.on_recording_done()

    def on_recording_done(self):
        self.stop_btn.configure(state="disabled")
        self.gen_btn.configure(state="normal")
        self.update_count()
        self.status_var.set("✓ Recording complete — enter a title and generate")
        self.log_msg("[Phase 1] Recording finished.")

    def generate_guide(self):
        title = self.title_entry.get().strip() or "Untitled Guide"
        self.gen_btn.configure(state="disabled")
        self.status_var.set("⚡ Generating guide...")
        self.log_msg(f"\n[Phase 2] Generating guide: \"{title}\"...")

        env = os.environ.copy()
        env["CUE_GUIDE_TITLE"] = title

        def run():
            proc = subprocess.Popen(
                [VENV_PYTHON, str(BASE / "backend.py")],
                cwd=str(BASE), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            for line in proc.stdout:
                self.after(0, self.log_msg, line.strip())
            proc.wait()
            self.after(0, self.on_generate_done, title)

        threading.Thread(target=run, daemon=True).start()

    def on_generate_done(self, title):
        self.status_var.set(f"✓ Guide saved → Output/{title}.md")
        self.log_msg("[Done] Guide generation complete!")
        self.record_btn.configure(state="normal")

    def on_close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.destroy()


if __name__ == "__main__":
    CueApp().mainloop()