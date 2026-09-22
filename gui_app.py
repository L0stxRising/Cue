import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
import sys
import pathlib
import glob
import hashlib
import random
import json
import time
import platform


if getattr(sys,"frozen",False):
    bs=pathlib.Path(sys.executable).resolve().parent
else:
    bs=pathlib.Path(__file__).resolve().parent
tp=bs/"tmp"
py2=str(bs/"Env"/("Scripts" if sys.platform=="win32" else "bin")/"python")
if not os.path.exists(py2):
    py2=sys.executable
frzn=getattr(sys,"frozen",False)

scr = None
a=0
b=""
temp_flag=False
xx  = 42
dat=[]

# w = tk.Tk()
# w.title("test window")
# w.mainloop()


class CueApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cue")
        self.configure(bg="black")
        self.geometry("420x280")
        self.resizable(False,False)
        self.p=None
        self.rn=False
        self._t=0

        tk.Label(self,text="Cue",font=("Arial",18,"bold"),bg="black",fg="white").pack(anchor="w",padx=14,pady=(10,2))
        r=tk.Frame(self,bg="black")
        r.pack(fill="x",padx=14,pady=(4,3))
        self.rb=tk.Button(r,text="Record",bg="steel blue",fg="white",relief="flat",width=9,command=self.srec)
        
        self.rb.pack(side="left",padx=(0,3))
        # self.rb.configure(cursor="hand2")
        
        self.sb=tk.Button(r,text="Stop",bg="dark red",fg="white",relief="flat",width=7,state="disabled",command=self.stprec)
        
        self.sb.pack(side="left",padx=(0,3))
        
        self.gb=tk.Button(r,text="Generate",bg="dark green",fg="white",relief="flat",width=9,state="disabled",command=self.dg)
        self.gb.pack(side="left")

        self.sv =tk.StringVar(value="Ready")
        
        # status_label = tk.Label(self, text="idle")
        # status_label.pack()
        tk.Label(self,textvariable=self.sv,bg="black",fg="steel blue",font=("Arial",10)).pack(anchor="w",padx=16,pady=(6,0))

        self.cv=tk.StringVar(value="0 screenshots")
        tk.Label(self,textvariable=self.cv,bg="black",fg="gray",font=("Arial",8)).pack(anchor="w",padx=16,pady=(0,5))

        f2=tk.Frame(self,bg="black")
        f2.pack(fill="x",padx=14,pady=(0,3))
        
        tk.Label(f2,text="Title",bg="black",fg="gray",font=("Arial",9)).grid(row=0,column=0,sticky="w")
        self.te=tk.Entry(f2,width=36,bg="black",fg="white",insertbackground="white",relief="flat",bd=3)
        self.te.grid(row=0,column=1,padx=(6,0),pady=2)
        # self.te.insert(0, "enter title here")

        tk.Label(f2,text="Notes",bg="black",fg="gray",font=("Arial",9)).grid(row=1,column=0,sticky="w")
        self.ne=tk.Entry(f2,width=36,bg="black",fg="white",insertbackground="white",relief="flat",bd=3)
        
        self.ne.grid(row=1,column=1,padx=(6,0),pady=2)

        self.iv=tk.BooleanVar(value=False)
        
        # chk = tk.Checkbutton(self, text="include images")
        # chk.pack()
        tk.Checkbutton(self,text="Embed screenshots",variable=self.iv,bg="black",fg="white",selectcolor="black",activebackground="black",activeforeground="white").pack(anchor="w",padx=14,pady=(2,6))

        self.protocol("WM_DELETE_WINDOW",self._qt)

    def _cn(self):
        c=len(glob.glob(str(tp/"*.png")))
        self.cv.set(f"{c} screenshots")

    def _sp(self,s,env=None):
        if frzn==True:
            e=sys.executable
            
            if "app" in s: 
                fl="--capture"
            else: 
                fl="--generate"
            # return subprocess.Popen([e, fl], shell=True)
            return subprocess.Popen([e,fl],cwd=str(bs),env=env or os.environ.copy(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        else:
            return subprocess.Popen([py2,"-u",str(bs/s)],cwd=str(bs),env=env or os.environ.copy(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)

    def srec(self):
        self.rb.configure(state="disabled")
        self.sb.configure(state="normal")
        self.gb.configure(state="disabled")
        self.sv.set("Capturing screenshots...")
        
        self.rn=True
        
        def _r():
            self.p=self._sp("app.py")
            for ln in self.p.stdout:
                self.after(0,self._cn)
            rt=self.p.wait()
            self.after(0,self._rd,rt)
        threading.Thread(target=_r,daemon=True).start()

    def stprec(self):
        if self.p and self.p.poll() is None:
            self.p.terminate()

    def _rd(self,rt=0):
        self.sb.configure(state="disabled")
        self.gb.configure(state="normal")
        
        self.rn=False
        
        self._cn()
        
        if rt==0: 
            self.sv.set("Done recording")
        else: 
            self.sv.set(f"Error ({rt})")

    def dg(self):
        t=self.te.get().strip()
        
        if t=="": 
            t="Untitled Guide"
            
        self.gb.configure(state="disabled")
        self.sv.set("Generating guide...")
        
        def _r():
            en=os.environ.copy()
            en["CUE_GUIDE_TITLE"]=t
            en["CUE_USER_NOTES"]=self.ne.get().strip()
            
            if self.iv.get()==True: 
                en["CUE_IMAGE_MODE"]="Yes"
            else: 
                en["CUE_IMAGE_MODE"]="No"
                
            # print("starting gen with title:", t)
            p2=self._sp("backend.py",en)
            
            out=[]
            for ln in p2.stdout:
                out.append(ln)
            rt=p2.wait()
            self.after(0,self._gd,rt,t,"".join(out))
        threading.Thread(target=_r,daemon=True).start()

    def _gd(self,rt,t,log=""):
        self.rb.configure(state="normal")
        self.gb.configure(state="normal")
        if rt==0: 
            self.sv.set(f"Guide saved — Output/{t}")
        else: 
            self.sv.set(f"Generation failed ({rt})")
            top=tk.Toplevel(self)
            top.title(f"Error Log ({rt})")
            top.geometry("500x300")
            st=scrolledtext.ScrolledText(top,bg="black",fg="white")
            st.pack(fill="both",expand=True)
            st.insert("1.0",log or "No error output captured.")

    def _qt(self):
        if self.p and self.p.poll() is None:
            self.p.terminate()
        # self.quit()
        self.destroy()

if __name__=="__main__":
    CueApp().mainloop()