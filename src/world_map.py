# world_map.py
# 道·衍 - 地圖驗證與事件系統

import random
from typing import Dict, Any, Optional
from world_data import WORLD_MAP, get_location_data, get_location_name, normalize_direction


def validate_movement(
    current_location_id: str,
    direction: str,
    player_tier: float
) -> Dict[str, Any]:
    """
    驗證移動是否合法

    Args:
        current_location_id: 當前地點 ID
        direction: 移動方向（"north", "south", "east", "west"）
        player_tier: 玩家境界

    Returns:
        {
            "valid": bool,
            "reason": str,            # 如果 invalid
            "destination_id": str,    # 如果 valid
            "destination_name": str,  # 如果 valid
            "description": str,       # 如果 valid
        }
    """
    # 檢查當前地點是否存在
    current_location = get_location_data(current_location_id)
    if not current_location:
        return {
            "valid": False,
            "reason": f"未知地點: {current_location_id}（這是系統錯誤，請回報）"
        }

    # 標準化方向
    normalized_dir = normalize_direction(direction) if direction else None
    if not normalized_dir:
        normalized_dir = direction  # 保留原始輸入

    # 檢查該方向是否可行
    exits = current_location.get("exits", {})
    if normalized_dir not in exits:
        available_dirs = list(exits.keys())
        if available_dirs:
            dir_names = {
                "north": "北",
                "south": "南",
                "east": "東",
                "west": "西"
            }
            available_chinese = [dir_names.get(d, d) for d in available_dirs]
            return {
                "valid": False,
                "reason": f"此處無法往{direction}。可用方向: {', '.join(available_chinese)}"
            }
        else:
            return {
                "valid": False,
                "reason": "此處是死路，無法離開。"
            }

    # 獲取目的地
    destination_id = exits[normalized_dir]
    destination = get_location_data(destination_id)

    if not destination:
        return {
            "valid": False,
            "reason": f"目的地數據錯誤: {destination_id}（這是系統錯誤，請回報）"
        }

    # 檢查境界要求
    required_tier = destination.get("tier_requirement", 1.0)
    if player_tier < required_tier:
        tier_names = {
            1.0: "練氣期",
            2.0: "築基期",
            3.0: "金丹期",
            4.0: "元嬰期"
        }
        required_name = tier_names.get(required_tier, f"境界 {required_tier}")
        current_name = tier_names.get(player_tier, f"境界 {player_tier}")

        return {
            "valid": False,
            "reason": f"境界不足。{destination['name']}需要{required_name}，你當前是{current_name}。"
        }

    # 移動合法
    return {
        "valid": True,
        "destination_id": destination_id,
        "destination_name": destination["name"],
        "description": destination["description"],
    }


def should_trigger_random_event(
    location_id: str,
    player_karma: int,
    base_multiplier: float = 1.0
) -> bool:
    """
    決定是否觸發隨機事件

    Args:
        location_id: 當前地點 ID
        player_karma: 玩家 karma 值
        base_multiplier: 基礎機率倍率（用於調試或特殊情況）

    Returns:
        是否觸發事件
    """
    location = get_location_data(location_id)
    if not location:
        return False

    base_chance = location.get("event_chance", 0.0)

    # karma 影響事件機率（最多 +10%）
    karma_bonus = min(player_karma / 1000, 0.10)

    final_chance = (base_chance + karma_bonus) * base_multiplier

    return random.random() < final_chance


def get_location_context(location_id: str) -> str:
    """
    生成地點的上下文描述（用於傳遞給 Logic Agent）

    Args:
        location_id: 地點 ID

    Returns:
        格式化的地點信息
    """
    location = get_location_data(location_id)
    if not location:
        return f"未知地點: {location_id}"

    exits = location.get("exits", {})
    dir_names = {
        "north": "北",
        "south": "南",
        "east": "東",
        "west": "西"
    }

    exit_descriptions = []
    for direction, dest_id in exits.items():
        dest = get_location_data(dest_id)
        dest_name = dest["name"] if dest else dest_id
        dir_chinese = dir_names.get(direction, direction)
        exit_descriptions.append(f"{dir_chinese}方 → {dest_name}")

    features = location.get("features", [])
    features_text = "、".join(features) if features else "無特殊"

    context = f"""當前地點: {location['name']}
境界要求: {location.get('tier_requirement', 1.0)}
可行路徑: {', '.join(exit_descriptions) if exit_descriptions else '無'}
特殊效果: {features_text}"""

    return context


def get_simple_movement_narrative(
    from_location_id: str,
    to_location_id: str,
    direction: str
) -> str:
    """
    生成簡單移動的敘述（不調用 AI）

    Args:
        from_location_id: 起點 ID
        to_location_id: 終點 ID
        direction: 移動方向

    Returns:
        移動敘述
    """
    from_name = get_location_name(from_location_id)
    to_location = get_location_data(to_location_id)
    to_name = to_location["name"] if to_location else to_location_id
    to_desc = to_location["description"] if to_location else ""

    dir_names = {
        "north": "北",
        "south": "南",
        "east": "東",
        "west": "西"
    }
    dir_chinese = dir_names.get(direction, direction)

    templates = [
        f"你離開{from_name}，朝{dir_chinese}方前行。{to_desc}不久，你來到了{to_name}。",
        f"你沿著山路向{dir_chinese}走去。{to_desc}經過一段時間，你抵達了{to_name}。",
        f"你邁步朝{dir_chinese}方行進。{to_desc}片刻之後，你進入了{to_name}。",
    ]

    return random.choice(templates)


def get_location_mp_cost(from_id: str, to_id: str) -> int:
    """
    計算移動消耗的法力值

    Args:
        from_id: 起點 ID
        to_id: 終點 ID

    Returns:
        法力消耗（通常 5-10 點）
    """
    # 基礎消耗
    base_cost = 5

    # 目的地境界要求越高，消耗越大
    to_location = get_location_data(to_id)
    if to_location:
        tier_requirement = to_location.get("tier_requirement", 1.0)
        tier_bonus = int((tier_requirement - 1.0) * 2)
        return base_cost + tier_bonus

    return base_cost


def get_location_time_cost(from_id: str, to_id: str) -> int:
    """
    計算移動消耗的時間（tick）

    Args:
        from_id: 起點 ID
        to_id: 終點 ID

    Returns:
        時間消耗（tick）
    """
    # 基礎消耗 3 tick
    base_cost = 3

    # 目的地境界要求越高，距離越遠
    to_location = get_location_data(to_id)
    if to_location:
        tier_requirement = to_location.get("tier_requirement", 1.0)
        tier_bonus = int((tier_requirement - 1.0) * 2)
        return base_cost + tier_bonus

    return base_cost
