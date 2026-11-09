pt="""
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
vision_prompt_text=pt
