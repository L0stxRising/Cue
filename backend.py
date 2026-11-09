import os
import sys
import pathlib
from vision_prompt_text import *
from compiler_prompt_text import *
import base64
import glob
import concurrent.futures
import time
from openai import OpenAI


# def compress_b64(b64_str):
#     raw_b = base64.b64decode(b64_str)
#     im = Image.open(io.BytesIO(raw_b))
#     im.thumbnail((1280, 720))
#     buf = io.BytesIO()
#     im.save(buf, format="JPEG", quality=80)
#     return base64.b64encode(buf.getvalue()).decode('utf-8')


def ContactAI(prompt_text,img,ml,ak):
    cl=OpenAI(base_url="https://openrouter.ai/api/v1",api_key=ak)
    last_unc=False
    
    for i in range(15):
        m=ml[i%len(ml)]
        mc=[{"type":"text","text":prompt_text}]
        if img:
            mc.append({"type":"image_url","image_url":{"url":f"data:image/png;base64,{img}"}})
            
        try:
            r=cl.chat.completions.create(
                model=m,
                messages=[{"role":"user","content":mc}],
                temperature=0.05,
                max_tokens=300 if img else 4096
            )
            ct=r.choices[0].message.content
            if not ct:
                continue
            if "Unclear" in ct:
                if last_unc==True:
                    return ct
                last_unc=True
                continue
            return ct
        except Exception as e:
            print(f"Error {m}: {e}")
            time.sleep(1)
            
    return None



def main():
    im=os.environ.get("CUE_IMAGE_MODE")
    if im is None:
        im="No"
    cue_img_flag=im

    un=os.environ.get("CUE_USER_NOTES")
    
    t=os.environ.get("CUE_GUIDE_TITLE")
    if not t:
        t="Guide"
    guide_doc_title=t
    
    ak=os.environ.get("OPENROUTER_API_KEY","")

    base_dir=pathlib.Path(__file__).resolve().parent
    tmp_dir=os.path.join(base_dir,"tmp")
    raw_log_path=os.path.join(tmp_dir,"rawguide.txt")
    out_dir=os.path.join(base_dir,"Output")
    
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # exts=["*.jpg","*.png","*.jpeg","*.bmp"]
    exts=["*.jpg","*.png","*.jpeg"]
    files=[]
    for pat in exts:
        files.extend(glob.glob(os.path.join(tmp_dir,pat)))
    files.sort()

    d=[]
    for f in files:
        with open(f,"rb") as fh:
            d.append(base64.b64encode(fh.read()).decode('utf-8'))
            
    if len(d)<1:
        print("No ScreenShots were Available To be Loaded!")
        sys.exit()
        
    print("==============Loaded Screenshots=============")
    print(f"Working With {len(d)} Screenshots!\n")
    print("Starting the Process of Guide Making.")
    print("It Might take a While So just Sit back and Enjoy!")

    mls=[
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "minimax/minimax-m3:free",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    ]

    print("===========Connecting to the Model===========")
    
    # results_list = []
    # for cur_b64 in d:
    #     ans = ContactAI(pt, cur_b64, mls, ak)
    #     results_list.append(ans)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        rr=list(ex.map(lambda single_img:ContactAI(pt,single_img,mls,ak),d))

    sc=sum(1 for r_item in rr if r_item)
    if sc<(len(d)-2):
        print("Many of the Screenshots could not be Described. Try again Later.")
        sys.exit(1)

    with open(raw_log_path,"w") as g:
        for idx,ct in enumerate(rr):
            if ct:
                g.write(f"Interaction {idx+1}\n{ct}\n\n")

    print("====Completed ScreenShot Data Extraction!====")

    with open(raw_log_path,"r") as g:
        rs=g.read()
    raw_interactions_log=rs

    # cm2 = ["nvidia/nemotron-3-ultra-550b-a55b:free"]
    cm2=[
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "nvidia/nemotron-3-super-120b-a12b:free"
    ]
    
    nb=""
    if un:
        nb="### USER INSTRUCTIONS:\n"+un
    notes_section_block=nb
        
    cp=compiler_prompt_text.format(im=im,t=t,nb=nb,rs=rs,cue_img_flag=im,guide_doc_title=t,notes_section_block=nb,raw_interactions_log=rs,**locals())

    print("==========Compiling ScreenShot Data==========\n")
    res=ContactAI(cp,None,cm2,ak)
    if not res:
        print("Compiling Failed Try Again Later")
        sys.exit(1)

    folder_name=t.replace(" ","_")
    if not folder_name or len(folder_name)==0:
        folder_name="Guide"
        
    guide_dir=os.path.join(base_dir,"Output",folder_name)
    guide_file=os.path.join(guide_dir,f"{folder_name}.md")
    
    if not os.path.exists(guide_dir):
        os.mkdir(guide_dir)

    print("stored File, Embedded Screenshots")
    with open(guide_file,"w") as g:
        g.write(res)
        
    print("============Completed Compilation============")
    # print("cleaning up temp files")
    print(f"Your Guide is At {guide_dir}")
    print("=================Done, Enjoy!================")


if __name__=="__main__":
    main()
