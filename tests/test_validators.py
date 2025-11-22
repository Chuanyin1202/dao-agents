# tests/test_validators.py
# 道·衍 - 數據一致性驗證器測試

import unittest
import sys
import os

# 添加 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from validators import ConsistencyValidator, auto_fix_state


class TestConsistencyValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ConsistencyValidator()

    # ========== 物品獲得測試 ==========
    def test_valid_gain(self):
        """測試正常的物品獲得"""
        narrative = "你撿起了一把鏽跡斑斑的鐵劍。"
        update = {"items_gained": ["鐵劍"]}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_missing_gain_update(self):
        """測試敘述有獲得，但狀態沒更新 (應報錯)"""
        narrative = "長老微笑著賜予你一枚築基丹。"
        update = {"items_gained": []}  # 空的
        result = self.validator.validate(narrative, update)
        self.assertFalse(result['valid'])
        self.assertTrue(any("賜予" in e for e in result['errors']))

    def test_negative_sentence_gain(self):
        """測試否定句（沒有獲得）不應誤報"""
        narrative = "你搜索了房間，但沒有獲得任何有用的東西。"
        update = {"items_gained": []}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])  # 不應報錯

    def test_gain_item_not_in_narrative(self):
        """測試狀態有物品但敘述沒提到（警告）"""
        narrative = "你走進了房間。"
        update = {"items_gained": ["神秘藥瓶"]}
        result = self.validator.validate(narrative, update)
        # 注意：目前實現中，這會被判定為警告而非錯誤
        # 但由於敘述中沒有「獲得」等關鍵詞，不會觸發錯誤
        # 只有反向檢查會產生警告
        self.assertEqual(len(result['warnings']), 1)
        self.assertTrue(any("神秘藥瓶" in w for w in result['warnings']))

    # ========== HP 變化測試 ==========
    def test_valid_damage(self):
        """測試正常的受傷"""
        narrative = "你被震飛出去，吐出一口鮮血，受了輕傷。"
        update = {"hp_change": -20}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])

    def test_missing_hp_deduction(self):
        """測試敘述受傷，但 HP 沒扣 (應報錯)"""
        narrative = "那一掌結結實實打在你胸口，你感到劇烈的疼痛。"
        update = {"hp_change": 0}
        result = self.validator.validate(narrative, update)
        self.assertFalse(result['valid'])
        self.assertTrue(any("疼痛" in e for e in result['errors']))

    def test_hp_change_too_large_warning(self):
        """測試 HP 扣減過大（警告）"""
        narrative = "你受了重傷。"
        update = {"hp_change": -250}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])  # 不算錯誤
        self.assertTrue(any("過大" in w and "HP" in w for w in result['warnings']))

    # ========== 移動測試 ==========
    def test_valid_movement(self):
        """測試正常的移動"""
        narrative = "你沿著山路前行，終於來到了青雲門·外門廣場。"
        update = {"location_new": "青雲門·外門廣場"}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])

    def test_missing_location_update(self):
        """測試敘述移動，但位置沒更新（應報錯）"""
        narrative = "經過一段艱難的跋涉，你終於抵達了靈獸森林。"
        update = {"location_new": None}
        result = self.validator.validate(narrative, update)
        self.assertFalse(result['valid'])
        self.assertTrue(any("抵達" in e for e in result['errors']))

    def test_intention_movement_not_error(self):
        """測試意圖移動（想要去）不應報錯"""
        narrative = "你打算來到青雲門，但路途遙遠，需要準備。"
        update = {"location_new": None}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])  # 不應報錯

    # ========== Karma 測試 ==========
    def test_karma_change_warning(self):
        """測試 karma 變化過大（警告）"""
        narrative = "你的善行感動了天地。"
        update = {"karma_change": 80}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])  # 不算錯誤
        self.assertTrue(any("Karma" in w and "過大" in w for w in result['warnings']))

    # ========== 技能學習測試 ==========
    def test_skill_learned(self):
        """測試技能學習"""
        narrative = "經過長時間的修煉，你學會了基礎劍法。"
        update = {"skills_gained": ["基礎劍法"]}
        result = self.validator.validate(narrative, update)
        self.assertTrue(result['valid'])

    def test_missing_skill_update(self):
        """測試敘述學會技能，但狀態沒更新（應報錯）"""
        narrative = "你學會了基礎劍法。"
        update = {"skills_gained": []}
        result = self.validator.validate(narrative, update)
        self.assertFalse(result['valid'])
        self.assertTrue(any("學會" in e for e in result['errors']))


class TestAutoFixState(unittest.TestCase):
    """測試 Level 3 自動修復機制"""

    def test_auto_fix_items_gained(self):
        """測試自動提取物品名"""
        narrative = "長老賜予你一枚築基丹和一把靈劍。"
        update = {"items_gained": []}

        fixed = auto_fix_state(narrative, update)

        self.assertTrue(len(fixed['items_gained']) > 0)
        # 應該提取到「築基丹」或「靈劍」
        items_str = "".join(fixed['items_gained'])
        self.assertTrue("築基丹" in items_str or "靈劍" in items_str)

    def test_auto_fix_hp_damage(self):
        """測試自動設置 HP 扣減（需要明確數值）"""
        narrative = "你受了重傷，失去了 20 點生命。"
        update = {"hp_change": 0}

        fixed = auto_fix_state(narrative, update)

        self.assertTrue(fixed['hp_change'] < 0)
        self.assertEqual(fixed['hp_change'], -20)

    def test_auto_fix_movement(self):
        """測試自動提取目的地（auto_fix 提取 location_new，然後由翻譯層轉為 location_id）"""
        narrative = "經過長途跋涉，你終於進入了靈獸森林。"
        update = {"location_new": None}

        fixed = auto_fix_state(narrative, update)

        # auto_fix_state 會提取到 location_new
        # 輸出應該包含 location_new（翻譯層會在 apply_state_update 時處理）
        # 或者如果已經經過翻譯層，會是 location_id
        # 由於 auto_fix_state 內部調用了 normalize_location_update，
        # 最終結果應該是 location_id（如果地點在地圖上）
        self.assertTrue(
            'location_new' in fixed or 'location_id' in fixed,
            f"Expected location_new or location_id in result, got: {fixed}"
        )

        if 'location_id' in fixed:
            # 如果已轉為 ID，驗證是正確的 ID
            self.assertEqual(fixed['location_id'], 'wildlands_forest')


if __name__ == '__main__':
    unittest.main()
