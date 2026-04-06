from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModuleInfo:
    id: str
    name: str
    version: str


class ModuleLoader:
    def __init__(self, modules_root: Path):
        self.modules_root = modules_root

    def list_modules(self) -> list[ModuleInfo]:
        out: list[ModuleInfo] = []
        if not self.modules_root.exists():
            return out
        for module_dir in sorted([p for p in self.modules_root.iterdir() if p.is_dir()]):
            meta_path = module_dir / "module.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            out.append(ModuleInfo(id=meta["id"], name=meta["name"], version=meta["version"]))
        return out

    def get_module_meta(self, module_id: str) -> dict:
        module_dir = self.modules_root / module_id
        meta_path = module_dir / "module.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Module not found: {module_id}")
        return json.loads(meta_path.read_text(encoding="utf-8"))

    def get_items(self, module_id: str) -> list[dict]:
        module_dir = self.modules_root / module_id
        items_path = module_dir / "items.json"
        if not items_path.exists():
            raise FileNotFoundError(f"Items not found for module: {module_id}")
        return json.loads(items_path.read_text(encoding="utf-8"))

