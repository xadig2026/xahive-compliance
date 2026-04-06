from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def extract_items_from_text(text: str) -> list[dict]:
    """
    Extracts items as:
      - id: e.g., GV.OC-01
      - question: line starting with Q<number>:
      - practices: bullet list under the question (checkbox candidates)
    Also attempts to keep current function/category context from headings like:
      GOVERN (GV)
      GV.OC — Organizational Context
    """
    func_map = {
        "GV": "GOVERN",
        "ID": "IDENTIFY",
        "PR": "PROTECT",
        "DE": "DETECT",
        "RS": "RESPOND",
        "RC": "RECOVER",
    }

    # Break into lines for simple state machine parsing.
    lines = [normalize_space(l) for l in text.splitlines()]
    lines = [l for l in lines if l]

    current_function = None
    current_category = None

    items: list[dict] = []

    subcat_re = re.compile(r"^(?P<id>(GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{2})\b")
    func_re = re.compile(r"^(GOVERN|IDENTIFY|PROTECT|DETECT|RESPOND|RECOVER)\s+\(([A-Z]{2})\)")
    cat_re = re.compile(r"^(?P<cat>(GV|ID|PR|DE|RS|RC)\.[A-Z]{2})\s+—\s+(?P<name>.+)$")
    q_re = re.compile(r"^Q\d+:\s+(?P<q>.+)$")
    bullet_re = re.compile(r"^[•\-\u2022]\s+(?P<t>.+)$")

    pending_id: str | None = None
    collecting_for: dict | None = None
    pending_bullet: str | None = None

    for line in lines:
        mfunc = func_re.match(line)
        if mfunc:
            code = mfunc.group(2)
            current_function = func_map.get(code, mfunc.group(1))
            continue

        mcat = cat_re.match(line)
        if mcat:
            current_category = mcat.group("cat")
            continue

        msub = subcat_re.match(line)
        if msub:
            # finalize any pending bullet for prior item
            if collecting_for and pending_bullet:
                collecting_for["practices"].append(pending_bullet)
                pending_bullet = None
            pending_id = msub.group("id")
            collecting_for = None
            continue

        mq = q_re.match(line)
        if mq and pending_id:
            collecting_for = {
                "id": pending_id,
                "function": current_function or pending_id.split(".")[0],
                "category": current_category or pending_id.split("-")[0],
                "question": mq.group("q"),
                "practices": [],
            }
            items.append(collecting_for)
            pending_id = None
            pending_bullet = None
            continue

        # collect practices (bullets) for current item
        if collecting_for:
            mb = bullet_re.match(line)
            if mb:
                if pending_bullet:
                    collecting_for["practices"].append(pending_bullet)
                pending_bullet = mb.group("t")
                continue
            # continuation line for previous bullet (wrapped text)
            if pending_bullet and not (
                func_re.match(line) or cat_re.match(line) or subcat_re.match(line) or q_re.match(line)
            ):
                pending_bullet = f"{pending_bullet} {line}"
                continue
            # end of bullet block
            if pending_bullet:
                collecting_for["practices"].append(pending_bullet)
                pending_bullet = None

    if collecting_for and pending_bullet:
        collecting_for["practices"].append(pending_bullet)

    return items


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    modules_root = repo_root / "modules"
    module_id = "nist_csf_2_0"
    module_dir = modules_root / module_id
    module_dir.mkdir(parents=True, exist_ok=True)

    # Default location: sibling resources folder next to coding/ (user workspace).
    pdf_path = Path(r"C:\xahive compliance Project\resources\NIST_CSF_2.0_Compliance_QA.pdf")
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found at {pdf_path}")

    reader = PdfReader(str(pdf_path))
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    items = extract_items_from_text(all_text)

    # Deduplicate by id if parsing repeats.
    dedup: dict[str, dict] = {}
    for it in items:
        dedup[it["id"]] = it
    items = [dedup[k] for k in sorted(dedup.keys())]

    meta = {
        "id": module_id,
        "name": "NIST CSF 2.0 (Checklist)",
        "version": "2024-02",
        "source": {
            "primary": "NIST CSWP 29 (February 2024)",
            "derivative": "NIST CSF 2.0 Compliance Q&A PDF (resources)",
        },
        "item_count": len(items),
    }

    (module_dir / "module.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (module_dir / "items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")

    print(f"Wrote {len(items)} items to {module_dir}")


if __name__ == "__main__":
    main()

