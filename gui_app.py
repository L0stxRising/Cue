import os
import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import pathlib
import sys
import glob
# import time


base_dir=pathlib.Path(__file__).resolve().parent
tmp_dir=base_dir/"tmp"

if sys.platform=="win32":
    py_bin=str(base_dir/"Env"/"Scripts"/"python.exe")
else:
    py_bin=str(base_dir/"Env"/"bin"/"python")

if not os.path.exists(py_bin):
    py_bin=sys.executable


class CueApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cue")
        self.geometry("420x280")
        self.resizable(False,False)
        self.configure(bg="black")
        self.proc=None

        tk.Label(self,text="Cue",font=("Arial",18,"bold"),bg="black",fg="white").pack(anchor="w",padx=14,pady=(10,2))

        btn_row=tk.Frame(self,bg="black")
        btn_row.pack(fill="x",padx=14,pady=(4,3))
        self.btn_rec=tk.Button(btn_row,text="Record",bg="steel blue",fg="white",relief="flat",width=9,command=self.start_rec)
        self.btn_rec.pack(side="left",padx=(0,3))
        # self.btn_rec.configure(cursor="hand2")
        
        self.btn_stop=tk.Button(btn_row,text="Stop",bg="dark red",fg="white",relief="flat",width=7,state="disabled",command=self.stop_rec)
        self.btn_stop.pack(side="left",padx=(0,3))
        
        self.btn_gen=tk.Button(btn_row,text="Generate",bg="dark green",fg="white",relief="flat",width=9,state="disabled",command=self.generate)
        self.btn_gen.pack(side="left")

        self.status_var=tk.StringVar(value="Ready")
        tk.Label(self,textvariable=self.status_var,bg="black",fg="steel blue",font=("Arial",10)).pack(anchor="w",padx=16,pady=(6,0))

        self.count_var=tk.StringVar(value="0 screenshots")
        tk.Label(self,textvariable=self.count_var,bg="black",fg="gray",font=("Arial",8)).pack(anchor="w",padx=16,pady=(0,5))

        form=tk.Frame(self,bg="black")
        form.pack(fill="x",padx=14,pady=(0,3))
        
        tk.Label(form,text="Title",bg="black",fg="gray",font=("Arial",9)).grid(row=0,column=0,sticky="w")
        self.entry_title=tk.Entry(form,width=36,bg="black",fg="white",insertbackground="white",relief="flat",bd=3)
        self.entry_title.grid(row=0,column=1,padx=(6,0),pady=2)

        tk.Label(form,text="Notes",bg="black",fg="gray",font=("Arial",9)).grid(row=1,column=0,sticky="w")
        self.entry_notes=tk.Entry(form,width=36,bg="black",fg="white",insertbackground="white",relief="flat",bd=3)
        self.entry_notes.grid(row=1,column=1,padx=(6,0),pady=2)

        self.img_var=tk.BooleanVar(value=False)
        # chk = tk.Checkbutton(self, text="images")
        tk.Checkbutton(self,text="Embed screenshots",variable=self.img_var,bg="black",fg="white",
                       selectcolor="black",activebackground="black",activeforeground="white").pack(anchor="w",padx=14,pady=(2,6))

        self.protocol("WM_DELETE_WINDOW",self.on_close)

    def update_count(self):
        count=len(glob.glob(str(tmp_dir/"*.png")))
        # print("count:", count)
        self.count_var.set(f"{count} screenshots")

    def run_subproc(self,script,env=None):
        cmd=[py_bin,"-u",str(base_dir/script)]
        # return subprocess.Popen(cmd, shell=True)
        return subprocess.Popen(cmd,cwd=str(base_dir),env=env or os.environ.copy(),
                                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)

    def start_rec(self):
        self.btn_rec.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.btn_gen.config(state="disabled")
        self.status_var.set("Capturing screenshots...")

        def worker():
            # print("worker started")
            self.proc=self.run_subproc("app.py")
            for _ in self.proc.stdout:
                self.after(0,self.update_count)
            code=self.proc.wait()
            self.after(0,self.rec_done,code)

        threading.Thread(target=worker,daemon=True).start()

    def stop_rec(self):
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()

    def rec_done(self,code):
        self.btn_stop.config(state="disabled")
        self.btn_gen.config(state="normal")
        self.update_count()
        if code==0:
            self.status_var.set("Done recording")
        else:
            self.status_var.set(f"Error ({code})")

    def generate(self):
        title=self.entry_title.get().strip()
        if not title or len(title)==0:
            title="Untitled Guide"
        else:
            title=title
            
        self.btn_gen.config(state="disabled")
        self.status_var.set("Generating guide...")

        def worker():
            env=os.environ.copy()
            env["CUE_GUIDE_TITLE"]=title
            env["CUE_USER_NOTES"]=self.entry_notes.get().strip()
            
            if self.img_var.get()==True:
                env["CUE_IMAGE_MODE"]="Yes"
            else:
                env["CUE_IMAGE_MODE"]="No"

            p=self.run_subproc("backend.py",env)
            # output = "".join([l for l in p.stdout])
            output=p.stdout.read()
            code=p.wait()
            self.after(0,self.gen_done,code,title,output)

        threading.Thread(target=worker,daemon=True).start()

    def gen_done(self,code,title,output):
        self.btn_rec.config(state="normal")
        self.btn_gen.config(state="normal")
        if code==0:
            self.status_var.set(f"Guide saved — Output/{title}")
        else:
            self.status_var.set(f"Generation failed ({code})")
            err_win=tk.Toplevel(self)
            err_win.title(f"Error Log ({code})")
            err_win.geometry("500x300")
            txt=scrolledtext.ScrolledText(err_win,bg="black",fg="white")
            txt.pack(fill="both",expand=True)
            if output and len(output)>0:
                txt.insert("1.0",output)
            else:
                txt.insert("1.0","No error output captured.")

    def on_close(self):
        if self.proc:
            if self.proc.poll() is None:
                self.proc.terminate()
        # self.quit()
        self.destroy()


if __name__=="__main__":
    CueApp().mainloop()
