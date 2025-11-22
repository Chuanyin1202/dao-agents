# -*- coding: utf-8 -*-
"""
回歸測試 - 已修復 bug 測試
確保已修復的 bug 不會再次出現
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from fixtures import StateInspector, NarrativeAnalyzer
from agent import agent_observer
from world_map import normalize_direction, validate_movement
from world_data import get_location_data, WORLD_MAP


class TestKnownBugs:
    """
    記錄已修復的 bug，防止復發

    每個測試對應一個已知 bug
    測試名稱格式：test_bug_YYYYMMDD_簡短描述
    """

    def test_bug_20241122_direction_input_bypasses_observer(self):
        """
        Bug #1: Observer 無法識別單字母方向 'n'

        發現日期：2024-11-22
        症狀：用戶輸入 'n' 被識別為 INSPECT，而非 MOVE
        根本原因：GPT-4o-mini 無法可靠識別單字母輸入
        修復方案：繞過 Observer，直接處理方向輸入
        修復日期：2024-11-22

        當前狀態：✅ 已修復
        """
        from main import DaoGame

        # 創建遊戲實例
        game = DaoGame()

        # 測試 is_direction_input 能正確識別
        assert game.is_direction_input('n') is True, \
            "❌ Bug #1 未修復：'n' 未被識別為方向輸入"

        assert game.is_direction_input('s') is True
        assert game.is_direction_input('e') is True
        assert game.is_direction_input('w') is True

        # 測試中文方向
        assert game.is_direction_input('北') is True
        assert game.is_direction_input('南') is True

        # 測試英文方向
        assert game.is_direction_input('north') is True
        assert game.is_direction_input('south') is True

        # 確認這些輸入能被標準化
        assert normalize_direction('n') == 'north'
        assert normalize_direction('北') == 'north'
        assert normalize_direction('north') == 'north'

        print("\n  ✅ Bug #1 已修復：方向輸入現在繞過 Observer 直接處理")

    def test_bug_20241122_npc_injury_misidentified_as_player(self):
        """
        Bug #2: NPC 受傷被誤判為玩家受傷

        發現日期：2024-11-22
        症狀：劇情說「霜焰獅受傷」，玩家 HP 被扣減
        根本原因：Validator 檢查「受傷」關鍵詞，但沒檢查主語
        修復方案：添加 _is_player_subject() 方法區分主語
        修復日期：2024-11-22

        當前狀態：✅ 已修復
        """
        analyzer = NarrativeAnalyzer()

        # NPC 受傷的劇情
        narrative = "你一劍刺中霜焰獅，牠痛苦地吼叫，身上流出鮮血。"

        # 檢查是否正確識別為 NPC 受傷
        is_player = analyzer._is_player_subject(narrative, ['受傷', '痛苦', '鮮血'])

        assert not is_player, \
            f"❌ Bug #2 復發：NPC 受傷被誤判為玩家受傷"

    def test_bug_20241122_location_set_to_nonexistent_tunnel(self):
        """
        Bug #3: 位置被設為不存在的「隧道」

        發現日期：2024-11-22
        症狀：劇情說「走進隧道」，location 被設為「隧道」（不在地圖上）
        根本原因：Level 3 auto-fix 提取位置時未驗證是否在地圖上
        修復方案：Level 3 auto-fix 添加位置驗證
        修復日期：2024-11-22

        當前狀態：✅ 已修復（需要實際驗證）
        """
        inspector = StateInspector()

        # 模擬被設為無效位置的狀態
        invalid_state = {
            'location_id': 'tunnel',  # 無效 ID
            'location': '隧道',
            'hp': 100,
            'max_hp': 100,
            'mp': 100,
            'max_mp': 100,
            'tier': 1.0,
            'inventory': []
        }

        errors = inspector.check_location_consistency(invalid_state)

        # 應該檢測到錯誤
        assert len(errors) > 0, \
            f"❌ Bug #3 相關檢查失敗：無法檢測無效位置"

        assert any('不存在' in e or 'tunnel' in e for e in errors), \
            f"錯誤訊息應提到無效位置: {errors}"

    def test_bug_20241122_hp_deduction_without_narrative_evidence(self):
        """
        Bug #4: 無劇情依據的 HP 扣減

        發現日期：2024-11-22
        症狀：用戶輸入 'l' (查看環境)，HP 莫名減少 10 點
        根本原因：
          1. Drama 生成了包含「受傷靈獸」的劇情
          2. Validator 檢測到「受傷」關鍵詞
          3. Level 3 auto-fix 猜測 -20 HP

        修復方案：
          1. Level 3 auto-fix 禁止猜測，只用明確數值
          2. 增強 Drama prompt，限制不應出現的事件
        修復日期：2024-11-22

        當前狀態：✅ 已修復
        """
        analyzer = NarrativeAnalyzer()

        # 查看環境的劇情（不應有受傷）
        narrative = "你環顧四周，看到遠處有一隻受傷的靈獸在休息。"

        # 模擬狀態更新（錯誤：扣了血）
        state_update_wrong = {'hp_change': -10}
        state_before = {'hp': 100}
        state_after_wrong = {'hp': 90}

        result_wrong = analyzer.analyze_consistency(
            narrative, state_update_wrong, state_before, state_after_wrong
        )

        # 應該檢測到不一致（NPC 受傷不應扣玩家血）
        # 或至少有警告
        assert not result_wrong['consistent'] or len(result_wrong['warnings']) > 0, \
            f"❌ Bug #4 相關檢查失敗：未檢測到無依據的 HP 扣減"

        # 正確的狀態更新（不扣血）
        state_update_correct = {'hp_change': 0}
        state_after_correct = {'hp': 100}

        result_correct = analyzer.analyze_consistency(
            narrative, state_update_correct, state_before, state_after_correct
        )

        # 這個應該一致
        assert result_correct['consistent'], \
            f"正確的狀態更新被誤判為不一致: {result_correct}"

    def test_bug_20241122_direction_normalization_gaps(self):
        """
        Bug #5: 方向標準化存在缺口

        發現日期：2024-11-22
        症狀：某些常見方向詞無法被 normalize_direction 轉換
        修復方案：補充 DIRECTION_ALIASES
        修復狀態：部分修復（可能還有遺漏）

        這個測試持續追蹤是否有新的缺口
        """
        common_directions = [
            ('n', 'north'),
            ('s', 'south'),
            ('e', 'east'),
            ('w', 'west'),
            ('北', 'north'),
            ('南', 'south'),
            ('東', 'east'),
            ('西', 'west'),
            ('north', 'north'),
            ('south', 'south'),
            ('east', 'east'),
            ('west', 'west'),
        ]

        missing = []

        for input_dir, expected in common_directions:
            normalized = normalize_direction(input_dir)
            if normalized != expected:
                missing.append((input_dir, expected, normalized))

        assert not missing, \
            f"❌ Bug #5 存在/復發：以下方向無法正確標準化:\n" + \
            "\n".join(f"  '{i}' -> 期望 '{e}', 實際 '{n}'" for i, e, n in missing)

    def test_bug_20241122_ui_promises_n_but_system_cannot_handle(self):
        """
        Bug #6: UI 提示與實際處理脫節

        發現日期：2024-11-22
        症狀：移動選單顯示「北 (n)」，但輸入 'n' 無法使用
        根本原因：
          1. UI 提示用戶可以用 'n'
          2. 但 Observer 無法識別 'n'
          3. 用戶體驗極差

        修復方案：繞過 Observer 直接處理方向輸入
        修復日期：2024-11-22

        當前狀態：✅ 已修復
        """
        from main import DaoGame

        # 這個 bug 是 Bug #1 的用戶體驗體現
        # 通過繞過 Observer 的方案一併解決

        # 測試：從山腳往北移動
        current_location = "qingyun_foot"
        loc_data = get_location_data(current_location)
        exits = loc_data.get('exits', {})

        # UI 會顯示「北 (n)」
        assert 'north' in exits, "測試前提：山腳應該有北出口"

        # 創建遊戲實例
        game = DaoGame()

        # 測試用戶輸入 'n' 現在能被正確識別
        assert game.is_direction_input('n') is True, \
            "❌ Bug #6 未修復：'n' 未被識別為方向輸入"

        # 測試其他 UI 提示的快捷方式
        assert game.is_direction_input('s') is True
        assert game.is_direction_input('e') is True
        assert game.is_direction_input('w') is True

        # 驗證標準化功能
        normalized = normalize_direction('n')
        assert normalized == 'north', \
            f"❌ 標準化失敗：'n' -> {normalized}"

        # 驗證移動驗證功能
        validation = validate_movement(current_location, 'north', 1.0)
        assert validation.get('valid', False), \
            f"❌ 移動驗證失敗：{validation.get('reason')}"

        print("\n  ✅ Bug #6 已修復：UI 提示的快捷鍵 (n/s/e/w) 現在可以正常使用")

    def test_bug_20241122_random_events_too_frequent_for_newbies(self):
        """
        Bug #7: 新手隨機事件觸發過於頻繁

        發現日期：2024-11-22
        症狀：練氣期 1-2 級玩家頻繁遇到高級事件
        修復方案：tier < 1.5 時，事件機率減少 70%
        修復日期：2024-11-22

        當前狀態：✅ 已修復
        """
        from world_map import should_trigger_random_event

        # 測試 1000 次，統計觸發率
        trigger_count = 0
        test_runs = 1000

        for _ in range(test_runs):
            # 新手（tier 1.2）
            triggered = should_trigger_random_event(
                location_id="qingyun_plaza",
                player_karma=0,
                player_tier=1.2,
                base_multiplier=1.0
            )
            if triggered:
                trigger_count += 1

        trigger_rate = (trigger_count / test_runs) * 100

        # 新手觸發率應 < 10%（假設原本是 30%，減少 70% 後約 9%）
        assert trigger_rate < 15.0, \
            f"❌ Bug #7 未修復或復發：新手事件觸發率 {trigger_rate:.1f}% (期望 < 15%)"

        print(f"  ✅ 新手事件觸發率: {trigger_rate:.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
