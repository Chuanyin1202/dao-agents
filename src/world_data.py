# world_data.py
# 道·衍 - 結構化世界地圖數據

"""
世界地圖數據結構

每個地點包含：
- id: 唯一標識符（用於存檔）
- name: 顯示名稱
- description: 環境描述
- tier_requirement: 最低境界要求
- exits: 可行方向 {direction: destination_id}
- event_chance: 隨機事件觸發機率（0.0-1.0）
- features: 特殊效果列表
- available_npcs: 可能遇到的 NPC ID 列表
"""

WORLD_MAP = {
    # 起點：青雲門山腳
    "qingyun_foot": {
        "id": "qingyun_foot",
        "name": "青雲門·山腳",
        "description": "青雲門的入口，石階蜿蜒而上，霧氣繚繞。遠處傳來弟子們修煉的聲音。",
        "tier_requirement": 1.0,  # 練氣期即可
        "exits": {
            "north": "qingyun_plaza",  # 往北 -> 外門廣場
            "east": "qingyun_herb",    # 往東 -> 靈草堂
        },
        "event_chance": 0.05,  # 5% 機率觸發事件
        "features": ["安全區域", "新手友善"],
        "available_npcs": ["npc_001_master_qingyun"],
    },

    # 核心區域：外門廣場
    "qingyun_plaza": {
        "id": "qingyun_plaza",
        "name": "青雲門·外門廣場",
        "description": "寬闊的練武場，外門弟子們在此切磋武藝。場中央立著一塊巨大的任務告示板。",
        "tier_requirement": 1.0,
        "exits": {
            "south": "qingyun_foot",   # 往南 -> 山腳
            "north": "qingyun_inner",  # 往北 -> 內門（需要築基期）
            "west": "qingyun_library", # 往西 -> 藏經閣（需要築基期）
        },
        "event_chance": 0.10,  # 人多，事件機率較高
        "features": ["可以切磋", "任務板"],
        "available_npcs": ["npc_002_elder_wang", "npc_003_disciple_li"],
    },

    # 商業區：靈草堂
    "qingyun_herb": {
        "id": "qingyun_herb",
        "name": "青雲門·靈草堂",
        "description": "藥香四溢的藥堂，架上擺滿了各種靈草和丹藥。一位白髮長老正在煉丹爐前專注工作。",
        "tier_requirement": 1.0,
        "exits": {
            "west": "qingyun_foot",    # 往西 -> 山腳
        },
        "event_chance": 0.02,  # 安靜的藥堂，事件少
        "features": ["可以購買丹藥", "可以學習煉丹"],
        "available_npcs": ["npc_004_herbalist_zhang"],
    },

    # 進階區域：藏經閣
    "qingyun_library": {
        "id": "qingyun_library",
        "name": "青雲門·藏經閣",
        "description": "古老的藏書樓，三層高的閣樓中收藏著宗門秘籍。空氣中瀰漫著古書的氣息。",
        "tier_requirement": 2.0,  # 需要築基期
        "exits": {
            "east": "qingyun_plaza",   # 往東 -> 外門廣場
        },
        "event_chance": 0.15,  # 秘籍之地，事件機率高
        "features": ["可以學習技能", "需要貢獻點", "靈氣濃郁"],
        "available_npcs": ["npc_005_librarian"],
    },

    # 進階區域：內門
    "qingyun_inner": {
        "id": "qingyun_inner",
        "name": "青雲門·內門",
        "description": "內門弟子的修煉聖地，靈氣濃度是外門的三倍。遠處可見幾座獨立的洞府。",
        "tier_requirement": 2.0,  # 需要築基期
        "exits": {
            "south": "qingyun_plaza",  # 往南 -> 外門廣場
        },
        "event_chance": 0.08,
        "features": ["靈氣濃度 +200%", "修煉速度加成"],
        "available_npcs": [],
    },

    # 野外區域：靈獸森林
    "wildlands_forest": {
        "id": "wildlands_forest",
        "name": "靈獸森林",
        "description": "青雲門外的密林，時常有低階靈獸出沒。樹木高大茂密，陽光難以穿透。",
        "tier_requirement": 1.0,
        "exits": {
            "south": "nearby_market",  # 往南 -> 集市
        },
        "event_chance": 0.20,  # 野外危險，事件多
        "features": ["可能遭遇靈獸", "可以採集靈草"],
        "available_npcs": [],
    },

    # 商業區：附近集市
    "nearby_market": {
        "id": "nearby_market",
        "name": "青雲鎮·集市",
        "description": "熱鬧的集市，凡人與修仙者混雜其中。各種奇珍異寶在此交易。",
        "tier_requirement": 1.0,
        "exits": {
            "north": "wildlands_forest", # 往北 -> 森林
        },
        "event_chance": 0.12,
        "features": ["可以交易", "物價便宜"],
        "available_npcs": [],
    },
}


# 方向對照表（用於自然語言解析）
DIRECTION_ALIASES = {
    # 北
    "north": "north", "北": "north", "n": "north",
    "往北": "north", "向北": "north", "北方": "north",

    # 南
    "south": "south", "南": "south", "s": "south",
    "往南": "south", "向南": "south", "南方": "south",

    # 東
    "east": "east", "東": "east", "e": "east",
    "往東": "east", "向東": "east", "東方": "east",

    # 西
    "west": "west", "西": "west", "w": "west",
    "往西": "west", "向西": "west", "西方": "west",
}


def get_location_data(location_id: str) -> dict:
    """
    獲取地點數據

    Args:
        location_id: 地點 ID

    Returns:
        地點數據字典，如果不存在返回 None
    """
    return WORLD_MAP.get(location_id)


def get_location_name(location_id: str) -> str:
    """
    獲取地點顯示名稱

    Args:
        location_id: 地點 ID

    Returns:
        地點名稱，如果不存在返回 ID 本身
    """
    location = WORLD_MAP.get(location_id)
    if location:
        return location['name']
    return location_id


def normalize_direction(user_input: str) -> str:
    """
    將用戶輸入標準化為方向

    Args:
        user_input: 用戶輸入（如 "往北"、"north"、"n"）

    Returns:
        標準化方向（"north", "south", "east", "west"），如果無法識別返回 None
    """
    user_input = user_input.strip().lower()
    return DIRECTION_ALIASES.get(user_input)


def get_all_locations() -> list:
    """
    獲取所有地點 ID 列表

    Returns:
        地點 ID 列表
    """
    return list(WORLD_MAP.keys())


def get_starting_location() -> str:
    """
    獲取起始地點 ID

    Returns:
        起始地點 ID
    """
    return "qingyun_foot"
