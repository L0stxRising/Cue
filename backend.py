import os
import sys
import pathlib
try:
    from dotenv import load_dotenv
    
    if getattr(sys,"frozen",False):
        dp2=pathlib.Path(sys.executable).resolve().parent/".env"
        
    else:
        dp2=pathlib.Path(__file__).resolve().parent/".env"
    load_dotenv(dp2)
except ImportError:
    pass
import json
import base64
import glob
import urllib.request
import urllib.error
import shutil
import re
import concurrent
import time
import hashlib
# import requests
# from PIL import Image


def ContactAI(prompt_text,img,ml,api_key):
    idx =0
    last_unc=False
    for _ in range(15):
        idx=idx%len(ml)
        mc=[{"type":"text","text":prompt_text}]
        if img:
            mc.append({"type":"image_url","image_url":{"url":f"data:image/png;base64,{img}"}})
        ReqData={
            "model":ml[idx],
            "messages":[{"role":"user","content":mc}],
            "temperature":0.05,
            "max_tokens":300 if img else 4096
        }
        
        ed=json.dumps(ReqData).encode('utf-8')
        rq =urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=ed)
        rq.add_header('Authorization',f'Bearer {api_key}')
        rq.add_header('Content-type','application/json')
        rq.add_header('HTTP-Referer','https://localhost')
        rq.add_header('X-title','UI_Analyzer_Script')
        
        try:
            response=urllib.request.urlopen(rq)
            r_body=response.read().decode('utf-8')
            if not r_body:
                print(f"Empty response from {ml[idx]}")
                idx+=1
                continue
            rs=json.loads(r_body)

            # if rs.get('error'):
            #     print(rs['error'])
            #     ix+=1
            #     continue

            if not rs or 'error' in rs:
                em=rs.get('error',{}).get('message','Unknown Error') if isinstance(rs,dict) else 'Invalid JSON'
                print(f"API Error from {ml[idx]}: {em}")
                idx +=1
                continue
            
            msg=rs.get('choices',[{}])[0].get('message',{})
            ct=msg.get('content') if msg else None
            if ct is None:
                print(f"Model {ml[idx]} failed, retrying...")
                idx+=1
                continue
            
            if "Unclear" in ct:
                print("Model Unable to Extract Data, Trying Again")
                if last_unc:
                    return ct
                last_unc=True
                continue
            return ct
        
        
        except urllib.error.HTTPError as e:
            err=e.read().decode('utf-8')
            print(f'Model {ml[idx]} failed with HTTP {e.code}: {err}')
            idx+=1
            time.sleep(1)
            
        except Exception as e:
            print(f'Connecting Failed with Error {e}')
            idx +=1
            time.sleep(1)
    else:
        return None

def main():
    i=os.environ.get("CUE_IMAGE_MODE")
    imgM=i if i is not None else "No"
    
    n=os.environ.get("CUE_USER_NOTES")
    u_notes=n if n is not None else None
    
    t=os.environ.get("CUE_GUIDE_TITLE")
    title=t if t is not None else "Guide"
    
    API_KEY=os.environ.get("OPENROUTER_API_KEY","")

    if getattr(sys,"frozen",False):
        bp=pathlib.Path(sys.executable).resolve().parent
    else:
        bp =pathlib.Path(__file__).resolve().parent
    
    tp=os.path.join(bp,"tmp")
    
    gp=os.path.join(tp,"rawguide.txt")
    if not os.path.exists(os.path.join(bp,"Output")):
        os.mkdir(os.path.join(bp,"Output"))

    # exts=["*.jpg","*.png","*.jpeg","*.bmp"]
    exts=["*.jpg","*.png","*.jpeg"]
    fl=[]
    for ext in exts:
        fl.extend(glob.glob(os.path.join(tp,ext)))
    fl.sort()

    d=[]
    for f in fl:
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

    pt = """
You are analyzing ONE screenshot. A click location is marked in ONE of two ways:

TYPE A — A synthetic marker: a perfectly round, solid, flat-colored RED DOT/CIRCLE drawn on top of the image. It has no text, no icon, no gradient — just a plain circle. This is NOT part of the real app UI.

TYPE B — A normal OS mouse cursor (small arrow/pointer icon), if no red dot exists.

STEP 1 — FIND THE MARKER:
- Scan for the plain red circle first. Do NOT confuse it with real red UI elements (buttons, error badges, notification dots, icons) — those usually have text, shading, or shape details. The synthetic marker is a flat, uniform circle only.
- If no such flat red circle exists anywhere, locate the normal mouse cursor arrow instead.
- If neither is visible, respond with the fallback format at the bottom.

STEP 2 — CHECK WHAT IS DIRECTLY UNDER THE MARKER:
The screenshot may have been captured a moment AFTER the user moved their mouse, so the marker might be resting on blank space, a margin, or between elements rather than exactly on the intended target. Classify what you see directly under/touching the marker into ONE of these:

- "On Element" — The marker is clearly touching or overlapping a distinct, nameable UI element (button, field, tab, link, icon, checkbox, etc).
- "Empty Space" — The marker is sitting on blank background, whitespace, plain page area, or an empty margin, with NO element directly beneath it.

STEP 3 — HANDLE EACH CASE:

IF "On Element": Identify that element only. Do not look elsewhere.

IF "Empty Space": Look ONLY within a small tight radius immediately around the marker (roughly the size of the marker itself, doubled) for the SINGLE nearest, most obviously interactive element (button, field, tab, link). 
- You may propose this nearby element as the likely intended target ONLY if exactly one clear interactive candidate exists nearby.
- If multiple equally-close candidates exist, or nothing interactive is within that tight radius, do NOT guess — use the fallback format instead.
- Never infer based on what the page "usually" does or what a typical user "probably" wants. Base the guess strictly on visible proximity, nothing else.

STEP 4 — INTERPRET:
If the identified element is a text input, assume the user typed relevant text and pressed Enter.

Respond in EXACTLY this plain-text format. No markdown, no JSON, no extra sentences:

Application: <App/website name, or "Unidentified">
Marker Found: <Red Dot / Mouse Cursor / None>
Marker Status: <On Element / Empty Space>
Confidence: <Direct / Inferred>
Element Type: <Button / Text Field / Link / Icon / Tab / Menu Item / Checkbox / Other>
Element Text: <exact visible label/text, or "[Icon: short description]" if no text>
Element Location: <e.g. Top-left, Center, Bottom navbar>
Likely Action: <short phrase — what happens when this is used>
Step Summary: <one sentence, e.g. "User clicks the Save button in the top toolbar.">

Use Confidence: Direct only if Marker Status is "On Element".
Use Confidence: Inferred only if Marker Status is "Empty Space" and you found exactly one clear nearby candidate.

If you cannot confidently find a marker, or find empty space with no single clear nearby candidate, respond with ONLY:
Unclear
"""

    print("===========Connecting to the Model===========")
    rs2=[]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        results=ex.map(lambda img:ContactAI(pt,img,mls,API_KEY),d)
        rr=list(results)

    sc=sum(1 for r in rr if r)

    if sc<(len(d)-2):
        print("Many of the Screenshots could not be Described. Try again Later.")
        sys.exit(1)

    with open(gp,"w") as g:
        for idx,ct in enumerate(rr):
            if ct:
                g.write(f"Interaction {idx+1}\n{ct}\n\n")

    print("====Completed ScreenShot Data Extraction!====")

    with open(gp,"r") as g:
        rs=g.read()

    # cm2=["nvidia/nemotron-3-ultra-550b-a55b:free"]
    cm2=["nvidia/nemotron-3-ultra-550b-a55b:free","nvidia/nemotron-3-ultra-550b-a55b:free","nvidia/nemotron-3-super-120b-a12b:free"]
    cp2=f"""
You are a Senior Technical Writer. Convert the raw UI-interaction logs below into a concise, well-formatted Markdown user guide.

### INPUT FORMAT NOTE:
Each raw log entry is one interaction with fields: Application, Marker Found, Marker Status, Confidence, Element Type, Element Text, Element Location, Likely Action, Step Summary. These come from an imperfect vision model, so some entries may be marked "Unclear" (extraction failed) or have "Confidence: Inferred" (the cursor was on empty space and the model guessed the nearest likely element).

### HANDLING UNCERTAIN ENTRIES:
- If Confidence is "Inferred," you may lightly cross-check it against the immediately PRECEDING and FOLLOWING steps only (nothing else) to judge if it fits the natural flow of the task. If it fits, treat it as a normal step. If it clearly contradicts the surrounding flow (e.g., breaks the task's logical sequence), silently omit it or merge it into the adjacent step rather than including a contradictory action.
- If an entry is "Unclear," never invent a step for it. Either omit it entirely or merge it into the surrounding narrative if the adjacent steps make its purpose obvious (e.g., a transition between two related actions).
- You may ONLY use adjacent log entries as context for resolving ambiguity. Never use outside knowledge about how the named application "usually" works to fill gaps.
- Regardless of Confidence level, write the final step in the SAME clean, direct, imperative tone. Do not add hedge words like "likely," "probably," or "it seems" into the final guide text — the reader should see a clean instruction. Uncertainty is resolved BEFORE writing, not expressed IN the writing.

### CORE RULES & FORMATTING:
1. **Pristine Markdown:** Clean structure and spacing. ALWAYS **bold** exact UI element text (e.g., click **Settings**), using the exact spelling/capitalization from "Element Text" — never invent or paraphrase UI labels.
2. **Smart Compression:** Merge consecutive micro-steps into one logical action if they're part of the same operation (e.g., clicking a search box + typing + pressing Enter becomes "Search for [X]"). Add an obvious missing precursor step if needed (e.g., "Navigate to [App]") based on the first entry's Application field.
3. **Ruthless Conciseness:** Direct, professional, imperative tone. No filler, no meta-commentary about the source logs, confidence levels, or extraction quality.
4. **Strict Accuracy:** Only use element names/text explicitly present in the logs. Never fabricate a UI label that isn't given, even when merging or inferring around uncertain entries.
5. **Image Placement:** User's image preference is "{imgM}". If enabled, append `|Image N|` at the end of a step, where N is the ORIGINAL "Interaction N" number from the logs it was derived from (use the first number if multiple were merged).

### REQUIRED OUTPUT SCHEMA:

# {title}

**Application:** [App Name] | **Platform:** [Platform/OS]
**Objective:** [1-sentence summary of the task]

---

### Prerequisites
- Access to **[App Name]** on **[Platform]**.
- [Any necessary initial state, e.g., Logged in]

---

### Step-by-Step Instructions

1. **[Action Headline]**
   [Direct instruction combining related micro-actions.] |Image X| *(if applicable)*

2. **[Action Headline]**
   [Next instruction...]

---
> **Note:** [Optional callout for warnings/non-obvious behavior. Omit section if not needed.]

{"### USER INSTRUCTIONS:" + u_notes if u_notes else ""}

### INPUT DATA:
**Raw Logs:**
{rs}
"""

    print("==========Compiling ScreenShot Data==========\n")
    res=ContactAI(cp2,None,cm2,API_KEY)
    
    if not res:
        print("Compiling Failed Try Again Later")
        sys.exit(1)

    # st2 = gt.replace(" ","_")
    st2=re.sub(r'[\\/:*?"<>|]',"_",title).strip() or "Guide"
    
    fp2=os.path.join(bp,"Output",st2)
    fgp=os.path.join(fp2,f"{st2}.md")
    os.mkdir(fp2) if not os.path.exists(fp2) else None

    if imgM.strip().lower() in ["yes","y","true","1"]:
        nfp=[]

        for idx,f in enumerate(fl):

            fn,ext=os.path.splitext(f)
            dest=os.path.join(fp2,f"{idx}{ext}")
            shutil.move(f,dest)
            
            nf=f"{idx}{ext}"
            nfp.append(nf)
        
        def rp(match):
            try:
                inum=int(match.group(1))
                ii=inum-1
                if 0<=ii<len(nfp):
                    return f"\n\n![Interaction {inum}]({nfp[ii]})\n\n"
            except(ValueError,IndexError):
                pass
            return ""
        
        fo=re.sub(r"\|Image\s*(\d+)\|",rp,res)
    else:
        fo=re.sub(r"\|Image\s*\d+\|","",res)

    print("stored File, Embedded Screenshots")
    with open(fgp,"w") as g:
        g.write(fo)
    print("============Completed Compilation============")

    # print("cleaning up temp files")
    print("Wiping Out tmp folder.")
    for fn in os.listdir(tp):
        fpp=os.path.join(tp,fn)
        if os.path.isfile(fpp):
            os.unlink(fpp)
    print(f"Your Guide is At {fp2}")
    print("=================Done, Enjoy!================")


if __name__=="__main__":
    main()
