from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_text_list(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Missing required vocab file: {path}. "
            "Update paths in generator/settings.py to point at your input data."
        )

    items: list[str] = []
    with p.open("r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            items.append(s)

    if not items:
        raise ValueError(f"Vocab file is empty after removing blank lines: {path}")
    return items


def read_json(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Missing required JSON file: {path}. "
            "Update paths in generator/settings.py to point at your input data."
        )

    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_state_region_mapping(obj: Any) -> dict[str, str]:
    if isinstance(obj, dict):
        # Shape 1: {"CA": "West", ...}
        if all(isinstance(k, str) and isinstance(v, str) for k, v in obj.items()):
            return dict(obj)

        # Shape 2: {"states": [{"state": "CA", "region": "West"}, ...]}
        states = obj.get("states")
        if isinstance(states, list):
            mapping: dict[str, str] = {}
            for entry in states:
                if not isinstance(entry, dict):
                    continue
                st = entry.get("state")
                rg = entry.get("region")
                if isinstance(st, str) and isinstance(rg, str):
                    mapping[st] = rg
            if mapping:
                return mapping

    raise ValueError(
        "Invalid states/regions JSON. Supported shapes: "
        "(1) {\"CA\": \"West\", ...} "
        "(2) {\"states\": [{\"state\": \"CA\", \"region\": \"West\"}, ...]}"
    )
