from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def main() -> None:
    p = Path(r"C:\xahive compliance Project\coding\backend\modules\nist_csf_2_0\items.json")
    items = json.loads(p.read_text(encoding="utf-8"))
    ids = [it["id"] for it in items]
    print("count", len(items))
    print("dupes", len(ids) - len(set(ids)))
    c = Counter(i.split(".")[0] for i in ids)
    print("by_func", dict(c))


if __name__ == "__main__":
    main()

