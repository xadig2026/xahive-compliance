from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    pdf_path = Path(r"C:\xahive compliance Project\resources\NIST_CSF_2.0_Compliance_QA.pdf")
    items_path = Path(r"C:\xahive compliance Project\coding\backend\modules\nist_csf_2_0\items.json")

    items = json.loads(items_path.read_text(encoding="utf-8"))
    have = {it["id"] for it in items}

    reader = PdfReader(str(pdf_path))
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    ids = set(re.findall(r"\b(?:GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{2}\b", all_text))
    missing = sorted(ids - have)
    extra = sorted(have - ids)

    print("unique_in_pdf", len(ids))
    print("unique_in_items", len(have))
    print("missing", len(missing))
    for m in missing:
        print("  ", m)
    print("extra", len(extra))
    for e in extra[:10]:
        print("  ", e)


if __name__ == "__main__":
    main()

