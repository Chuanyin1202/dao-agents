#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實際遊戲測試 - 模擬真實用戶操作
"""

import sys
import os
sys.path.insert(0, 'src')

from io import StringIO
from main import DaoGame

def test_direction_movement():
    """測試方向移動在實際遊戲中是否工作"""

    print("=== 測試 1: 創建遊戲實例 ===")
    game = DaoGame()
    print("✅ 遊戲實例創建成功")

    print("\n=== 測試 2: 創建測試玩家 ===")
    # 創建測試玩家
    game.player_state = {
        'name': '測試玩家',
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
    print("✅ 測試玩家創建成功")

    print("\n=== 測試 3: 測試方向識別 ===")
    test_inputs = ['n', 's', 'e', 'w', '北', '南', 'north']
    for inp in test_inputs:
        is_dir = game.is_direction_input(inp)
        print(f"  is_direction_input('{inp}'): {is_dir}")
        if not is_dir:
            print(f"❌ 失敗：'{inp}' 未被識別為方向")
            return False
    print("✅ 所有方向輸入都能正確識別")

    print("\n=== 測試 4: 測試實際移動（不調用 AI）===")
    print(f"當前位置: {game.player_state['location']}")

    # 測試往北移動
    print("\n嘗試往北移動...")
    try:
        success = game.handle_direction_movement('n')
        if success:
            print(f"✅ 移動成功！新位置: {game.player_state['location']}")
            print(f"   位置 ID: {game.player_state['location_id']}")
        else:
            print("❌ 移動失敗")
            return False
    except Exception as e:
        print(f"❌ 移動時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n=== 測試 5: 驗證狀態更新 ===")
    if game.player_state['location_id'] != 'qingyun_foot':
        print(f"✅ 位置已更新: {game.player_state['location_id']}")
    else:
        print("❌ 位置未更新")
        return False

    print("\n" + "="*50)
    print("🎉 所有測試通過！遊戲方向移動功能正常工作！")
    print("="*50)
    return True

if __name__ == "__main__":
    # 設置環境變數避免 AI 調用
    os.environ['DEBUG'] = 'true'

    success = test_direction_movement()
    sys.exit(0 if success else 1)
