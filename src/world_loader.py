# world_loader.py
# 道·衍 - 世界設定載入與驗證

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import config


DEFAULT_ALLOWED_EVENTS = [
    "ATTACK",
    "MOVE",
    "TALK",
    "INSPECT",
    "USE_ITEM",
    "CULTIVATE",
    "REST",
    "SKILL_USE",
    "TRADE",
]


class WorldSettings:
    """統一載入 locations/npcs/events/items/skills 的輕量工具。"""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = Path(data_path) if data_path else config.DATA_PATH

        self.locations: List[Dict[str, Any]] = self._load_locations()
        self.npcs: List[Dict[str, Any]] = self._load_json_file("npcs.json", root_key="npcs")
        self.events: List[Dict[str, Any]] = self._load_json_file("events.json", root_key="events")
        self.items: List[Dict[str, Any]] = self._load_json_file("items.json", root_key="items")
        self.skills: List[Dict[str, Any]] = self._load_json_file("skills.json", root_key="skills")

        self.locations_by_id: Dict[str, Dict[str, Any]] = {loc["id"]: loc for loc in self.locations}
        self.npcs_by_id: Dict[str, Dict[str, Any]] = {npc["id"]: npc for npc in self.npcs if "id" in npc}
        self.events_by_location: Dict[str, Dict[str, Any]] = {
            e["location_id"]: e for e in self.events if e.get("location_id")
        }

        self._validate_references()

    def _load_json_file(self, filename: str, root_key: Optional[str] = None) -> List[Dict[str, Any]]:
        path = self.data_path / filename
        if not path.exists():
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[world_loader] 無法讀取 {filename}: {exc}")
            return []

        if root_key is None:
            if isinstance(data, list):
                return data
            return []

        return data.get(root_key, []) if isinstance(data, dict) else []

    def _load_locations(self) -> List[Dict[str, Any]]:
        raw_locations = self._load_json_file("locations.json", root_key="locations")
        return [self._apply_location_defaults(loc) for loc in raw_locations if isinstance(loc, dict)]

    def _apply_location_defaults(self, loc: Dict[str, Any]) -> Dict[str, Any]:
        loc = dict(loc)
        loc.setdefault("allowed_events", list(DEFAULT_ALLOWED_EVENTS))
        loc.setdefault("allowed_item_drops", [])
        loc.setdefault("allowed_npcs", loc.get("available_npcs", []))
        loc.setdefault("environment_tags", loc.get("features", []))
        loc.setdefault("tags", loc.get("features", []))
        loc.setdefault("lore_facts", [])
        loc.setdefault("can_invent_details", False)
        return loc

    def _validate_references(self):
        # locations id 唯一性
        if len(self.locations_by_id) != len(self.locations):
            print("[world_loader] ⚠️  發現重複的 location id，請檢查 locations.json")

        # npc 的 location_id 是否存在
        for npc in self.npcs:
            loc_id = npc.get("location_id")
            if loc_id and loc_id not in self.locations_by_id:
                print(f"[world_loader] ⚠️  NPC {npc.get('id')} 的 location_id '{loc_id}' 不存在於 locations")

        # events 的 location_id 是否存在
        for event in self.events:
            loc_id = event.get("location_id")
            if loc_id and loc_id not in self.locations_by_id:
                print(f"[world_loader] ⚠️  事件池 location_id '{loc_id}' 不存在於 locations")

        # treasures 物品是否存在
        item_ids = {item.get("id") or item.get("name") for item in self.items}
        for event in self.events:
            for treasure in event.get("treasures", []):
                name = treasure.get("item_id") or treasure.get("item_name")
                if name and name not in item_ids:
                    # 僅警告，不阻斷
                    print(f"[world_loader] ⚠️  事件池引用未知物品 '{name}'")

