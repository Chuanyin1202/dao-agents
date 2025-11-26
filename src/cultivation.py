# cultivation.py
# 道·衍 - 境界修煉系統

"""
境界突破制修煉系統

核心循環：
1. 修煉 (c) → 累積 cultivation_progress
2. 進度滿後 → 嘗試突破 (b)
3. 成功：tier 提升、屬性成長
4. 失敗：受傷 + 進度減半
"""

import random
from typing import Dict, Any, Tuple

# 大境界配置
# tier 整數部分對應大境界
TIER_CONFIG = {
    1: {
        "name": "練氣期",
        "required_progress": 100,  # 突破所需進度
        "base_success_rate": 70,   # 基礎成功率 %
        "hp_bonus": 10,            # 突破後 max_hp 增加
        "mp_bonus": 5,             # 突破後 max_mp 增加
    },
    2: {
        "name": "築基期",
        "required_progress": 200,
        "base_success_rate": 60,
        "hp_bonus": 20,
        "mp_bonus": 10,
    },
    3: {
        "name": "元嬰期",
        "required_progress": 400,
        "base_success_rate": 50,
        "hp_bonus": 40,
        "mp_bonus": 20,
    },
    4: {
        "name": "金丹期",
        "required_progress": 800,
        "base_success_rate": 40,
        "hp_bonus": 60,
        "mp_bonus": 30,
    },
    5: {
        "name": "化神期",
        "required_progress": 1600,
        "base_success_rate": 30,
        "hp_bonus": 100,
        "mp_bonus": 50,
    },
    6: {
        "name": "度劫期",
        "required_progress": 9999,  # 極難突破
        "base_success_rate": 10,
        "hp_bonus": 200,
        "mp_bonus": 100,
    },
}

# 小境界名稱（根據 tier 小數部分）
SUB_TIER_NAMES = {
    (0.0, 0.2): "初期",
    (0.3, 0.5): "中期",
    (0.6, 0.9): "後期",
}

# 修煉基礎消耗和獲得
CULTIVATE_MP_COST = 10       # 修煉消耗法力
CULTIVATE_BASE_PROGRESS = 10  # 基礎進度獲得
CULTIVATE_TIME_COST = 10      # 時間消耗（tick）

# 地點修煉加成
LOCATION_CULTIVATION_BONUS = {
    "qingyun_pool": 1.5,       # 靈池 +50%
    "qingyun_inner_gate": 1.5,  # 內門 +50%
    "qingyun_hall": 1.3,       # 主殿 +30%
}

# 突破失敗懲罰
BREAKTHROUGH_FAILURE_HP_RATIO = 0.3  # 失敗時扣除 max_hp 的 30%
BREAKTHROUGH_FAILURE_PROGRESS_RATIO = 0.5  # 失敗時進度減半


def get_major_tier(tier: float) -> int:
    """獲取大境界（tier 的整數部分）"""
    return int(tier)


def get_sub_tier_name(tier: float) -> str:
    """獲取小境界名稱"""
    decimal = round(tier % 1, 1)
    for (low, high), name in SUB_TIER_NAMES.items():
        if low <= decimal <= high:
            return name
    return "初期"


def get_tier_info(tier: float) -> Dict[str, Any]:
    """
    獲取境界完整資訊

    Args:
        tier: 境界值（如 1.3 = 練氣期中期）

    Returns:
        境界資訊字典
    """
    major = get_major_tier(tier)
    config = TIER_CONFIG.get(major, TIER_CONFIG[1])

    return {
        "major_tier": major,
        "tier_name": config["name"],
        "sub_tier_name": get_sub_tier_name(tier),
        "full_name": f"{config['name']}{get_sub_tier_name(tier)}",
        "required_progress": config["required_progress"],
        "base_success_rate": config["base_success_rate"],
        "hp_bonus": config["hp_bonus"],
        "mp_bonus": config["mp_bonus"],
    }


def get_tier_display_name(tier: float) -> str:
    """獲取境界顯示名稱（如：練氣期中期）"""
    info = get_tier_info(tier)
    return info["full_name"]


def calculate_breakthrough_rate(tier: float, karma: int) -> float:
    """
    計算突破成功率

    Args:
        tier: 當前境界
        karma: 氣運值

    Returns:
        成功率（0-100）
    """
    info = get_tier_info(tier)
    base_rate = info["base_success_rate"]

    # 氣運加成：每點氣運 +0.5%
    karma_bonus = karma * 0.5

    # 計算最終成功率（限制在 5%-95%）
    success_rate = base_rate + karma_bonus
    return max(5.0, min(95.0, success_rate))


def can_breakthrough(player_state: Dict[str, Any]) -> Tuple[bool, str]:
    """
    檢查是否可以嘗試突破

    Args:
        player_state: 玩家狀態

    Returns:
        (可否突破, 原因說明)
    """
    tier = player_state.get("tier", 1.0)
    progress = player_state.get("cultivation_progress", 0)
    hp = player_state.get("hp", 0)
    max_hp = player_state.get("max_hp", 100)

    info = get_tier_info(tier)
    required = info["required_progress"]

    # 檢查進度是否足夠
    if progress < required:
        return False, f"修煉進度不足（{progress}/{required}）"

    # 檢查 HP 是否足夠（至少 50%）
    if hp < max_hp * 0.5:
        return False, "生命值過低，無法承受突破的壓力"

    # 檢查是否已達最高境界
    if tier >= 6.9:
        return False, "已達度劫期巔峰，無法繼續突破"

    return True, "可以嘗試突破"


def attempt_breakthrough(player_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    嘗試境界突破

    Args:
        player_state: 玩家狀態

    Returns:
        {
            "success": bool,
            "state_changes": dict,  # 狀態變更
            "narrative_hint": str,  # 給 AI 的劇情提示
            "message": str,         # 系統訊息
        }
    """
    tier = player_state.get("tier", 1.0)
    karma = player_state.get("karma", 0)
    progress = player_state.get("cultivation_progress", 0)
    max_hp = player_state.get("max_hp", 100)
    max_mp = player_state.get("max_mp", 50)
    attempts = player_state.get("breakthrough_attempts", 0)

    info = get_tier_info(tier)
    success_rate = calculate_breakthrough_rate(tier, karma)

    # 擲骰決定成敗
    roll = random.uniform(0, 100)
    success = roll < success_rate

    if success:
        # 突破成功
        new_tier = round(tier + 0.3, 1)

        # 檢查是否進入新的大境界
        old_major = get_major_tier(tier)
        new_major = get_major_tier(new_tier)
        crossed_major = new_major > old_major

        # 計算屬性成長
        hp_bonus = info["hp_bonus"]
        mp_bonus = info["mp_bonus"]

        new_info = get_tier_info(new_tier)

        return {
            "success": True,
            "state_changes": {
                "tier": new_tier,
                "cultivation_progress": 0,
                "max_hp_change": hp_bonus,
                "max_mp_change": mp_bonus,
                "hp": max_hp + hp_bonus,  # 完全恢復
                "mp": max_mp + mp_bonus,  # 完全恢復
                "breakthrough_attempts": attempts + 1,
            },
            "narrative_hint": (
                f"突破成功！玩家從{info['full_name']}突破到{new_info['full_name']}。"
                f"{'跨入了新的大境界！' if crossed_major else ''}"
                f"體內靈力暴漲，渾身經脈都在重塑。"
            ),
            "message": (
                f"突破成功！境界提升至 {new_info['full_name']} ({new_tier})\n"
                f"生命上限 +{hp_bonus}，法力上限 +{mp_bonus}"
            ),
            "success_rate": success_rate,
            "roll": roll,
        }
    else:
        # 突破失敗
        hp_loss = int(max_hp * BREAKTHROUGH_FAILURE_HP_RATIO)
        new_progress = int(progress * BREAKTHROUGH_FAILURE_PROGRESS_RATIO)

        return {
            "success": False,
            "state_changes": {
                "hp_change": -hp_loss,
                "cultivation_progress": new_progress,
                "breakthrough_attempts": attempts + 1,
            },
            "narrative_hint": (
                f"突破失敗！玩家嘗試突破{info['full_name']}但遭到反噬。"
                f"靈力失控，經脈受損，需要時間恢復。"
            ),
            "message": (
                f"突破失敗！遭受反噬，生命 -{hp_loss}\n"
                f"修煉進度降至 {new_progress}"
            ),
            "success_rate": success_rate,
            "roll": roll,
        }


def cultivate(player_state: Dict[str, Any], location_id: str) -> Dict[str, Any]:
    """
    執行修煉

    Args:
        player_state: 玩家狀態
        location_id: 當前地點 ID

    Returns:
        {
            "success": bool,
            "state_changes": dict,
            "progress_gained": int,
            "mp_cost": int,
            "message": str,
        }
    """
    mp = player_state.get("mp", 0)
    progress = player_state.get("cultivation_progress", 0)
    tier = player_state.get("tier", 1.0)

    # 檢查法力是否足夠
    if mp < CULTIVATE_MP_COST:
        return {
            "success": False,
            "state_changes": {},
            "progress_gained": 0,
            "mp_cost": 0,
            "message": f"法力不足，需要 {CULTIVATE_MP_COST} 點法力才能修煉",
        }

    # 計算地點加成
    location_bonus = LOCATION_CULTIVATION_BONUS.get(location_id, 1.0)
    progress_gained = int(CULTIVATE_BASE_PROGRESS * location_bonus)

    # 計算新進度
    info = get_tier_info(tier)
    required = info["required_progress"]
    new_progress = min(progress + progress_gained, required)  # 不超過所需進度

    # 構建訊息
    bonus_text = ""
    if location_bonus > 1.0:
        bonus_text = f"（地點加成 +{int((location_bonus - 1) * 100)}%）"

    can_break, _ = can_breakthrough({**player_state, "cultivation_progress": new_progress})
    ready_text = "\n修煉圓滿，可以嘗試突破了！" if can_break else ""

    return {
        "success": True,
        "state_changes": {
            "mp_change": -CULTIVATE_MP_COST,
            "cultivation_progress": new_progress,
        },
        "progress_gained": progress_gained,
        "mp_cost": CULTIVATE_MP_COST,
        "message": (
            f"修煉完成！進度 +{progress_gained}{bonus_text}\n"
            f"當前進度：{new_progress}/{required}"
            f"{ready_text}"
        ),
    }


def get_cultivation_status(player_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    獲取修煉狀態摘要

    Args:
        player_state: 玩家狀態

    Returns:
        修煉狀態資訊
    """
    tier = player_state.get("tier", 1.0)
    progress = player_state.get("cultivation_progress", 0)
    karma = player_state.get("karma", 0)
    attempts = player_state.get("breakthrough_attempts", 0)

    info = get_tier_info(tier)
    required = info["required_progress"]
    success_rate = calculate_breakthrough_rate(tier, karma)
    can_break, reason = can_breakthrough(player_state)

    return {
        "tier": tier,
        "tier_name": info["full_name"],
        "progress": progress,
        "required": required,
        "progress_percent": min(100, int(progress / required * 100)),
        "can_breakthrough": can_break,
        "breakthrough_reason": reason,
        "success_rate": success_rate,
        "attempts": attempts,
    }
