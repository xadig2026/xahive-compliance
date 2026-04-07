"""
Fully deterministic narratives — no LLM. Every sentence ends with [CONTROL_ID] from the assessment.
Weaknesses and priorities: top 3 lowest-readiness controls, with CSF function + category + question context.
"""

from __future__ import annotations

from typing import Any


def _inc(c: dict[str, Any]) -> bool:
    return bool(c.get("included_in_rollup"))


def _pct(c: dict[str, Any]) -> float | None:
    v = c.get("readiness_percent")
    return float(v) if v is not None else None


def _by_function(controls: list[dict[str, Any]], fn: str) -> list[dict[str, Any]]:
    return [c for c in controls if c.get("function") == fn]


def _truncate(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _section_label(c: dict[str, Any]) -> str:
    fn = (c.get("function") or "—").strip()
    cat = (c.get("category") or "—").strip()
    return f"{fn} · {cat}"


def _rank_by_lowest_readiness(applicable: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []
    for c in applicable:
        p = _pct(c)
        if p is None:
            continue
        scored.append((p, c))
    scored.sort(key=lambda x: x[0])
    return [c for _, c in scored]


def template_block_for_controls(controls: list[dict[str, Any]]) -> dict[str, list[str]]:
    applicable = [c for c in controls if _inc(c)]
    strengths: list[str] = []
    weaknesses: list[str] = []
    priorities: list[str] = []

    ranked = _rank_by_lowest_readiness(applicable)
    worst_three = ranked[:3]
    all_trivial = (
        len(worst_three) > 0
        and all(
            (_pct(c) or 0) >= 99.5 and (c.get("status") or "") == "Implemented" for c in worst_three
        )
    )

    for c in applicable:
        cid = c["control_id"]
        st = c.get("status") or "NotStarted"
        p = _pct(c)
        if p is None:
            continue
        if st == "Implemented" or p >= 85.0:
            q = _truncate(c.get("question") or "", 160)
            strengths.append(
                f'{_section_label(c)}: "{q}" — strong signal from status and score ({p}% readiness). [{cid}]'
            )

    if not all_trivial:
        for c in worst_three:
            cid = c["control_id"]
            st = c.get("status") or "NotStarted"
            p = _pct(c)
            if p is None:
                continue
            sec = _section_label(c)
            q = _truncate(c.get("question") or "", 160)
            weaknesses.append(
                f'Weakness in {sec}: "{q}" — {p}% readiness, status {st}. [{cid}]'
            )
            priorities.append(
                f'Priority for {sec}: "{q}" — advance this control (currently {p}% readiness) toward full implementation. [{cid}]'
            )

    return {
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:3],
        "priorities": priorities[:3],
    }


def build_template_narratives(facts: dict[str, Any]) -> dict[str, Any]:
    controls: list[dict[str, Any]] = list(facts.get("controls") or [])
    overall_controls = [c for c in controls if _inc(c)]

    overall = template_block_for_controls(overall_controls)

    sections_out: list[dict[str, Any]] = []
    for fn in facts.get("function_order") or []:
        fn_controls = _by_function(controls, fn)
        blk = template_block_for_controls(fn_controls)
        sections_out.append(
            {
                "function": fn,
                "strengths": blk["strengths"],
                "weaknesses": blk["weaknesses"],
                "priorities": blk["priorities"],
            }
        )

    return {"overall": overall, "sections": sections_out}
