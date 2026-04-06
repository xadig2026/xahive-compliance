"""
Compact, model-facing facts for narratives — only scores, statuses, and question text.
"""

from __future__ import annotations

from typing import Any

from app.scoring.readiness import build_readiness


def build_narrative_facts(module_id: str, items: list[dict[str, Any]], responses: dict[str, Any]) -> dict[str, Any]:
    """Single source of truth: derived from the same readiness engine as /readiness."""
    r = build_readiness(module_id, items, responses)
    controls: list[dict[str, Any]] = []
    for row in r["by_item"]:
        controls.append(
            {
                "control_id": row["item_id"],
                "function": row["function"],
                "category": row.get("category") or "",
                "question": (row.get("question") or "")[:800],
                "status": row.get("status", "NotStarted"),
                "readiness_percent": row.get("readiness_percent"),
                "included_in_rollup": row.get("included_in_rollup", True),
            }
        )

    fn_order = [x["function"] for x in r["by_function"]]

    return {
        "module_id": module_id,
        "overall": r["overall"],
        "by_function": r["by_function"],
        "function_order": fn_order,
        "controls": controls,
    }
