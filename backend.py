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
import urllib.request
import urllib.error
import json
import base64
import shutil
import concurrent
import re
import time


def ContactAI(prompt_text, img, ModelList, api_key):
    MODEL_IDX=0
    Last_UNCLEAR=False
    for _ in range(15):
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
        req.add_header('Authorization', f'Bearer {api_key}')
        req.add_header('Content-type', 'application/json')
        req.add_header('HTTP-Referer', 'https://localhost')
        req.add_header('X-title', 'UI_Analyzer_Script')
        
        try:
            response = urllib.request.urlopen(req)
            raw_body = response.read().decode('utf-8')
            
            if not raw_body:
                print(f"Empty response from {ModelList[MODEL_IDX]}")
                MODEL_IDX += 1
                continue
                
            result = json.loads(raw_body)
            
            if not result or 'error' in result:
                err_msg = result.get('error', {}).get('message', 'Unknown Error') if isinstance(result, dict) else 'Invalid JSON'
                print(f"API Error from {ModelList[MODEL_IDX]}: {err_msg}")
                MODEL_IDX += 1
                continue
            message_choice = result.get('choices', [{}])[0].get('message', {})
            content = message_choice.get('content') if message_choice else None
            
            if content is None:
                print(f"Model {ModelList[MODEL_IDX]} returned null content, retrying...")
                MODEL_IDX += 1
                continue

            if "Unclear" in content:
                print("Model Unable to Extract Data, Trying Again")
                if Last_UNCLEAR:
                    return content
                Last_UNCLEAR = True
                continue
                
            return content

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f'Model {ModelList[MODEL_IDX]} failed with HTTP {e.code}: {error_body}')
            MODEL_IDX += 1
            time.sleep(1)
        except Exception as e:
            print(f'Connecting Failed with Error {e}')
            MODEL_IDX += 1
            time.sleep(1)
    else:
        return None
def main():
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
    "google/gemma-4-26b-a4b-it:free",
    "minimax/minimax-m3:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
    ]
    prompt_text = """
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
        
    raw_steps=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(lambda image: ContactAI(prompt_text, image, MODEL_LIST, API_KEY), data)
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
        

    COMPILE_MODEL=["nvidia/nemotron-3-ultra-550b-a55b:free","nvidia/nemotron-3-ultra-550b-a55b:free","nvidia/nemotron-3-super-120b-a12b:free"]
    compile_prompt = f"""
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
5. **Image Placement:** User's image preference is "{Image_Mode}". If enabled, append `|Image N|` at the end of a step, where N is the ORIGINAL "Interaction N" number from the logs it was derived from (use the first number if multiple were merged).

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
    result=ContactAI(compile_prompt,None,COMPILE_MODEL, API_KEY)
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


if __name__ == "__main__":
    main()
