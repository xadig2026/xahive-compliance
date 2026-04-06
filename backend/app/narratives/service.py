"""
Orchestrate narrative generation: OpenAI (deterministic settings) with grounding validation,
falling back to template text when the key is missing or output fails validation.
"""

from __future__ import annotations

import os
import traceback
from typing import Any

from app.narratives.facts import build_narrative_facts
from app.narratives.template_narrative import build_template_narratives
from app.narratives.validate import allowed_control_ids, apply_grounding_to_narrative_block


def _trim_block(block: dict[str, Any]) -> dict[str, Any]:
    """Cap list lengths so UI and LLM stay aligned (3 weaknesses / priorities, 5 strengths)."""
    return {
        "strengths": (block.get("strengths") or [])[:5],
        "weaknesses": (block.get("weaknesses") or [])[:3],
        "priorities": (block.get("priorities") or [])[:3],
    }


def _trim_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out = {
        "overall": _trim_block(payload.get("overall") or {}),
        "sections": [],
    }
    for s in payload.get("sections") or []:
        fn = s.get("function")
        tb = _trim_block(s)
        out["sections"].append({"function": fn, **tb})
    return out


def _merge_block(
    grounded: dict[str, list[str]],
    fallback: dict[str, list[str]],
) -> dict[str, list[str]]:
    """If a list is empty after grounding, use deterministic template lines."""
    out = {}
    for key in ("strengths", "weaknesses", "priorities"):
        g = grounded.get(key) or []
        if g:
            out[key] = g
        else:
            out[key] = fallback.get(key) or []
    return out  # type: ignore[return-value]


def _align_sections(
    llm_sections: list[dict[str, Any]],
    facts: dict[str, Any],
    template_sections: list[dict[str, Any]],
    allowed: set[str],
) -> list[dict[str, Any]]:
    order = facts.get("function_order") or []
    by_fn: dict[str, dict[str, Any]] = {s.get("function"): s for s in llm_sections if s.get("function")}
    out: list[dict[str, Any]] = []
    tmpl_by_fn = {s.get("function"): s for s in template_sections}

    for fn in order:
        raw = by_fn.get(fn, {"function": fn, "strengths": [], "weaknesses": [], "priorities": []})
        tmpl = tmpl_by_fn.get(fn, {"strengths": [], "weaknesses": [], "priorities": []})
        grounded = apply_grounding_to_narrative_block(raw, allowed)
        merged = _merge_block(grounded, tmpl)
        out.append({"function": fn, **merged})
    return out


def generate_readiness_narratives(
    module_id: str,
    items: list[dict[str, Any]],
    responses: dict[str, Any],
) -> dict[str, Any]:
    facts = build_narrative_facts(module_id, items, responses)
    template = build_template_narratives(facts)
    allowed = allowed_control_ids(facts)

    source = "template"
    error_detail: str | None = None
    llm_raw: dict[str, Any] | None = None

    use_llm = os.environ.get("OPENAI_API_KEY", "").strip() != ""
    if use_llm:
        try:
            from app.narratives.openai_narrative import call_openai_narratives

            llm_raw = call_openai_narratives(facts)
            source = "openai"
        except Exception:
            error_detail = traceback.format_exc()
            llm_raw = None
            source = "template"

    if not llm_raw:
        trimmed = _trim_payload({"overall": template["overall"], "sections": template["sections"]})
        return {
            "overall": trimmed["overall"],
            "sections": trimmed["sections"],
            "meta": {
                "source": source,
                "error": (error_detail[:500] + "…") if error_detail and len(error_detail) > 500 else error_detail,
            },
        }

    overall_g = apply_grounding_to_narrative_block(llm_raw.get("overall") or {}, allowed)
    overall_final = _merge_block(overall_g, template["overall"])

    sections_final = _align_sections(
        list(llm_raw.get("sections") or []),
        facts,
        template["sections"],
        allowed,
    )

    trimmed = _trim_payload({"overall": overall_final, "sections": sections_final})
    return {
        "overall": trimmed["overall"],
        "sections": trimmed["sections"],
        "meta": {
            "source": "openai_validated",
            "model": os.environ.get("OPENAI_NARRATIVE_MODEL", "gpt-4o-mini"),
        },
    }


def grounded_only(
    facts: dict[str, Any],
    block: dict[str, Any],
) -> dict[str, list[str]]:
    """Utility: filter a block without template merge (tests)."""
    allowed = allowed_control_ids(facts)
    return apply_grounding_to_narrative_block(block, allowed)
