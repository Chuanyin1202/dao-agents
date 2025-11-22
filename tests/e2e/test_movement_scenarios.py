# -*- coding: utf-8 -*-
"""
移動場景端到端測試
模擬真實用戶操作，測試完整移動流程
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from fixtures import GameSimulator, StateInspector
from agent import agent_observer
from world_map import validate_movement, normalize_direction


class TestMovementScenarios:
    """測試所有移動相關場景"""

    @pytest.fixture
    def game_sim(self):
        """提供遊戲模擬器"""
        sim = GameSimulator(mock_ai=True)
        sim.create_test_player(location_id="qingyun_foot")
        return sim

    @pytest.fixture
    def inspector(self):
        """提供狀態檢查器"""
        return StateInspector()

    def test_movement_complete_flow_single_letter(self, game_sim, inspector):
        """
        場景：完整移動流程 - 單字母快捷鍵

        步驟：
        1. 玩家在山腳
        2. 輸入 'm' 觸發移動選單
        3. 選單顯示可用方向
        4. 輸入 'n'
        5. 成功移動到外門廣場

        當前狀態：❌ 會失敗
        失敗點：Observer 無法識別 'n'
        """
        # 記錄初始狀態
        state_before = game_sim.get_player_state()

        assert state_before['location_id'] == "qingyun_foot"

        # 步驟 1: 模擬輸入 'm'
        result1 = game_sim.simulate_input("m")

        # 驗證顯示了選單
        assert "可用方向" in result1["output"], "移動選單未顯示"

        # 步驟 2: 模擬輸入 'n'
        # 這裡我們需要直接測試 Observer → validate → move 的流程
        # 因為 GameSimulator 可能尚未完整實現

        # 測試 Observer 解析
        intent = agent_observer('n', recent_events=[])
        print(f"\nObserver 解析 'n': {intent}")

        # 測試標準化
        target = intent.get('target')
        normalized = normalize_direction(target) if target else None
        print(f"標準化結果: {target} -> {normalized}")

        # 測試移動驗證
        if normalized:
            validation = validate_movement("qingyun_foot", normalized, 1.0)
            print(f"移動驗證: {validation}")

            # 斷言移動成功
            assert validation['valid'], f"移動驗證失敗: {validation.get('reason')}"
            assert validation['destination_id'] == "qingyun_plaza", \
                f"目的地錯誤: 期望 qingyun_plaza, 實際 {validation['destination_id']}"
        else:
            pytest.fail(
                f"❌ 完整移動流程失敗\n\n"
                f"失敗點: Observer 無法正確處理單字母 'n'\n"
                f"  intent 類型: {intent.get('intent')}\n"
                f"  target: {target}\n"
                f"  標準化後: {normalized}\n\n"
                f"這證明了當前架構的核心問題：\n"
                f"  1. UI 提示用戶可以輸入 'n'\n"
                f"  2. 但 Observer 無法識別 'n'\n"
                f"  3. 導致移動失敗\n"
            )

    def test_movement_chinese_direction(self):
        """
        場景：使用中文方向

        輸入：'北'
        期望：成功移動
        """
        intent = agent_observer('北', recent_events=[])

        assert intent.get('intent') == 'MOVE', \
            f"Observer 未識別為 MOVE: {intent}"

        target = intent.get('target')
        assert target, f"Observer 未提取 target: {intent}"

        normalized = normalize_direction(target)
        assert normalized == 'north', \
            f"標準化失敗: {target} -> {normalized}"

        # 驗證移動
        validation = validate_movement("qingyun_foot", normalized, 1.0)
        assert validation['valid'], validation.get('reason')

    def test_movement_full_sentence(self):
        """
        場景：使用完整句子

        輸入：'我要往北走'
        期望：成功移動
        """
        intent = agent_observer('我要往北走', recent_events=[])

        assert intent.get('intent') == 'MOVE', \
            f"Observer 未識別為 MOVE: {intent}"

        target = intent.get('target')
        normalized = normalize_direction(target) if target else None

        assert normalized == 'north', \
            f"目標提取或標準化失敗: target={target}, normalized={normalized}"

        # 驗證移動
        validation = validate_movement("qingyun_foot", normalized, 1.0)
        assert validation['valid'], validation.get('reason')

    def test_movement_invalid_direction(self):
        """
        場景：無效方向

        輸入：往南（山腳沒有南出口）
        期望：顯示友好錯誤訊息
        """
        validation = validate_movement("qingyun_foot", "south", 1.0)

        assert not validation['valid'], "應該拒絕無效方向"

        reason = validation.get('reason', '')
        assert '無法' in reason or '不存在' in reason, \
            f"錯誤訊息不夠清晰: {reason}"

        # 確保錯誤訊息提示可用方向
        assert '可用方向' in reason or '北' in reason, \
            f"錯誤訊息應提示可用方向: {reason}"

    def test_movement_tier_requirement(self):
        """
        場景：境界不足

        假設某地點需要築基期，但玩家只有練氣期
        期望：拒絕並說明原因
        """
        # 這個測試需要實際地圖數據
        # 暫時跳過，標記為需要實現
        pytest.skip("需要地圖數據：有境界要求的地點")

    def test_movement_mp_consumption(self, game_sim, inspector):
        """
        場景：移動消耗法力

        驗證：
        1. 移動後 MP 應該減少
        2. MP 減少量合理（5-10 點）
        """
        pytest.skip("需要完整的 GameSimulator 實現")

    def test_movement_narrative_consistency(self, game_sim, inspector):
        """
        場景：移動後的劇情一致性

        驗證：
        1. 劇情提到移動到的地點名稱
        2. player_state 的 location 與劇情一致
        """
        pytest.skip("需要完整的 GameSimulator 和 NarrativeAnalyzer")

    def test_all_directions_from_plaza(self):
        """
        測試：從外門廣場出發，所有方向都能正常使用

        外門廣場有多個出口，測試每個出口
        """
        from world_data import get_location_data

        plaza_data = get_location_data("qingyun_plaza")
        exits = plaza_data.get('exits', {})

        for direction, dest_id in exits.items():
            validation = validate_movement("qingyun_plaza", direction, 1.0)

            assert validation['valid'], \
                f"從外門廣場往 {direction} 失敗: {validation.get('reason')}"

            assert validation['destination_id'] == dest_id, \
                f"目的地錯誤: 期望 {dest_id}, 實際 {validation['destination_id']}"

    def test_movement_state_integrity(self, inspector):
        """
        測試：移動後狀態的完整性

        檢查：
        1. location 和 location_id 一致
        2. HP/MP 在合法範圍
        3. 無意外的欄位變化
        """
        # 模擬移動前後的狀態
        state_before = {
            'location_id': 'qingyun_foot',
            'location': '青雲門·山腳',
            'hp': 100,
            'max_hp': 100,
            'mp': 100,
            'max_mp': 100,
            'tier': 1.0,
            'inventory': [],
            'karma': 0,
            'tick': 0
        }

        state_after = {
            'location_id': 'qingyun_plaza',
            'location': '青雲門·外門廣場',
            'hp': 100,
            'max_hp': 100,
            'mp': 95,  # 消耗 5 點
            'max_mp': 100,
            'tier': 1.0,
            'inventory': [],
            'karma': 0,
            'tick': 3  # 消耗 3 tick
        }

        # 檢查狀態完整性
        errors_before = inspector.check_all(state_before)
        errors_after = inspector.check_all(state_after)

        assert not errors_before, f"移動前狀態有問題: {errors_before}"
        assert not errors_after, f"移動後狀態有問題: {errors_after}"

        # 檢查狀態變化合理性
        diff = inspector.diff_states(state_before, state_after)

        assert diff['hp_change'] == 0, "移動不應扣血"
        assert diff['mp_change'] < 0, "移動應消耗法力"
        assert diff['location_change'], "位置應該變化"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
