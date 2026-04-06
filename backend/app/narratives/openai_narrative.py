"""
OpenAI Chat Completions with JSON schema (strict), temperature 0, and optional seed.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Strict JSON Schema for Structured Outputs (all keys required; no extras).
NARRATIVE_JSON_SCHEMA: dict[str, Any] = {
    "name": "readiness_narratives",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "overall": {
                "type": "object",
                "properties": {
                    "strengths": {
                        "type": "array",
                        "maxItems": 5,
                        "items": {"type": "string", "maxLength": 650},
                    },
                    "weaknesses": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {"type": "string", "maxLength": 650},
                    },
                    "priorities": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {"type": "string", "maxLength": 650},
                    },
                },
                "required": ["strengths", "weaknesses", "priorities"],
                "additionalProperties": False,
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "function": {"type": "string"},
                        "strengths": {
                            "type": "array",
                            "maxItems": 5,
                            "items": {"type": "string", "maxLength": 650},
                        },
                        "weaknesses": {
                            "type": "array",
                            "maxItems": 3,
                            "items": {"type": "string", "maxLength": 650},
                        },
                        "priorities": {
                            "type": "array",
                            "maxItems": 3,
                            "items": {"type": "string", "maxLength": 650},
                        },
                    },
                    "required": ["function", "strengths", "weaknesses", "priorities"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["overall", "sections"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = """You write short cybersecurity readiness commentary for an internal checklist report.

Hard rules (violations are unacceptable):
1) Use ONLY information in the FACTS_JSON object. Do not invent vendors, products, incidents, regulations, team names, or controls not present there.
2) Every bullet string MUST contain one or more control identifiers in square brackets copied exactly from FACTS_JSON, e.g. [DE.AE-02]. Only use control_ids listed under "controls".
3) Do not state percentages or statuses unless they appear for that control in FACTS_JSON.
4) strengths: only for controls that show strong readiness (e.g. Implemented or high readiness_percent). At most 5 bullets.
5) weaknesses: at most 3 bullets. Each bullet MUST name the CSF function and category from FACTS_JSON (e.g. "DETECT · DE.AE") and briefly reflect the question text — not only the control_id. Only the weakest-gap controls.
6) priorities: at most 3 bullets, aligned to the same weakest controls as weaknesses where possible; include function, category, and question context; cite [CONTROL_ID].
7) overall: synthesize across the whole module using the same citation rules (max 5 strengths, max 3 weaknesses, max 3 priorities).
8) sections: produce exactly one object per function name listed in "function_order", in that order, with "function" matching exactly.
9) Keep each bullet one sentence where possible.
10) If there is insufficient evidence for a list, return an empty array for that list."""


def call_openai_narratives(facts: dict[str, Any]) -> dict[str, Any]:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("OPENAI_NARRATIVE_MODEL", "gpt-4o-mini").strip()
    client = OpenAI(api_key=api_key)

    user_payload = {
        "FACTS_JSON": facts,
        "instructions": "Return JSON only. Follow the system rules exactly.",
    }

    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": NARRATIVE_JSON_SCHEMA,
        },
    }
    seed = os.environ.get("OPENAI_NARRATIVE_SEED", "").strip()
    if seed.isdigit():
        kwargs["seed"] = int(seed)

    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("Empty completion")
    return json.loads(content)
