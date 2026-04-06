"""
Per-question score 0–5 and readiness rollups (overall + CSF Function).

Not applicable: excluded entirely from scoring — no points earned, no points
possible, and not counted in any readiness percentage (overall or by function).
Those rows are still listed in by_item for transparency.
"""

from __future__ import annotations

from typing import Any


def _is_not_applicable(resp: dict[str, Any] | None) -> bool:
    if not resp:
        return False
    status = resp.get("status")
    if not isinstance(status, str):
        return False
    return status.strip() == "NotApplicable"


def _count_checks(item: dict[str, Any], checks: dict[str, bool] | None) -> tuple[int, int]:
    practices = item.get("practices") or []
    n = len(practices)
    if n == 0:
        return 0, 0
    c = checks or {}
    done = sum(1 for i in range(n) if c.get(str(i)))
    return done, n


def score_item_points(item: dict[str, Any], resp: dict[str, Any] | None) -> tuple[float | None, float, bool]:
    """
    (earned, possible, included_in_rollup).

    Not applicable: (None, 0.0, False) — ignored for all totals and percentages.
    """
    if not resp:
        return 0.0, 5.0, True

    if _is_not_applicable(resp):
        return None, 0.0, False

    status = resp.get("status") or "NotStarted"

    if status == "Implemented":
        return 5.0, 5.0, True

    if status == "NotStarted":
        return 0.0, 5.0, True

    done, n = _count_checks(item, resp.get("checks"))
    attested = bool(resp.get("attested"))

    if n == 0:
        return (4.0 if attested else 0.0), 5.0, True

    ratio = done / n
    if done == 0:
        return 0.0, 5.0, True

    raw = 5.0 * ratio
    if done >= n:
        return min(4.0, raw), 5.0, True
    earned = max(1.0, min(4.0, round(raw * 2) / 2))
    return earned, 5.0, True


def build_readiness(module_id: str, items: list[dict[str, Any]], responses: dict[str, Any]) -> dict[str, Any]:
    by_item: list[dict[str, Any]] = []
    fn_stats: dict[str, dict[str, float | int]] = {}

    points_earned = 0.0
    points_possible = 0.0
    not_applicable_questions = 0

    for item in items:
        iid = item["id"]
        resp = responses.get(iid)
        earned, possible, included = score_item_points(item, resp)
        fn = item.get("function") or "Other"

        if fn not in fn_stats:
            fn_stats[fn] = {"earned": 0.0, "possible": 0.0, "na": 0, "total": 0}
        fn_stats[fn]["total"] += 1
        if earned is None:
            fn_stats[fn]["na"] += 1
            not_applicable_questions += 1
        elif included:
            fn_stats[fn]["earned"] += earned
            fn_stats[fn]["possible"] += possible
            points_earned += earned
            points_possible += possible

        item_pct = None
        if earned is not None:
            item_pct = round(100.0 * float(earned) / 5.0, 1)

        by_item.append(
            {
                "item_id": iid,
                "function": fn,
                "category": item.get("category"),
                "question": item.get("question") or "",
                "score": earned,
                "max_score": 5.0 if included else None,
                "readiness_percent": item_pct,
                "included_in_rollup": included,
                "status": (resp or {}).get("status", "NotStarted"),
            }
        )

    by_function: list[dict[str, Any]] = []
    for fn in sorted(fn_stats.keys()):
        s = fn_stats[fn]
        pe = float(s["earned"])
        pp = float(s["possible"])
        pct = (100.0 * pe / pp) if pp > 0 else None
        by_function.append(
            {
                "function": fn,
                "question_count": int(s["total"]),
                "not_applicable_count": int(s["na"]),
                "points_earned": round(pe, 2),
                "points_possible": round(pp, 2),
                "readiness_percent": round(pct, 1) if pct is not None else None,
            }
        )

    overall_pct = (100.0 * points_earned / points_possible) if points_possible > 0 else None

    return {
        "module_id": module_id,
        "overall": {
            "readiness_percent": round(overall_pct, 1) if overall_pct is not None else None,
            "points_earned": round(points_earned, 2),
            "points_possible": round(points_possible, 2),
            "applicable_questions": int(round(points_possible / 5.0)) if points_possible else 0,
            "not_applicable_questions": not_applicable_questions,
        },
        "by_function": by_function,
        "by_item": by_item,
    }
