# event_pools.py
# 道·衍 - 事件池系統

"""
事件池機制：為每個地點定義「允許發生的事件」
AI 只能從池中選擇，不能憑空創造

設計原則：
1. 每個地點有固定的 NPC 遭遇池
2. 每個地點有固定的物品掉落池
3. AI 只負責「描述」事件，不定義事件本身
"""

from typing import Dict, List, Any

from world_loader import WorldSettings


# 每個地點的事件池定義
EVENT_POOLS = {
    # 青雲門山腳（新手區）
    "qingyun_foot": {
        "npcs": [
            # 這裡沒有固定 NPC，玩家需要主動移動到其他地點
        ],
        "random_encounters": [
            # 隨機遭遇（低機率）
            {
                "type": "npc",
                "npc_id": None,  # 山腳沒有隨機遭遇
                "weight": 0.0,
            }
        ],
        "treasures": [
            # 可能發現的物品（修煉、查看周圍時）
            {
                "type": "item",
                "item_name": "靈草",
                "weight": 0.05,  # 5% 機率
                "tier_required": 1.0,
            }
        ],
        "events": [
            # 特殊事件（純環境描述，無 NPC）
            {
                "type": "scenery",
                "description": "遠處傳來鐘聲",
                "weight": 0.1,
            }
        ]
    },

    # 青雲門外門廣場
    "qingyun_plaza": {
        "npcs": [
            # 固定 NPC（總是在這裡）
            "npc_002_elder_chen",  # 陳長老
        ],
        "random_encounters": [
            {
                "type": "npc",
                "npc_id": "npc_004_disciple_red",  # 紅藝
                "weight": 0.3,  # 30% 遇到
                "tier_range": (1.0, 2.0),
            }
        ],
        "treasures": [
            {
                "type": "item",
                "item_name": "乾糧",
                "weight": 0.05,
            }
        ],
        "events": []
    },

    # 靈獸森林（危險區域）
    "wildlands_forest": {
        "npcs": [],  # 沒有固定 NPC
        "random_encounters": [
            {
                "type": "npc",
                "npc_id": "npc_003_beast_frostlion",  # 霜焰獅
                "weight": 0.2,
                "tier_range": (1.8, 2.5),
            }
        ],
        "treasures": [
            {
                "type": "item",
                "item_name": "靈藥",
                "weight": 0.1,
            },
            {
                "type": "item",
                "item_name": "獸皮",
                "weight": 0.15,
            }
        ],
        "events": []
    },

    # 青雲門主殿
    "qingyun_hall": {
        "npcs": [
            "npc_001_master_qingyun",  # 青雲門掌門
        ],
        "random_encounters": [],  # 主殿沒有隨機遭遇
        "treasures": [],  # 主殿不能隨便撿東西
        "events": []
    }
}

# 若有 JSON 定義則覆蓋內建事件池
try:  # pragma: no cover
    _world_settings = WorldSettings()
    if _world_settings.events_by_location:
        EVENT_POOLS = {
            loc_id: {
                "npcs": data.get("npcs", []),
                "random_encounters": data.get("random_encounters", []),
                "treasures": data.get("treasures", []),
                "events": data.get("events", []),
            }
            for loc_id, data in _world_settings.events_by_location.items()
        }
except Exception as exc:
    print(f"[event_pools] ⚠️  無法從 JSON 載入事件池，使用內建版本: {exc}")


def get_event_pool(location_id: str) -> Dict[str, Any]:
    """
    獲取指定地點的事件池

    Args:
        location_id: 地點 ID

    Returns:
        事件池字典，包含 npcs, random_encounters, treasures, events
    """
    return EVENT_POOLS.get(location_id, {
        "npcs": [],
        "random_encounters": [],
        "treasures": [],
        "events": []
    })


def get_available_npcs(location_id: str) -> List[str]:
    """
    獲取指定地點所有可能出現的 NPC ID

    Args:
        location_id: 地點 ID

    Returns:
        NPC ID 列表
    """
    pool = get_event_pool(location_id)

    npcs = pool.get("npcs", []).copy()

    # 添加隨機遭遇中的 NPC
    for encounter in pool.get("random_encounters", []):
        if encounter.get("type") == "npc" and encounter.get("npc_id"):
            npcs.append(encounter["npc_id"])

    return npcs


def get_available_items(location_id: str) -> List[str]:
    """
    獲取指定地點可能掉落的物品

    Args:
        location_id: 地點 ID

    Returns:
        物品名稱列表
    """
    pool = get_event_pool(location_id)

    items = []
    for treasure in pool.get("treasures", []):
        if treasure.get("type") == "item":
            items.append(treasure["item_name"])

    return items
