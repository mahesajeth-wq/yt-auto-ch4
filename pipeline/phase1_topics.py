import os
import json
from pipeline.config import TOPIC_LOG_SIZE, ENGINEERING_SUBCLUSTERS
from pipeline.gemini import GeminiClient, _robust_json_loads

def select_topic(format_type: str) -> dict:
    # ── 1. Load published topics log ─────────────────────────────────────────
    topic_log_path = "published_topics.json"
    if os.path.exists(topic_log_path):
        try:
            with open(topic_log_path, "r") as f:
                data = json.load(f)
                published = data.get("topics", [])
                subcluster_idx = data.get("subcluster_idx", 0)
                call_count = data.get("call_count", 0)
        except Exception as e:
            print(f"Warning: Failed to load published topics: {e}")
            published = []; subcluster_idx = 0; call_count = 0
    else:
        published = []; subcluster_idx = 0; call_count = 0

    recent_topics = published[-TOPIC_LOG_SIZE:]
    call_count += 1

    # ── 2. Determine subcluster + format rotation ────────────────────────────
    current_subcluster = ENGINEERING_SUBCLUSTERS[subcluster_idx % len(ENGINEERING_SUBCLUSTERS)]
    is_trending = (call_count % 5 == 0)

    topic_instruction = (
        f"Generate topics about how structures, machines, and infrastructure work, "
        f"and engineering failures or near-misses analyzed through their mechanism and fix. "
        f"Focus area: {current_subcluster}. "
        f"Default to failures with no human casualties (structural collapse without loss of life, "
        f"near-misses, design flaws caught before failure). "
        f"Only generate a casualty-involved case if explicitly flagged as part of the Yellow-tier rotation, "
        f"and frame it around the resulting safety standard or fix, not the event itself. "
        f"Avoid politically sensitive incidents like Chernobyl. "
        f"Rotate across six formats: mechanism deep-dive, failure case study, near-miss, ranked list, then-vs-now, ancient-vs-modern."
    )

    # ── 3. Build Gemini prompt ───────────────────────────────────────────────
    prompt = f"""{topic_instruction}

Sub-cluster focus for this batch: {current_subcluster}

CRITICAL: Do NOT suggest any topic similar to these recently published topics:
{json.dumps(recent_topics, indent=2)}

AVOID: biology, pet animals, modern politics, tragedy-centered framing, disaster clickbait.
FOCUS: how things work, engineering mechanisms, structural analysis, design fixes, infrastructure.

Return ONLY a raw JSON array of objects. No markdown, no preamble.
Each object must have exactly these fields:
- "topic": specific subject with a named fact, event, or document (e.g. "How the Citicorp Center's design flaw was secretly fixed at night for months")
- "short_hook": opening question or statement, 8 words or less, creates a strong information gap
- "hook_type": one of "curiosity_gap", "contrarian", "time_pressure", "self_identification", "narrative_pull"
- "for_format": "short", "long", or "both"
- "subcluster": the sub-cluster this belongs to (string)
"""

    print(f"[Phase1] Requesting topics — subcluster: {current_subcluster} | trending: {is_trending}")
    client = GeminiClient()
    response_text = client.generate_text(prompt, use_grounding=is_trending, temperature=0.75)

    try:
        topics_list = _robust_json_loads(response_text)
        if not isinstance(topics_list, list):
            raise ValueError("Response is not a JSON list")
    except Exception as e:
        print(f"Error parsing topics: {e}")
        topics_list = [
            {
                "topic": "How the Tacoma Narrows Bridge danced itself apart in 1940 and changed aerodynamic engineering",
                "short_hook": "This bridge collapsed in 47 seconds.",
                "hook_type": "curiosity_gap",
                "for_format": "both",
                "subcluster": current_subcluster
            }
        ]

    # ── 4. Pick first topic matching format_type ──────────────────────────────
    selected_topic = None
    for item in topics_list:
        if item.get("for_format", "both") in (format_type, "both"):
            selected_topic = item
            break
    if not selected_topic:
        selected_topic = topics_list[0]
        selected_topic["for_format"] = format_type

    print(f"[Phase1] Selected: {selected_topic['topic']}")

    # ── 5. Persist state ──────────────────────────────────────────────────────
    published.append(selected_topic["topic"])
    published = published[-TOPIC_LOG_SIZE:]
    next_subcluster_idx = (subcluster_idx + 1) % len(ENGINEERING_SUBCLUSTERS)

    with open(topic_log_path, "w") as f:
        json.dump({
            "topics": published,
            "subcluster_idx": next_subcluster_idx,
            "call_count": call_count
        }, f, indent=2)

    return selected_topic
