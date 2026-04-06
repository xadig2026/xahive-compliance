"""
Drop narrative bullets that cite unknown control IDs or omit required [CONTROL_ID] tags.
"""

from __future__ import annotations

import re
from typing import Any

_BRACKETS = re.compile(r"\[([^\]]+)\]")


def allowed_control_ids(facts: dict[str, Any]) -> set[str]:
    return {c["control_id"] for c in facts.get("controls", []) if c.get("control_id")}


def filter_grounded_bullets(bullets: list[str], allowed: set[str]) -> list[str]:
    out: list[str] = []
    for b in bullets:
        if not b or not isinstance(b, str):
            continue
        found = [x.strip() for x in _BRACKETS.findall(b)]
        if not found:
            continue
        if not all(x in allowed for x in found):
            continue
        out.append(b.strip())
    return out


def apply_grounding_to_narrative_block(
    block: dict[str, Any],
    allowed: set[str],
) -> dict[str, Any]:
    return {
        "strengths": filter_grounded_bullets(block.get("strengths") or [], allowed),
        "weaknesses": filter_grounded_bullets(block.get("weaknesses") or [], allowed),
        "priorities": filter_grounded_bullets(block.get("priorities") or [], allowed),
    }
