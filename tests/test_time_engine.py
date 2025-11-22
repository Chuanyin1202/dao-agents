# tests/test_time_engine.py
# 道·衍 - 時間引擎測試

import unittest
import sys
import os

# 添加 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from time_engine import TimeEngine, advance_game_time, get_current_game_time


class TestTimeEngine(unittest.TestCase):
    def setUp(self):
        self.time = TimeEngine()

    # ========== 初始化測試 ==========
    def test_initial_tick(self):
        """測試初始 tick 為 0"""
        self.assertEqual(self.time.current_tick, 0)

    def test_initial_time_description(self):
        """測試初始時間描述"""
        desc = self.time.get_time_description()
        self.assertIn("第 1 天", desc)
        self.assertIn("深夜", desc)

    # ========== Tick 遞增測試 ==========
    def test_advance_time(self):
        """測試 advance_time 方法"""
        old_tick = self.time.current_tick
        new_tick = self.time.advance_time(10)
        self.assertEqual(new_tick, old_tick + 10)
        self.assertEqual(self.time.current_tick, old_tick + 10)

    def test_advance_time_multiple(self):
        """測試多次推進時間"""
        self.time.advance_time(5)
        self.time.advance_time(3)
        self.assertEqual(self.time.current_tick, 8)

    def test_advance_time_negative(self):
        """測試負值應該拋出異常"""
        with self.assertRaises(ValueError):
            self.time.advance_time(-10)

    # ========== Get/Set Tick 測試 ==========
    def test_get_current_tick(self):
        """測試獲取當前 tick"""
        self.time.advance_time(100)
        self.assertEqual(self.time.get_current_tick(), 100)

    def test_set_current_tick(self):
        """測試設置當前 tick（用於存檔載入）"""
        self.time.set_current_tick(500)
        self.assertEqual(self.time.current_tick, 500)

    def test_set_current_tick_negative(self):
        """測試設置負值應該拋出異常"""
        with self.assertRaises(ValueError):
            self.time.set_current_tick(-10)

    # ========== 時間描述測試 ==========
    def test_time_description_day_1(self):
        """測試第 1 天的描述"""
        self.time.current_tick = 0
        desc = self.time.get_time_description()
        self.assertIn("第 1 天", desc)

    def test_time_description_day_2(self):
        """測試第 2 天的描述"""
        # 1 天 = 144 tick
        self.time.current_tick = 144
        desc = self.time.get_time_description()
        self.assertIn("第 2 天", desc)

    def test_time_description_morning(self):
        """測試上午時段"""
        # 8 小時 = (8 * 144 / 24) = 48 tick
        self.time.current_tick = 48
        desc = self.time.get_time_description()
        self.assertIn("上午", desc)

    def test_time_description_afternoon(self):
        """測試下午時段"""
        # 15 小時 = (15 * 144 / 24) = 90 tick
        self.time.current_tick = 90
        desc = self.time.get_time_description()
        self.assertIn("下午", desc)

    def test_time_description_evening(self):
        """測試晚上時段"""
        # 20 小時 = (20 * 144 / 24) = 120 tick
        self.time.current_tick = 120
        desc = self.time.get_time_description()
        self.assertIn("晚上", desc)

    def test_time_description_late_night(self):
        """測試深夜時段"""
        # 2 小時 = (2 * 144 / 24) = 12 tick
        self.time.current_tick = 12
        desc = self.time.get_time_description()
        self.assertIn("深夜", desc)

    # ========== 行動時間計算測試 ==========
    def test_calculate_time_cost_move(self):
        """測試移動行動的時間消耗"""
        cost = self.time.calculate_time_cost("MOVE")
        self.assertEqual(cost, 3)

    def test_calculate_time_cost_cultivate(self):
        """測試修煉行動的時間消耗"""
        cost = self.time.calculate_time_cost("CULTIVATE")
        self.assertEqual(cost, 10)

    def test_calculate_time_cost_unknown(self):
        """測試未知行動類型（應返回預設值 1）"""
        cost = self.time.calculate_time_cost("UNKNOWN_ACTION")
        self.assertEqual(cost, 1)


class TestTimeEngineFunctions(unittest.TestCase):
    """測試時間引擎的輔助函數"""

    def test_advance_game_time(self):
        """測試 advance_game_time 函數"""
        # 重置時間引擎
        from time_engine import global_time_engine
        global_time_engine.set_current_tick(0)

        result = advance_game_time("MOVE")
        self.assertEqual(result['ticks_passed'], 3)
        self.assertEqual(result['new_tick'], 3)
        self.assertIn('time_description', result)

    def test_get_current_game_time(self):
        """測試 get_current_game_time 函數"""
        from time_engine import global_time_engine
        global_time_engine.set_current_tick(100)

        result = get_current_game_time()
        self.assertEqual(result['tick'], 100)
        self.assertIn('description', result)


class TestTimeEngineLongTerm(unittest.TestCase):
    """測試長期時間推移"""

    def setUp(self):
        self.time = TimeEngine()

    def test_one_day(self):
        """測試一整天（144 tick）"""
        self.time.advance_time(144)
        desc = self.time.get_time_description()
        # 應該是第 2 天
        self.assertIn("第 2 天", desc)

    def test_ten_days(self):
        """測試 10 天"""
        self.time.advance_time(144 * 10)
        desc = self.time.get_time_description()
        self.assertIn("第 11 天", desc)

    def test_large_tick_value(self):
        """測試大 tick 值（100 天）"""
        self.time.current_tick = 144 * 100
        desc = self.time.get_time_description()
        self.assertIn("第 101 天", desc)


if __name__ == '__main__':
    unittest.main()
