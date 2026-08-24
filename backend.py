import os
import pathlib
import sys
try:
    from dotenv import load_dotenv
    if getattr(sys, "frozen", False):
        _dotenv_path = pathlib.Path(sys.executable).resolve().parent / ".env"
    else:
        _dotenv_path = pathlib.Path(__file__).resolve().parent / ".env"
    load_dotenv(_dotenv_path)
except ImportError:
    pass
import glob
import PIL
import urllib.request
import urllib.error
import json
import base64
import tqdm.auto as tqdm
import shutil
import datetime
import threading
import concurrent
import re
_img = os.environ.get("CUE_IMAGE_MODE")
Image_Mode = _img if _img is not None else "No"
_notes = os.environ.get("CUE_USER_NOTES")
USER_NOTES = _notes if _notes is not None else None
_title = os.environ.get("CUE_GUIDE_TITLE")
GUIDE_TITLE = _title if _title is not None else "Guide"
API_KEY=os.environ.get("OPENROUTER_API_KEY", "")
if getattr(sys, "frozen", False):
    BASE_PATH=pathlib.Path(sys.executable).resolve().parent
else:
    BASE_PATH=pathlib.Path(__file__).resolve().parent
TMP_PATH=os.path.join(BASE_PATH,"tmp")
GUIDE_PATH=os.path.join(TMP_PATH,"rawguide.txt")
if not os.path.exists(os.path.join(BASE_PATH,"Output")):
    os.mkdir(os.path.join(BASE_PATH,"Output"))
exts=["*.jpg", "*.png", "*.jpeg"]

filepaths = []
for ext in exts:
    filepaths.extend(glob.glob(os.path.join(TMP_PATH, ext)))

filepaths.sort()

data = []
for filepath in filepaths:
    with open(filepath, "rb") as f:
        data.append(base64.b64encode(f.read()).decode('utf-8'))
if len(data)<1:
    print("No ScreenShots were Available To be Loaded!")
    sys.exit()
print("==============Loaded Screenshots=============")
print(f"Working With {len(data)} Screenshots!\n")

print("Starting the Process of Guide Making.")
print("It Might take a While So just Sit back and Enjoy!")
MODEL_LIST=[
"google/gemma-4-31b-it:free",
"nvidia/nemotron-nano-12b-v2-vl:free", #Something Wrong with this Model Everytime its-> Connecting Failed with Error 'choices'
"google/gemma-4-26b-a4b-it:free",
"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
]
prompt_text = """
You are analyzing ONE screenshot. A click location is marked in ONE of two ways:

TYPE A — A synthetic marker: a perfectly round, solid, flat-colored RED DOT/CIRCLE drawn on top of the image. It has no text, no icon, no gradient — just a plain circle. This is NOT part of the real app UI.

TYPE B — A normal OS mouse cursor (small arrow/pointer icon), if no red dot exists.

STEP 1 — FIND THE MARKER:
- Scan for the plain red circle first. Do NOT confuse it with real red UI elements (buttons, error badges, notification dots, icons) — those usually have text, shading, or shape details. The synthetic marker is a flat, uniform circle only.
- If no such flat red circle exists anywhere, locate the normal mouse cursor arrow instead.
- If neither is visible, say so (see fallback below).

STEP 2 — IDENTIFY THE ELEMENT AT THE MARKER:
Look ONLY at the UI element directly under or touching the marker. Ignore all other parts of the screenshot.

STEP 3 — INTERPRET:
If the element is a text input, assume the user typed relevant text and pressed Enter.

Respond in EXACTLY this plain-text format. No markdown, no JSON, no extra sentences:

Application: <App/website name, or "Unidentified">
Marker Found: <Red Dot / Mouse Cursor / None>
Element Type: <Button / Text Field / Link / Icon / Tab / Menu Item / Checkbox / Other>
Element Text: <exact visible label/text, or "[Icon: short description]" if no text>
Element Location: <e.g. Top-left, Center, Bottom navbar>
Likely Action: <short phrase — what happens when this is used>
Step Summary: <one sentence, e.g. "User clicks the Save button in the top toolbar.">

If you cannot confidently find a marker or element, respond with only:
Element Type: Unclear
Step Summary: Unable to determine the action from this screenshot.
"""
def ContactAI(prompt_text,img,ModelList):
    MODEL_IDX=0
    for _ in range(5):
        MODEL_IDX=MODEL_IDX % len(ModelList)
        messages_content = [{"type": "text", "text": prompt_text}]
        if img:
            messages_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})
            
        ReqData = {
            "model": ModelList[MODEL_IDX],
            "messages": [{"role": "user", "content": messages_content}],
            "temperature": 0.05,
            "max_tokens": 300 if img else 4096
        }
        encoded_data = json.dumps(ReqData).encode('utf-8')
        req=urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",data=encoded_data)
        req.add_header('Authorization', f'Bearer {API_KEY}')
        req.add_header('Content-type', 'application/json')
        req.add_header('HTTP-Referer', 'https://localhost')
        req.add_header('X-title', 'UI_Analyzer_Script')
        
        try:
            response=urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            if 'error' in result:
                print(f"API Error from {ModelList[MODEL_IDX]}: {result['error'].get('message', 'Unknown Error')}")
                MODEL_IDX += 1
                continue
            return result['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f'Model {ModelList[MODEL_IDX]} failed with HTTP {e.code}: {error_body}')
            MODEL_IDX += 1
        except Exception as e:
            print(f'Connecting Failed with Error {e}')
            MODEL_IDX+=1
    else:
        return None
    
print("===========Connecting to the Model===========")
    
raw_steps=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(lambda image: ContactAI(prompt_text, image, MODEL_LIST), data)
    raw_results = list(results)
successful_count = sum(1 for r in raw_results if r)
if successful_count < (len(data) - 2):
    print("Many of the Screenshots could not be Described. Try again Later.")
    sys.exit(1)
with open(GUIDE_PATH, "w") as G:
    for idx, content in enumerate(raw_results):
        if content:
            G.write(f"Interaction {idx + 1}\n{content}\n\n")
print("====Completed ScreenShot Data Extraction!====")
with open(GUIDE_PATH,"r") as G:
    raw_steps=G.read()
    

COMPILE_MODEL=["nvidia/nemotron-3-ultra-550b-a55b:free"]
prompt_text = f"""
You are a Senior Technical Writer. Convert the raw UI-interaction logs below into a concise, well-formatted Markdown user guide.

### INPUT FORMAT NOTE:
Each raw log entry is one interaction with fields like Application, Marker Found, Element Type, Element Text, Element Location, Likely Action, Step Summary. Some entries may be marked "Unclear" (extraction failed) or "Unidentified" (app not recognized) — these come from an imperfect vision model. Treat them charitably: infer the likely intent from surrounding steps and context, but NEVER fabricate specific UI text/labels that weren't given. If a step is genuinely unusable, merge it silently into the previous or next step rather than leaving a broken/empty step in the guide.

### CORE RULES & FORMATTING:
1. **Pristine Markdown:** Clean structure and spacing. ALWAYS **bold** exact UI element text (e.g., click **Settings**), using the exact spelling/capitalization from "Element Text" — never invent or paraphrase UI labels.
2. **Smart Compression:** Merge consecutive micro-steps into one logical action if they're part of the same operation (e.g., clicking a search box + typing + pressing Enter becomes "Search for [X]"). Add an obvious missing precursor step if needed (e.g., "Navigate to [App]") based on the first entry's Application field.
3. **Continuity over literalism:** If an entry is "Unclear," do not create a step for it — infer from the previous and next confirmed steps whether it was a transition, and omit or merge instead of guessing wildly.
4. **Ruthless Conciseness:** Direct, professional, imperative tone. No filler, no meta-commentary about the source logs.
5. **Strict Accuracy:** Only use element names/text explicitly present in the logs.
6. **Image Placement:** User's image preference is "{Image_Mode}". If enabled, append `|Image N|` at the end of a step, where N is the ORIGINAL "Interaction N" number from the logs it was derived from (use the first number if multiple were merged).

### REQUIRED OUTPUT SCHEMA:

# {GUIDE_TITLE}

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

{"### USER INSTRUCTIONS:" + USER_NOTES if USER_NOTES else ""}

### INPUT DATA:
**Raw Logs:**
{raw_steps}
"""

print("==========Compiling ScreenShot Data==========\n")
result=ContactAI(prompt_text,None,COMPILE_MODEL)
if not result:
    print("Compiling Failed Try Again Later")
    sys.exit(1)

# I put Sanitization here just in case yk yk
safe_title = re.sub(r'[\\/:*?"<>|]', "_", GUIDE_TITLE).strip() or "Guide"
FINAL_PATH = os.path.join(BASE_PATH, "Output", safe_title)
FINAL_GUIDE_PATH = os.path.join(FINAL_PATH, f"{safe_title}.md")
os.mkdir(FINAL_PATH) if not os.path.exists(FINAL_PATH) else None
if Image_Mode.strip().lower() in ["yes", "y", "true", "1"]:
    NewFilePaths=[]
    for idx,filePath in enumerate(filepaths):
        filename,ext=os.path.splitext(filePath)
        dest=os.path.join(FINAL_PATH,f"{idx}{ext}")
        shutil.move(filePath,dest)
        new_filename = f"{idx}{ext}"
        NewFilePaths.append(new_filename)

    def replace_marker(match):
        try:
            interaction_num = int(match.group(1))
            img_idx = interaction_num - 1 
            if 0 <= img_idx < len(NewFilePaths):
                return f"\n\n![Interaction {interaction_num}]({NewFilePaths[img_idx]})\n\n"
        except (ValueError, IndexError):
            pass
        return ""

    final_output = re.sub(r"\|Image\s*(\d+)\|", replace_marker, result)
else:
    final_output = re.sub(r"\|Image\s*\d+\|", "", result)
print("stored File, Embedded Screenshots")
with open(FINAL_GUIDE_PATH, "w") as G:
    G.write(final_output)
print("============Completed Compilation============")


print("Wiping Out tmp folder.")
for filename in os.listdir(TMP_PATH):
    file_path = os.path.join(TMP_PATH, filename)
    if os.path.isfile(file_path):
        os.unlink(file_path)
print(f"Your Guide is At {FINAL_PATH}")
print("=================Done, Enjoy!================")