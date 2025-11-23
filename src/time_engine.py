# time_engine.py
# 道·衍 - 全域時間系統

"""
時間系統（Global Tick）

設計理念：
- 每個行動推進遊戲時間（tick）
- 用於未來的「懶惰結算」（Lazy Evaluation）
- 例如：靈草每 100 tick 生長一次、NPC 每 50 tick 移動一次

Tick 換算：
- 1 tick ≈ 10 分鐘遊戲時間
- 1 遊戲日 = 144 tick
- 1 遊戲月 = 4320 tick
"""

from typing import Dict, Any


class TimeEngine:
    """
    全域時間引擎

    管理遊戲內的時間流逝和事件調度
    """

    def __init__(self):
        self.current_tick = 0  # 全域時鐘（從遊戲開始計算）

    def advance_time(self, ticks: int) -> int:
        """
        推進時間

        Args:
            ticks: 要推進的 tick 數

        Returns:
            新的 current_tick
        """
        if ticks < 0:
            raise ValueError("Ticks 不能為負數")

        self.current_tick += ticks
        return self.current_tick

    def get_current_tick(self) -> int:
        """
        獲取當前時間

        Returns:
            當前 tick
        """
        return self.current_tick

    def set_current_tick(self, tick: int):
        """
        設置當前時間（用於從存檔載入）

        Args:
            tick: 要設置的 tick 值
        """
        if tick < 0:
            raise ValueError("Tick 不能為負數")

        self.current_tick = tick

    def get_time_description(self) -> str:
        """
        獲取時間的文字描述

        Returns:
            時間描述（如 "第 3 天 上午"）
        """
        day = (self.current_tick // 144) + 1
        hour_in_day = (self.current_tick % 144) // 6  # 0-23

        if 6 <= hour_in_day < 12:
            period = "上午"
        elif 12 <= hour_in_day < 18:
            period = "下午"
        elif 18 <= hour_in_day < 24:
            period = "晚上"
        else:
            period = "深夜"

        return f"第 {day} 天 {period}"

    def get_detailed_time_context(self) -> Dict[str, Any]:
        """
        獲取詳細的時間上下文（用於 AI 描述）

        Returns:
            {
                "hour": 0-23,
                "period": "深夜/上午/下午/晚上",
                "season": "春/夏/秋/冬",
                "day": 遊戲天數,
                "weather_hint": 天氣提示
            }
        """
        day = (self.current_tick // 144) + 1
        hour_in_day = (self.current_tick % 144) // 6  # 0-23

        # 時段
        if 6 <= hour_in_day < 12:
            period = "上午"
            period_desc = "陽光明媚"
        elif 12 <= hour_in_day < 18:
            period = "下午"
            period_desc = "日頭正盛"
        elif 18 <= hour_in_day < 24:
            period = "晚上"
            period_desc = "暮色降臨"
        else:
            period = "深夜"
            period_desc = "夜深人靜"

        # 季節（假設 120 天為一個循環：春夏秋冬各 30 天）
        day_in_year = day % 120
        if day_in_year <= 30:
            season = "春"
            season_desc = "萬物復甦，生機盎然"
        elif day_in_year <= 60:
            season = "夏"
            season_desc = "烈日炎炎，蟬鳴陣陣"
        elif day_in_year <= 90:
            season = "秋"
            season_desc = "秋高氣爽，落葉紛飛"
        else:
            season = "冬"
            season_desc = "寒風凜冽，白雪皚皚"

        return {
            "hour": hour_in_day,
            "period": period,
            "period_desc": period_desc,
            "season": season,
            "season_desc": season_desc,
            "day": day,
            "weather_hint": f"{season}季{period}，{period_desc}，{season_desc}"
        }

    def calculate_time_cost(self, action_type: str) -> int:
        """
        計算行動消耗的時間

        Args:
            action_type: 行動類型（"MOVE", "CULTIVATE", "TALK" 等）

        Returns:
            消耗的 tick 數
        """
        action_costs = {
            "MOVE": 3,        # 移動：3 tick（約 30 分鐘）
            "CULTIVATE": 10,  # 修煉：10 tick（約 1.5 小時）
            "TALK": 1,        # 對話：1 tick（約 10 分鐘）
            "INSPECT": 1,     # 檢查：1 tick
            "USE_ITEM": 1,    # 使用物品：1 tick
            "REST": 5,        # 休息：5 tick（約 50 分鐘）
            "ATTACK": 2,      # 戰鬥：2 tick（約 20 分鐘）
            "SKILL_USE": 2,   # 使用技能：2 tick
            "TRADE": 2,       # 交易：2 tick
        }

        # ✅ Fallback: 未知意圖預設 1 tick，避免 KeyError
        return action_costs.get(action_type, 1)


# 全域時間引擎實例
global_time_engine = TimeEngine()


def get_time_engine() -> TimeEngine:
    """
    獲取全域時間引擎實例

    Returns:
        TimeEngine 實例
    """
    return global_time_engine


def advance_game_time(action_type: str) -> Dict[str, Any]:
    """
    推進遊戲時間（根據行動類型）

    Args:
        action_type: 行動類型

    Returns:
        {
            "ticks_passed": int,
            "new_tick": int,
            "time_description": str
        }
    """
    engine = get_time_engine()
    ticks = engine.calculate_time_cost(action_type)
    new_tick = engine.advance_time(ticks)

    return {
        "ticks_passed": ticks,
        "new_tick": new_tick,
        "time_description": engine.get_time_description()
    }


def get_current_game_time() -> Dict[str, Any]:
    """
    獲取當前遊戲時間

    Returns:
        {
            "tick": int,
            "description": str
        }
    """
    engine = get_time_engine()

    return {
        "tick": engine.get_current_tick(),
        "description": engine.get_time_description()
    }


def load_game_time(tick: int):
    """
    從存檔載入遊戲時間

    Args:
        tick: 存檔中的 tick 值
    """
    engine = get_time_engine()
    engine.set_current_tick(tick)


# 未來擴展：事件調度器
# TODO: 實現 EventScheduler 用於「懶惰結算」
# 例如：每 100 tick 生長靈草、每 50 tick NPC 移動等
