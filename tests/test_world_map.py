# tests/test_world_map.py
# 道·衍 - 世界地圖測試

import unittest
import sys
import os

# 添加 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from world_map import validate_movement, get_location_context, should_trigger_random_event
from world_data import WORLD_MAP, get_location_data


class TestValidateMovement(unittest.TestCase):
    """測試移動驗證功能"""

    def test_valid_movement(self):
        """測試合法的移動（山腳 -> 外門廣場）"""
        result = validate_movement("qingyun_foot", "north", player_tier=1.0)
        self.assertTrue(result['valid'])
        self.assertEqual(result['destination_id'], "qingyun_plaza")

    def test_invalid_direction(self):
        """測試無效的方向"""
        result = validate_movement("qingyun_foot", "west", player_tier=1.0)
        self.assertFalse(result['valid'])
        self.assertIn("reason", result)

    def test_tier_requirement_not_met(self):
        """測試境界不足（練氣期無法進入藏經閣）"""
        result = validate_movement("qingyun_plaza", "west", player_tier=1.0)
        self.assertFalse(result['valid'])
        self.assertIn("境界", result['reason'])

    def test_tier_requirement_met(self):
        """測試境界滿足（築基期可進入藏經閣）"""
        result = validate_movement("qingyun_plaza", "west", player_tier=2.0)
        self.assertTrue(result['valid'])
        self.assertEqual(result['destination_id'], "qingyun_library")

    def test_unknown_location(self):
        """測試不存在的地點"""
        result = validate_movement("不存在的地方", "north", player_tier=1.0)
        self.assertFalse(result['valid'])
        self.assertIn("未知地點", result['reason'])


class TestLocationData(unittest.TestCase):
    """測試地點數據結構"""

    def test_all_locations_have_required_fields(self):
        """測試所有地點都有必要欄位"""
        for loc_id, loc_data in WORLD_MAP.items():
            self.assertIn('id', loc_data)
            self.assertIn('name', loc_data)
            self.assertIn('description', loc_data)
            self.assertIn('exits', loc_data)

    def test_all_exits_valid(self):
        """測試所有出口的目標地點存在"""
        for loc_id, loc_data in WORLD_MAP.items():
            for direction, dest_id in loc_data.get('exits', {}).items():
                self.assertIn(dest_id, WORLD_MAP,
                    f"{loc_id} 連接到不存在的地點 {dest_id}")

    def test_tier_requirements_format(self):
        """測試境界要求格式正確"""
        valid_tiers = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

        for loc_id, loc_data in WORLD_MAP.items():
            tier_req = loc_data.get("tier_requirement", 1.0)
            self.assertIn(tier_req, valid_tiers,
                f"{loc_id} 的 tier_requirement 無效: {tier_req}")


class TestLocationContext(unittest.TestCase):
    """測試地點上下文生成"""

    def test_get_location_context(self):
        """測試生成地點上下文"""
        context = get_location_context("qingyun_foot")
        self.assertIn("當前地點", context)
        self.assertIn("青雲門·山腳", context)
        self.assertIn("可行路徑", context)

    def test_unknown_location_context(self):
        """測試不存在地點的上下文"""
        context = get_location_context("不存在的地方")
        self.assertIn("未知地點", context)


class TestRandomEvents(unittest.TestCase):
    """測試隨機事件觸發"""

    def test_event_trigger_with_low_chance(self):
        """測試低機率事件"""
        # qingyun_herb 的 event_chance 是 0.02 (2%)
        # 測試 10 次，理論上不一定觸發
        # 這個測試主要確保函數不會拋出異常
        for _ in range(10):
            should_trigger_random_event("qingyun_herb", player_karma=0)
        # 只要沒有拋出異常就通過
        self.assertTrue(True)

    def test_event_trigger_with_high_multiplier(self):
        """測試高倍率下觸發機率大幅增加"""
        # 使用超高倍率應該大幅增加觸發機率
        # event_chance = 0.10, multiplier = 100.0 -> final_chance = 10.0 (會被 cap 在 1.0)
        result = should_trigger_random_event("qingyun_plaza", player_karma=0, base_multiplier=100.0)
        # 由於 random 的不確定性，我們改為測試多次
        triggered_count = 0
        for _ in range(10):
            if should_trigger_random_event("qingyun_plaza", player_karma=0, base_multiplier=100.0):
                triggered_count += 1
        # 高倍率下應該至少觸發幾次
        self.assertGreater(triggered_count, 0)


if __name__ == '__main__':
    unittest.main()
