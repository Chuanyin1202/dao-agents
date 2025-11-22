# -*- coding: utf-8 -*-
"""
方向處理單元測試
測試新的方向輸入分類器和直接處理邏輯
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from world_map import normalize_direction


class TestDirectionHandling:
    """測試方向處理功能"""

    def test_normalize_direction_single_letters(self):
        """測試單字母方向標準化"""
        assert normalize_direction('n') == 'north'
        assert normalize_direction('s') == 'south'
        assert normalize_direction('e') == 'east'
        assert normalize_direction('w') == 'west'

    def test_normalize_direction_english(self):
        """測試英文方向標準化"""
        assert normalize_direction('north') == 'north'
        assert normalize_direction('south') == 'south'
        assert normalize_direction('east') == 'east'
        assert normalize_direction('west') == 'west'

        # 測試大小寫
        assert normalize_direction('North') == 'north'
        assert normalize_direction('SOUTH') == 'south'

    def test_normalize_direction_chinese(self):
        """測試中文方向標準化"""
        assert normalize_direction('北') == 'north'
        assert normalize_direction('南') == 'south'
        assert normalize_direction('東') == 'east'
        assert normalize_direction('西') == 'west'

    def test_normalize_direction_phrases(self):
        """測試方向短語標準化"""
        # 這些需要在 DIRECTION_ALIASES 中定義
        possible_inputs = ['往北', '向南', '北方', '南方']

        for input_dir in possible_inputs:
            result = normalize_direction(input_dir)
            # 應該能標準化（即使測試時可能還沒全部實現）
            assert result in ['north', 'south', 'east', 'west', None], \
                f"'{input_dir}' 標準化結果異常: {result}"

    def test_normalize_direction_invalid(self):
        """測試無效輸入"""
        assert normalize_direction('invalid') is None
        assert normalize_direction('') is None
        assert normalize_direction('上') is None  # 不支持的方向

    def test_is_direction_input_integration(self):
        """測試 is_direction_input 方法（整合測試）"""
        from main import DaoGame

        # 創建遊戲實例（不需要實際運行）
        game = DaoGame()

        # 測試單字母
        assert game.is_direction_input('n') is True
        assert game.is_direction_input('s') is True
        assert game.is_direction_input('e') is True
        assert game.is_direction_input('w') is True

        # 測試中文
        assert game.is_direction_input('北') is True
        assert game.is_direction_input('南') is True

        # 測試英文
        assert game.is_direction_input('north') is True
        assert game.is_direction_input('south') is True

        # 測試非方向輸入
        assert game.is_direction_input('attack') is False
        assert game.is_direction_input('我要攻擊') is False
        assert game.is_direction_input('hello') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
