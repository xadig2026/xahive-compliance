from __future__ import annotations

import json
import os
import sys

import httpx


BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
if len(sys.argv) > 1:
    BASE = sys.argv[1]


def main() -> None:
    mods = httpx.get(f"{BASE}/api/modules", timeout=10).json()
    assert mods, "No modules returned"
    module_id = mods[0]["id"]

    meta = httpx.get(f"{BASE}/api/modules/{module_id}", timeout=10).json()
    assert meta.get("id") == module_id

    items = httpx.get(f"{BASE}/api/modules/{module_id}/items", timeout=30).json()
    assert items, "No items"

    print(json.dumps({"module_id": module_id, "item_count": len(items)}, indent=2))


if __name__ == "__main__":
    main()
