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
prompt_text = ("""
URGENT VISUAL DIRECTIVE: Look strictly at the location of the MOUSE CURSOR or RED CIRCLE/BOX in this screenshot. Ignore the rest of the page.

Analyze the specific UI element being hovered, highlighted, or clicked. If it's a text input, assume the user is pressing Enter.

Reply EXACTLY in this plain text key-value format. Do not use Markdown, JSON, or introductory sentences.

Application: [App/Website Name or 'Unidentified']
Platform/Environment: [Web / Desktop / Mobile]
Interaction Marker: [Mouse Cursor / Red Box / None]
Target Element Type: [Button / Text Field / Sidebar / Tab / Icon]
Exact Element Text: "[Exact text on the element, or '[Icon: name]' if none]"
Element Location: [Top-right, Left sidebar, Center, etc.]
Action: [What clicking/entering this does]
Raw Step Summary: [A single sentence summary, e.g., "User clicks the 'Save' button in the settings menu."]
""")
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
You are a Senior Technical Writer. Convert the provided raw UI interaction logs into a concise, meticulously formatted Markdown User Guide.

### CORE RULES & FORMATTING:
1. **Pristine Markdown:** Emphasize clean structure, spacing, and readability. ALWAYS **bold** exact UI elements (e.g., click **Settings**).
2. **Smart Compression:** Assume basic user competency. Group micro-steps into single logical actions (e.g., instead of "click search, type query, hit enter," use "Search for [Query]"). Include obvious missing precursors (e.g., "Navigate to Website X").
3. **Ruthless Conciseness:** Write in direct, professional imperative tone. Zero conversational filler. Keep spatial directions minimal unless necessary.
4. **Strict Accuracy:** Use the exact spelling and capitalization of UI elements provided in the logs. Do not invent unperformed actions.
5. **Image Placement:** The user's image preference is: "{Image_Mode}". If opted in, append pointers like `|Image 1|` at the end of the corresponding step (matching the raw data interaction number).

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
   [Single, direct instruction combining related micro-actions. e.g., "In the left sidebar, click **Settings**."] |Image X| *(if applicable)*

2. **[Action Headline]**  
   [Next logical instruction...]

---
> **Note:** [Optional short callout for warnings or non-obvious behavior derived from logs. Omit if unnecessary.]

{"### USER INSTRUCTIONS:" + USER_NOTES if USER_NOTES.strip() else ""}

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