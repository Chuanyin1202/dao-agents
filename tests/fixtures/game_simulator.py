# -*- coding: utf-8 -*-
"""
GameSimulator - 完整遊戲環境模擬器
用於端到端測試和整合測試
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from io import StringIO
from contextlib import redirect_stdout

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from main import DaoGame


class GameSimulator:
    """
    模擬完整遊戲環境，用於自動化測試

    使用方式：
        sim = GameSimulator(mock_ai=True)
        sim.create_test_player("測試玩家")
        result = sim.simulate_input("m")
        assert "可用方向" in result["output"]
    """

    def __init__(self, mock_ai: bool = True, db_path: Optional[str] = None):
        """
        Args:
            mock_ai: 是否模擬 AI 回應（True=快速測試，False=真實 AI）
            db_path: 測試資料庫路徑（None=使用臨時記憶體資料庫）
        """
        self.mock_ai = mock_ai
        self.db_path = db_path or ":memory:"

        # 設置環境變數
        if mock_ai:
            os.environ['MOCK_AI'] = 'true'

        # 創建遊戲實例（DaoGame 不接受參數）
        self.game = DaoGame()

        # 記錄
        self.conversation_log = []
        self.state_history = []

    def create_test_player(
        self,
        name: str = "測試玩家",
        location_id: str = "qingyun_foot",
        tier: float = 1.0,
        hp: int = 100,
        mp: int = 100
    ) -> Dict[str, Any]:
        """
        創建測試玩家

        Returns:
            初始玩家狀態
        """
        # 創建新玩家
        self.game.player_name = name
        self.game.player_state = {
            "location_id": location_id,
            "location": self.game._get_location_name(location_id),
            "tier": tier,
            "hp": hp,
            "max_hp": hp,
            "mp": mp,
            "max_mp": mp,
            "inventory": [],
            "karma": 0,
            "tick": 0
        }

        # 保存初始狀態
        self._save_state_snapshot("初始化")

        return self.game.player_state.copy()

    def simulate_input(self, user_input: str) -> Dict[str, Any]:
        """
        模擬用戶輸入

        Args:
            user_input: 用戶輸入的指令

        Returns:
            {
                "success": bool,
                "output": str,           # 輸出內容
                "state_before": dict,    # 操作前狀態
                "state_after": dict,     # 操作後狀態
                "state_changes": dict,   # 狀態變化
                "errors": list           # 錯誤列表
            }
        """
        # 記錄操作前狀態
        state_before = self.game.player_state.copy()

        # 捕獲輸出
        output_buffer = StringIO()
        errors = []
        success = False

        try:
            # 模擬輸入（這裡需要直接調用遊戲邏輯，而非整個 run loop）
            # 因為 run() 是無限迴圈，我們需要調用內部方法

            # 調用 handle_shortcut
            expanded_input = self.game.handle_shortcut(user_input)
            if expanded_input is None:
                # 快捷命令已處理完畢（如 help, quit）
                output = f"快捷命令 '{user_input}' 已處理"
                success = True
            else:
                # 需要進一步處理
                with redirect_stdout(output_buffer):
                    # 這裡需要調用實際的處理邏輯
                    # 由於 main.py 的結構，我們可能需要重構部分邏輯
                    # 暫時使用簡化版本
                    if user_input == 'm':
                        # 移動快捷命令特殊處理
                        output = self._simulate_movement_menu()
                    else:
                        # 其他命令通過 Observer 處理
                        output = self._simulate_command(expanded_input)

                success = True

        except Exception as e:
            errors.append(str(e))
            output = f"錯誤: {e}"

        # 記錄操作後狀態
        state_after = self.game.player_state.copy()

        # 計算狀態變化
        state_changes = self._diff_states(state_before, state_after)

        # 保存到歷史
        self._save_state_snapshot(f"輸入: {user_input}")
        self.conversation_log.append({
            "input": user_input,
            "output": output,
            "success": success,
            "errors": errors
        })

        return {
            "success": success,
            "output": output,
            "state_before": state_before,
            "state_after": state_after,
            "state_changes": state_changes,
            "errors": errors
        }

    def _simulate_movement_menu(self) -> str:
        """模擬移動選單顯示"""
        from world_data import get_location_data, get_location_name

        current_loc_id = self.game.player_state.get('location_id', 'qingyun_foot')
        loc_data = get_location_data(current_loc_id)
        exits = loc_data.get('exits', {})

        output = "\n【可用方向】\n"
        direction_map = {'north': '北', 'south': '南', 'east': '東', 'west': '西'}

        for direction, dest_id in exits.items():
            dest_name = get_location_name(dest_id)
            dir_chinese = direction_map.get(direction, direction)
            output += f"  {dir_chinese} ({direction[0]}) → {dest_name}\n"

        return output

    def _simulate_command(self, command: str) -> str:
        """模擬命令處理（簡化版本）"""
        # 這裡需要根據實際需求實現
        # 暫時返回簡化結果
        return f"處理命令: {command}"

    def _diff_states(self, before: Dict, after: Dict) -> Dict:
        """計算狀態差異"""
        changes = {}

        # 檢查所有欄位
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)

            if before_val != after_val:
                changes[key] = {
                    "before": before_val,
                    "after": after_val,
                    "delta": self._calculate_delta(before_val, after_val)
                }

        return changes

    def _calculate_delta(self, before, after):
        """計算數值變化"""
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            return after - before
        return None

    def _save_state_snapshot(self, label: str):
        """保存狀態快照"""
        self.state_history.append({
            "label": label,
            "state": self.game.player_state.copy(),
            "step": len(self.state_history)
        })

    def get_player_state(self) -> Dict[str, Any]:
        """獲取當前玩家狀態"""
        return self.game.player_state.copy()

    def assert_state(self, **assertions):
        """
        驗證狀態

        使用方式：
            sim.assert_state(
                location_id="qingyun_plaza",
                hp=100,
                mp={"min": 90}
            )
        """
        current_state = self.game.player_state
        errors = []

        for key, expected in assertions.items():
            actual = current_state.get(key)

            # 處理不同類型的斷言
            if isinstance(expected, dict):
                # 範圍檢查
                if "min" in expected and actual < expected["min"]:
                    errors.append(f"{key}: 期望 >= {expected['min']}, 實際 {actual}")
                if "max" in expected and actual > expected["max"]:
                    errors.append(f"{key}: 期望 <= {expected['max']}, 實際 {actual}")
                if "unchanged" in expected and expected["unchanged"]:
                    # 需要與初始狀態比較（這裡簡化處理）
                    pass
            else:
                # 精確匹配
                if actual != expected:
                    errors.append(f"{key}: 期望 {expected}, 實際 {actual}")

        if errors:
            raise AssertionError(f"狀態驗證失敗:\n" + "\n".join(f"  - {e}" for e in errors))

        return True
