# -*- coding: utf-8 -*-
"""
UI 一致性測試
測試 UI 提示與實際功能的一致性

這個測試會發現當前的核心問題：
- 移動選單顯示 "北 (n)"，但輸入 'n' 無法使用
"""

import sys
import pytest
from pathlib import Path

# 添加路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agent import agent_observer
from world_map import normalize_direction, validate_movement
from world_data import get_location_data, DIRECTION_ALIASES


class TestUIConsistency:
    """測試 UI 提示與實際功能的一致性"""

    def test_direction_menu_single_letter_shortcuts_work(self):
        """
        測試：移動選單中顯示的單字母快捷鍵能正常使用

        當前狀態：✅ 已修復
        修復方案：繞過 Observer，直接處理方向輸入

        這個測試驗證完整的遊戲流程：
        - UI 提示說可以用 'n'
        - 遊戲系統能正確識別並處理 'n'
        """
        from main import DaoGame

        # 模擬場景：玩家在山腳，移動選單顯示「北 (n) → 青雲門·外門廣場」
        current_location = "qingyun_foot"
        loc_data = get_location_data(current_location)
        exits = loc_data.get('exits', {})

        # 獲取所有可用方向的單字母簡寫
        direction_shortcuts = {
            'north': 'n',
            'south': 's',
            'east': 'e',
            'west': 'w'
        }

        failures = []
        game = DaoGame()

        for direction, shortcut in direction_shortcuts.items():
            if direction not in exits:
                continue  # 跳過不可用的方向

            print(f"\n測試方向: {direction} (快捷鍵: {shortcut})")

            # 步驟 1: 遊戲能否識別單字母為方向輸入？
            is_direction = game.is_direction_input(shortcut)
            print(f"  is_direction_input('{shortcut}'): {is_direction}")

            if not is_direction:
                failures.append({
                    'shortcut': shortcut,
                    'direction': direction,
                    'problem': f"遊戲未將 '{shortcut}' 識別為方向輸入",
                })
                continue

            # 步驟 2: 能否被標準化為正確方向？
            normalized = normalize_direction(shortcut)
            print(f"  normalize_direction('{shortcut}'): {normalized}")

            if normalized != direction:
                failures.append({
                    'shortcut': shortcut,
                    'direction': direction,
                    'problem': f"標準化結果錯誤: 期望 {direction}, 實際 {normalized}",
                })
                continue

            # 步驟 3: 移動驗證是否通過？
            validation = validate_movement(current_location, direction, 1.0)
            print(f"  validate_movement: {validation.get('valid')}")

            if not validation.get('valid'):
                failures.append({
                    'shortcut': shortcut,
                    'direction': direction,
                    'problem': f"移動驗證失敗: {validation.get('reason')}",
                })
                continue

            print(f"  ✅ '{shortcut}' 完整流程成功")

        # 斷言
        if failures:
            error_msg = "\n\n❌ UI 一致性測試失敗：移動選單顯示的快捷鍵無法使用\n\n"
            error_msg += "失敗詳情:\n"

            for i, failure in enumerate(failures, 1):
                error_msg += f"\n{i}. 快捷鍵 '{failure['shortcut']}' (方向: {failure['direction']})\n"
                error_msg += f"   問題: {failure['problem']}\n"

            error_msg += "\n💡 問題：遊戲系統無法正確處理 UI 提示的快捷鍵\n"

            pytest.fail(error_msg)
        else:
            print("\n\n✅ 所有快捷鍵都能正常工作！")

    def test_direction_aliases_completeness(self):
        """
        測試：DIRECTION_ALIASES 是否涵蓋所有 Observer 可能返回的 target

        這個測試檢查：
        - Observer 返回的 target 值能否被 normalize_direction 轉換
        """
        # Observer 可能返回的 target 值（基於實際測試）
        possible_targets = [
            ('n', 'north'),
            ('s', 'south'),
            ('e', 'east'),
            ('w', 'west'),
            ('north', 'north'),
            ('south', 'south'),
            ('east', 'east'),
            ('west', 'west'),
            ('北', 'north'),
            ('南', 'south'),
            ('東', 'east'),
            ('西', 'west'),
            ('北方', 'north'),
            ('南方', 'south'),
            ('東方', 'east'),
            ('西方', 'west'),
            ('往北', 'north'),
            ('往南', 'south'),
            ('往東', 'east'),
            ('往西', 'west'),
        ]

        missing = []

        for target, expected_direction in possible_targets:
            normalized = normalize_direction(target)

            if not normalized:
                missing.append({
                    'target': target,
                    'expected': expected_direction,
                    'problem': f"'{target}' 無法被標準化"
                })
            elif normalized != expected_direction:
                missing.append({
                    'target': target,
                    'expected': expected_direction,
                    'problem': f"'{target}' 標準化為 {normalized}，期望 {expected_direction}"
                })

        if missing:
            error_msg = "\n\n❌ DIRECTION_ALIASES 不完整\n\n"
            for item in missing:
                error_msg += f"  • {item['problem']}\n"

            error_msg += "\n需要添加到 DIRECTION_ALIASES:\n"
            for item in missing:
                error_msg += f"  '{item['target']}': '{item['expected']}',\n"

            pytest.fail(error_msg)

    def test_observer_direction_recognition_rate(self):
        """
        測試：Observer 對方向輸入的識別成功率

        期望：成功率 >= 80%
        當前：成功率約 20%（只有 '北' 能識別）
        """
        test_inputs = [
            ('n', 'north', '單字母 n'),
            ('s', 'south', '單字母 s'),
            ('e', 'east', '單字母 e'),
            ('w', 'west', '單字母 w'),
            ('北', 'north', '中文 北'),
            ('南', 'south', '中文 南'),
            ('東', 'east', '中文 東'),
            ('西', 'west', '中文 西'),
            ('north', 'north', '英文 north'),
            ('往北', 'north', '往北'),
            ('我要往北走', 'north', '完整句子'),
        ]

        results = []

        for input_text, expected_dir, description in test_inputs:
            intent = agent_observer(input_text, recent_events=[])

            is_move = intent.get('intent') == 'MOVE'
            target = intent.get('target')
            normalized = normalize_direction(target) if target else None

            success = is_move and normalized == expected_dir

            results.append({
                'input': input_text,
                'description': description,
                'success': success,
                'intent_type': intent.get('intent'),
                'target': target,
                'normalized': normalized,
                'expected': expected_dir
            })

        # 計算成功率
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        success_rate = (success_count / total_count) * 100

        print(f"\n\n📊 Observer 方向識別成功率: {success_count}/{total_count} ({success_rate:.1f}%)\n")

        for r in results:
            status = "✅" if r['success'] else "❌"
            print(f"{status} {r['description']:20} | 輸入: {r['input']:15} | intent: {r['intent_type']:10} | target: {r['target']}")

        # 斷言：成功率應 >= 80%
        assert success_rate >= 80.0, f"\n\n❌ Observer 方向識別成功率過低: {success_rate:.1f}% (期望 >= 80%)\n\n" \
                                      f"這導致用戶無法使用單字母或簡短方向指令。\n" \
                                      f"建議：\n" \
                                      f"  1. 在 handle_shortcut 中將方向轉換為完整指令\n" \
                                      f"  2. 或者繞過 Observer，直接處理方向輸入\n"

    def test_all_map_locations_reachable(self):
        """
        測試：所有地圖位置的出口都可達且有效

        檢查：
        1. 出口指向的 location_id 存在
        2. 反向路徑存在（如果 A→B，則應有 B→A）
        """
        from world_data import WORLD_MAP

        errors = []

        for loc_id, loc_data in WORLD_MAP.items():
            exits = loc_data.get('exits', {})

            for direction, dest_id in exits.items():
                # 檢查 1: 目的地存在
                if dest_id not in WORLD_MAP:
                    errors.append(
                        f"{loc_id} 的 {direction} 出口指向不存在的 {dest_id}"
                    )
                    continue

                # 檢查 2: 反向路徑（可選，視設計而定）
                # 暫時跳過，因為可能存在單向路徑

        assert not errors, f"\n\n❌ 地圖完整性檢查失敗:\n" + "\n".join(f"  • {e}" for e in errors)


if __name__ == "__main__":
    # 可以直接執行此文件進行測試
    pytest.main([__file__, "-v", "-s"])
