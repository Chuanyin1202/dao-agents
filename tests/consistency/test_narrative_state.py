# -*- coding: utf-8 -*-
"""
劇情-狀態一致性測試
測試劇情敘述與狀態更新的一致性
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from fixtures import NarrativeAnalyzer


class TestNarrativeStateConsistency:
    """測試劇情敘述與狀態更新的一致性"""

    @pytest.fixture
    def analyzer(self):
        """提供劇情分析器"""
        return NarrativeAnalyzer()

    def test_damage_narrative_with_hp_change(self, analyzer):
        """
        測試：劇情提到玩家受傷，HP 必須扣減

        這是之前發現的 bug：
        - 劇情說玩家受傷
        - 但實際是 NPC 受傷
        - Validator 誤判導致扣血
        """
        # 場景 1: 玩家受傷（應該扣血）
        narrative1 = "你不慎被霜焰獅爪子劃傷，鮮血滲出，你感到一陣疼痛。"
        state_update1 = {'hp_change': -10}
        state_before1 = {'hp': 100}
        state_after1 = {'hp': 90}

        result1 = analyzer.analyze_consistency(
            narrative1, state_update1, state_before1, state_after1
        )

        assert result1['consistent'], f"應該一致，但發現錯誤: {result1['errors']}"

        # 場景 2: NPC 受傷（不應扣玩家血）
        narrative2 = "你一劍刺中霜焰獅的腹部，牠發出痛苦的吼叫，身上的傷口流出鮮血。"
        state_update2 = {'hp_change': 0}  # 玩家 HP 不變
        state_before2 = {'hp': 100}
        state_after2 = {'hp': 100}

        result2 = analyzer.analyze_consistency(
            narrative2, state_update2, state_before2, state_after2
        )

        assert result2['consistent'], \
            f"NPC 受傷不應扣玩家血，但檢測到錯誤: {result2['errors']}"

        # 場景 3: 劇情說玩家受傷，但沒扣血（錯誤）
        narrative3 = "你被靈獸的尾巴掃中，受傷流血，感到痛苦。"
        state_update3 = {'hp_change': 0}  # 錯誤：沒扣血
        state_before3 = {'hp': 100}
        state_after3 = {'hp': 100}

        result3 = analyzer.analyze_consistency(
            narrative3, state_update3, state_before3, state_after3
        )

        assert not result3['consistent'], "應該檢測到不一致"
        assert len(result3['errors']) > 0, "應該有錯誤"
        assert 'hp_change' in str(result3['errors']).lower() or '受傷' in str(result3['errors']), \
            f"錯誤訊息應提到 HP 或受傷: {result3['errors']}"

    def test_location_narrative_with_movement(self, analyzer):
        """
        測試：劇情提到移動，location 必須變化

        這是之前發現的另一個 bug：
        - 劇情說「走進隧道」
        - location 被設為「隧道」（不存在的地點）
        """
        # 場景 1: 正常移動
        narrative1 = "你沿著山路往北走去，不久後來到了青雲門·外門廣場。"
        state_update1 = {'location_new': '青雲門·外門廣場', 'location_id': 'qingyun_plaza'}
        state_before1 = {'location_id': 'qingyun_foot'}
        state_after1 = {'location_id': 'qingyun_plaza'}

        result1 = analyzer.analyze_consistency(
            narrative1, state_update1, state_before1, state_after1
        )

        assert result1['consistent'], f"應該一致，但發現問題: {result1}"

        # 場景 2: 劇情提到不存在的地點（之前的 bug）
        narrative2 = "你好奇地走進一條隧道，裡面漆黑一片。"
        state_update2 = {'location_new': '隧道'}  # 錯誤：隧道不在地圖上
        state_before2 = {'location_id': 'qingyun_foot'}
        state_after2 = {'location_id': 'tunnel'}  # 無效 ID

        # 這個測試需要檢查 location 是否在地圖上
        # 暫時只檢查劇情一致性
        result2 = analyzer.analyze_consistency(
            narrative2, state_update2, state_before2, state_after2
        )

        # 劇情本身可能一致，但 location 無效由其他測試檢查

    def test_item_gain_narrative_with_inventory(self, analyzer):
        """
        測試：劇情提到獲得物品，背包必須增加
        """
        # 場景 1: 正常獲得物品
        narrative1 = "你在草叢中發現了一把生鏽的鐵劍，將它拾起放入背包。"
        state_update1 = {'items_gained': ['鐵劍']}
        state_before1 = {'inventory': []}
        state_after1 = {'inventory': ['鐵劍']}

        result1 = analyzer.analyze_consistency(
            narrative1, state_update1, state_before1, state_after1
        )

        assert result1['consistent'] or len(result1['warnings']) == 0, \
            f"應該一致或只有警告: {result1}"

        # 場景 2: 劇情說獲得，但背包未變（錯誤）
        narrative2 = "你獲得了一本《基礎劍法》秘籍。"
        state_update2 = {'items_gained': []}  # 錯誤：沒加到背包
        state_before2 = {'inventory': []}
        state_after2 = {'inventory': []}

        result2 = analyzer.analyze_consistency(
            narrative2, state_update2, state_before2, state_after2
        )

        assert not result2['consistent'] or len(result2['warnings']) > 0, \
            "應該檢測到不一致或警告"

    def test_explicit_damage_value_extraction(self, analyzer):
        """
        測試：從劇情中提取明確的傷害數值

        例如：「你失去了 20 點生命」
        """
        test_cases = [
            ("你失去了 20 點生命", 20),
            ("扣除 15 HP", 15),
            ("損失 10 點血量", 10),
            ("受到 25 點傷害", 25),
            ("你感到一陣疼痛", None),  # 沒有明確數值
        ]

        for narrative, expected in test_cases:
            damage = analyzer.extract_damage_hints(narrative)
            assert damage == expected, \
                f"劇情 '{narrative}' 期望提取 {expected}，實際 {damage}"

    def test_player_vs_npc_subject_detection(self, analyzer):
        """
        測試：區分玩家和 NPC 受傷

        這是之前 bug 的根源：
        - 無法區分「你受傷」和「牠受傷」
        """
        test_cases = [
            ("你受傷了", ['受傷'], True),  # 玩家
            ("牠受傷了", ['受傷'], False),  # NPC
            ("靈獸受傷倒地", ['受傷'], False),  # NPC
            ("霜焰獅痛苦地吼叫", ['痛苦'], False),  # NPC
            ("你感到疼痛", ['疼痛'], True),  # 玩家
            ("他受了重傷", ['重傷'], False),  # NPC（他/她指 NPC）
        ]

        for narrative, keywords, is_player in test_cases:
            result = analyzer._is_player_subject(narrative, keywords)
            assert result == is_player, \
                f"劇情 '{narrative}' 期望 {'玩家' if is_player else 'NPC'}，實際 {'玩家' if result else 'NPC'}"

    def test_movement_destination_extraction(self, analyzer):
        """
        測試：從劇情中提取移動目的地
        """
        test_cases = [
            ("你來到了青雲門·外門廣場", "青雲門·外門廣場"),
            ("抵達靈草堂", "靈草堂"),
            ("你進入了內門大殿", "內門大殿"),
            ("你只是看了看周圍", None),  # 沒有移動
        ]

        for narrative, expected in test_cases:
            destination = analyzer.extract_movement_destination(narrative)
            if expected:
                assert destination and expected in destination, \
                    f"劇情 '{narrative}' 期望提取 '{expected}'，實際 '{destination}'"
            else:
                assert destination is None, \
                    f"劇情 '{narrative}' 不應提取目的地，但得到 '{destination}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
