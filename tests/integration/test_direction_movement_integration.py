# -*- coding: utf-8 -*-
"""
整合測試 - 完整的方向移動流程
這個測試會調用實際的 handle_direction_movement 方法
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from main import DaoGame


class TestDirectionMovementIntegration:
    """測試完整的方向移動整合流程"""

    def test_handle_direction_movement_executes_without_error(self):
        """
        測試：handle_direction_movement 能完整執行不報錯

        這個測試會：
        1. 創建真實的遊戲實例
        2. 設置測試玩家
        3. 調用 handle_direction_movement
        4. 驗證沒有異常
        5. 驗證狀態確實改變
        """
        # 創建遊戲實例
        game = DaoGame()

        # 設置測試玩家
        game.player_state = {
            'name': '整合測試玩家',
            'location_id': 'qingyun_foot',
            'location': '青雲門·山腳',
            'hp': 100,
            'max_hp': 100,
            'mp': 50,
            'max_mp': 50,
            'tier': 1.0,
            'inventory': [],
            'skills': [],
            'karma': 0
        }
        game.player_id = 999  # 測試 ID

        # 記錄初始位置
        initial_location = game.player_state['location_id']

        # 嘗試往北移動
        try:
            success = game.handle_direction_movement('n')
        except Exception as e:
            pytest.fail(f"handle_direction_movement 拋出異常: {e}\n"
                       f"這表示實現有問題（比如調用不存在的方法）")

        # 驗證移動成功
        assert success, "handle_direction_movement 應該返回 True"

        # 驗證位置改變
        new_location = game.player_state['location_id']
        assert new_location != initial_location, \
            f"位置應該改變，但還是 {initial_location}"

        print(f"\n  ✅ 成功從 {initial_location} 移動到 {new_location}")

    def test_handle_direction_movement_all_directions(self):
        """
        測試：所有方向輸入格式都能正確處理

        測試單字母、中文、英文全稱
        """
        test_cases = [
            ('n', 'qingyun_foot', '往北'),
            ('s', 'qingyun_plaza', '往南'),
            ('北', 'qingyun_foot', '中文北'),
            ('north', 'qingyun_foot', '英文 north'),
        ]

        game = DaoGame()
        failures = []

        for direction_input, start_location, description in test_cases:
            # 重置玩家位置
            game.player_state = {
                'name': '測試玩家',
                'location_id': start_location,
                'location': '測試位置',
                'hp': 100,
                'max_hp': 100,
                'mp': 50,
                'max_mp': 50,
                'tier': 1.0,
                'inventory': [],
                'skills': [],
                'karma': 0
            }
            game.player_id = 999

            try:
                success = game.handle_direction_movement(direction_input)
                if not success:
                    failures.append(f"{description} ('{direction_input}') 返回 False")
            except Exception as e:
                failures.append(f"{description} ('{direction_input}') 拋出異常: {e}")

        if failures:
            pytest.fail(
                f"以下方向移動失敗:\n" +
                "\n".join(f"  - {f}" for f in failures)
            )

        print(f"\n  ✅ 所有 {len(test_cases)} 種方向輸入格式都能正確處理")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
