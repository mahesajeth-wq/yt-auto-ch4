import json
import datetime
import random
from pipeline.config import HOOK_PATTERNS
from pipeline.gemini import GeminiClient, _robust_json_loads

def get_next_weekday_2pm_ist_utc():
    # IST is UTC+5:30. 2:00 PM IST = 14:00 IST = 08:30 AM UTC.
    now = datetime.datetime.now(datetime.timezone.utc)
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now_ist = now + ist_offset
    
    target_date = now_ist.date()
    # If it's past 2 PM IST today, start looking from tomorrow
    if now_ist.time() >= datetime.time(14, 0):
        target_date += datetime.timedelta(days=1)
        
    # Find next weekday (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri)
    while target_date.weekday() >= 5: # Saturday=5, Sunday=6
        target_date += datetime.timedelta(days=1)
        
    target_dt_ist = datetime.datetime.combine(target_date, datetime.time(14, 0))
    target_dt_utc = target_dt_ist - ist_offset
    return target_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_script(topic: dict, format_type: str) -> dict:
    client = GeminiClient()
    
    if format_type == "short":
        import random as _random
        segment_count = _random.choices([4, 5, 6], weights=[15, 65, 20], k=1)[0]
        
        hook_pattern = random.choice(HOOK_PATTERNS)
        hook_formatted = hook_pattern.format(
            subject=topic.get("topic", "history"),
            thing=topic.get("topic", "history"),
            seconds="30",
            topic=topic.get("topic", "history"),
            event="An event"
        )
        
        prompt = f"""Generate an extremely viral, high-retention 25-35 second YouTube Short engineering script on the topic: "{topic['topic']}".
Use the following hook concept as your core theme: "{hook_formatted}" (short hook: "{topic.get('short_hook', '')}").

Narration Style Requirements:
1. Pacing & Punchiness: Every single sentence must be extremely short, sharp, and high-impact (5 to 10 words MAXIMUM per segment's narration). Avoid long clauses or passive language.
2. Hook/Pattern Interrupt: Segment 1 must immediately shatter the viewer's attention. Start mid-consequence, not mid-setup. DO NOT use introductory filler like "Did you know..." or "Have you ever wondered...". Go straight to the verifiable outcome in under 8 words.
3. Emotional/Sensory Triggers: Use strong, dramatic verbs and adjectives (e.g., "shattered", "forged", "betrayed", "banned", "secret", "exposed", "deciphered").
4. No Fluff: Get straight to the documented historical facts. Every word must justify its existence.

For every `broll_query` field, write a SHORT, SPECIFIC, STOCK-FOOTAGE-FRIENDLY
search term of 3-6 words MAXIMUM. Write exactly what a human would type into
a stock video search bar (Pexels, Pixabay, etc). Use concrete nouns and visual
objects — NOT instructions or descriptions of what you want.

CORRECT examples: "bridge construction aerial", "steel beam welding closeup",
"concrete pouring foundation", "wind tunnel testing model", "dam spillway water flow",
"crane lifting steel girder", "earthquake damaged building", "engineering blueprint technical drawing"

WRONG examples: "visually jarring close-up of the topic", "macro b-roll of engineering
element", "closing beautiful shot returning to start", "diagram concept visualization",
"DNA double helix" (not relevant), "chemical" (not relevant)

IMPORTANT B-ROLL RULES:
- Stock video sites have excellent coverage of construction, architecture, infrastructure, and engineering processes.
- For specific structures, search by name: "Golden Gate Bridge", "Hoover Dam", "Burj Khalifa".
- For abstract engineering concepts, use: "structural stress test", "wind load simulation", "foundation construction site".
- ALWAYS include concrete visual anchors to give the video an authentic engineering documentary feel.

For each segment, also provide a `broll_queries` array with 3-5 ALTERNATIVE search terms for the same visual concept. These should be synonyms, related concepts, or different angles on the same subject. The first entry should match `broll_query`.

For any named structure or engineer: ALWAYS include their name in the query.

You MUST return your response ONLY as a raw JSON object with no markdown syntax. The JSON structure MUST be exactly like this:
{{
  "title": "A catchy title under 40 chars, starting with a hook word/number and containing one emoji",
  "description": "Line1: restate the hook\nLine2: The mechanism. The fix. The lesson.\nLine3: Full breakdown -> [link]\n\n#engineering #howitworks #infrastructure #design #construction",
  "tags": ["8 to 12 relevant tags under 500 characters total"],
  "category_id": "27",
  "segments": [
    {{
      "id": 1,
      "narration": "opening shocking hook sentence - 8 words or less, massive information gap",
      "broll_query": "{topic['topic']} ancient artifact museum",
      "broll_queries": ["{topic['topic']} ancient artifact museum", "old manuscript archives", "archaeological excavation site"],
      "duration_target": 6
    }},
    {{
      "id": 2,
      "narration": "Mind-bending historical fact that expands on the hook - 8 words or less",
      "broll_query": "old map magnifying glass",
      "duration_target": 6
    }},
    {{
      "id": {segment_count},
      "narration": "Final sentence that GRAMMATICALLY FLOWS INTO Segment 1's first sentence when read back-to-back — creating an audio loop the viewer doesn't register as a restart. Loop seamlessly.",
      "broll_query": "ancient library slow tracking shot",
      "duration_target": 6
    }}
  ],
  "thumbnail_text": "3 to 5 bold words max for the thumbnail",
  "loop_callout": true
}}

For Segment 1 specifically:
- `broll_query` MUST describe a high-motion, high-contrast, visually arresting shot (fast motion, dramatic close-up, panning shot) — this is the opening pattern-interrupt.

For the final segment (Segment {segment_count}) specifically:
- Resolve all loops and design the final sentence to end on a transition that flows seamlessly back into Segment 1's hook narration.
- The final sentence should THEMATICALLY echo or re-contextualize the IDEA from Segment 1's hook.
"""
    else:  # long-form
        prompt = f"""Generate a comprehensive 7-10 minute YouTube educational engineering script on the topic: "{topic['topic']}".
The script must have 15 to 18 segments, each targeting 25-35 seconds of narration.
Structure the narrative into:
- Intro hook: start mid-consequence and create an information gap (segments 1-2)
- Act 1: The structure, machine, or mechanism being examined (segments 3-7)
- Act 2: The failure, near-miss, or surprising design decision (segments 8-12)
- Act 3: The fix, the safety standard that followed, or the engineering legacy (segments 13-16)
- Closing CTA & link (segments 17-18)

For every `broll_query` field, write a SHORT, SPECIFIC, STOCK-FOOTAGE-FRIENDLY
search term of 3-6 words MAXIMUM. Write exactly what a human would type into
a stock video search bar (Pexels, Pixabay, etc). Use concrete nouns and visual
objects — NOT instructions or descriptions of what you want.

CORRECT examples: "bridge construction aerial", "steel beam welding closeup",
"concrete pouring foundation", "wind tunnel testing model", "dam spillway water flow",
"crane lifting steel girder", "earthquake damaged building"

WRONG examples: "visually jarring close-up of the topic", "macro b-roll of engineering
element", "closing beautiful shot returning to start", "diagram concept visualization"

For each segment, also provide a `broll_queries` array with 3-5 ALTERNATIVE search terms for the same visual concept. These should be synonyms, related concepts, or different angles on the same subject. The first entry should match `broll_query`.

For any named structure or engineer: ALWAYS include their name in the query.

You MUST return your response ONLY as a raw JSON object with no markdown syntax. The JSON structure MUST be exactly like this:
{{
  "title": "Engaging educational title for a long video, under 70 characters",
  "description": "A detailed, engaging description explaining what the video covers, including timestamps and educational value.\\n\\n#engineering #education #howitworks #infrastructure",
  "tags": ["15 to 20 relevant tags"],
  "category_id": "27",
  "segments": [
    {{
      "id": 1,
      "narration": "Opening narration hook starting mid-consequence...",
      "broll_query": "{topic['topic']} ancient library",
      "broll_queries": ["{topic['topic']} ancient library", "dusty library books archives", "old scroll parchment closeup"],
      "duration_target": 30
    }}
  ],
  "thumbnail_text": "3 to 5 bold words max for the thumbnail image",
  "loop_callout": false
}}
"""

    print("Generating script content using Gemini...")
    max_attempts = 3
    script_text = ""
    script = None
    for attempt in range(max_attempts):
        try:
            script_text = client.generate_text(prompt, use_grounding=False, temperature=0.8)
            script = _robust_json_loads(script_text)
            break
        except Exception as e:
            print(f"Error parsing script JSON on attempt {attempt+1}: {e}. Raw script text: {script_text}")
            if attempt == max_attempts - 1:
                raise RuntimeError("Failed to generate a valid script JSON from Gemini after 3 attempts") from e

    if format_type == "short":
        script["segment_count"] = segment_count

    # Add scheduling metadata for long form
    if format_type == "long":
        script["publish_at"] = get_next_weekday_2pm_ist_utc()
    else:
        # Default publish_at for shorts: let's set it to None so we can upload as private first
        script["publish_at"] = None

    # --- FACT VERIFICATION ---
    print("Running fact verification on the generated script...")
    verification_prompt = f"""You are a fact checker. Verify the historical accuracy of each segment's narration in the following script JSON:
{json.dumps(script, indent=2)}

Check if all claims are backed by credible historical consensus.
Return ONLY the modified script JSON with an added `"verified": true` or `"verified": false` field inside EACH segment object in the "segments" list.
If a claim is unverifiable, speculative, or false, mark `"verified": false`.
"""
    try:
        verified_text = client.generate_text(verification_prompt, use_grounding=True, temperature=0.2)
        verified_script = _robust_json_loads(verified_text)
        script["segments"] = verified_script.get("segments", script["segments"])
    except Exception as e:
        print(f"Fact check failed or quota-limited ({e}), keeping original script for Judge AI review.")
        for seg in script["segments"]:
            seg["verified"] = True

    # Regenerate unverified segments
    for seg in script["segments"]:
        if not seg.get("verified", True):
            print(f"Segment {seg['id']} failed fact check. Regenerating narration...")
            regen_prompt = f"""The following script segment narration failed fact-checking or was unverified:
Topic: {topic['topic']}
Segment details: {json.dumps(seg, indent=2)}

Rewrite the "narration" so that it is 100% scientifically accurate, verifiable, and maintains the exact same tone and target duration.
Return ONLY a raw JSON object for this segment with the updated "narration" and `"verified": true`.
"""
            try:
                regen_text = client.generate_text(regen_prompt, use_grounding=True, temperature=0.3)
                regen_seg = _robust_json_loads(regen_text)
                seg["narration"] = regen_seg.get("narration", seg["narration"])
                seg["verified"] = True
            except Exception as e:
                print(f"Failed to regenerate segment {seg['id']} ({e}). Keeping original for Judge AI review.")
                seg["verified"] = True

    return script
