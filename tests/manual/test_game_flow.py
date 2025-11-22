#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
遊戲流程自動化測試
模擬真實玩家操作，找出所有問題
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import agent_observer, extract_json_from_text
from world_map import validate_movement, normalize_direction
from world_data import get_location_data, DIRECTION_ALIASES

def test_observer_direction_parsing():
    """測試 Observer 對方向的解析"""
    print("\n" + "="*70)
    print("測試 1: Observer 對方向輸入的解析")
    print("="*70)

    test_cases = [
        ("n", "north", "單字母 n"),
        ("北", "north", "中文 北"),
        ("north", "north", "英文 north"),
        ("往北", "north", "往北"),
        ("我要往北走", "north", "完整句子"),
    ]

    results = []
    for input_text, expected_direction, description in test_cases:
        print(f"\n測試輸入: '{input_text}' ({description})")

        # 模擬 Observer 解析
        try:
            intent = agent_observer(input_text, recent_events=[])

            print(f"  解析結果:")
            print(f"    intent: {intent.get('intent')}")
            print(f"    target: {intent.get('target')}")
            print(f"    confidence: {intent.get('confidence')}")

            # 檢查是否正確識別
            is_move = intent.get('intent') == 'MOVE'
            target = intent.get('target', '')

            # 標準化目標
            normalized = normalize_direction(target) if target else None

            success = is_move and normalized == expected_direction

            results.append({
                'input': input_text,
                'description': description,
                'success': success,
                'intent': intent.get('intent'),
                'target': target,
                'normalized': normalized,
                'expected': expected_direction
            })

            if success:
                print(f"  ✅ 成功識別為往{expected_direction}移動")
            else:
                print(f"  ❌ 失敗！")
                print(f"     期望: MOVE intent, target 能轉換為 {expected_direction}")
                print(f"     實際: intent={intent.get('intent')}, normalized={normalized}")

        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            results.append({
                'input': input_text,
                'description': description,
                'success': False,
                'error': str(e)
            })

    # 總結
    print("\n" + "-"*70)
    print("測試結果總結:")
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")

    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"  {status} {r['description']}: {r['input']}")

    return results


def test_direction_normalization():
    """測試方向標準化"""
    print("\n" + "="*70)
    print("測試 2: 方向標準化功能")
    print("="*70)

    print("\n當前的 DIRECTION_ALIASES 映射:")
    for key, value in sorted(DIRECTION_ALIASES.items()):
        print(f"  '{key}' -> '{value}'")

    test_cases = [
        "n", "s", "e", "w",
        "north", "south", "east", "west",
        "北", "南", "東", "西",
        "N", "NORTH", "North",  # 測試大小寫
        "invalid", "", None      # 測試無效輸入
    ]

    print("\n測試各種輸入:")
    for input_val in test_cases:
        result = normalize_direction(input_val) if input_val else None
        print(f"  normalize_direction('{input_val}') -> {result}")

    return True


def test_movement_validation():
    """測試移動驗證邏輯"""
    print("\n" + "="*70)
    print("測試 3: 移動驗證邏輯")
    print("="*70)

    # 測試從山腳往北移動
    print("\n測試場景: 從青雲門·山腳(qingyun_foot)往北移動")

    location = get_location_data("qingyun_foot")
    print(f"\n當前位置數據:")
    print(f"  ID: qingyun_foot")
    print(f"  名稱: {location.get('name')}")
    print(f"  可用出口: {location.get('exits')}")

    test_directions = [
        ("north", True, "qingyun_plaza", "標準方向 north"),
        ("n", True, "qingyun_plaza", "縮寫 n"),
        ("北", True, "qingyun_plaza", "中文 北"),
        ("south", False, None, "無效方向 south"),
        ("invalid", False, None, "無效方向 invalid"),
    ]

    print("\n測試各種方向輸入:")
    for direction, should_succeed, expected_dest, description in test_directions:
        print(f"\n  測試: {description} ('{direction}')")

        # 先標準化
        normalized = normalize_direction(direction)
        print(f"    標準化後: {normalized}")

        # 驗證移動
        validation = validate_movement("qingyun_foot", direction, 1.0)

        print(f"    驗證結果: valid={validation['valid']}")
        if validation['valid']:
            print(f"      目的地ID: {validation.get('destination_id')}")
            print(f"      目的地名: {validation.get('destination_name')}")

            if validation.get('destination_id') == expected_dest:
                print(f"    ✅ 正確")
            else:
                print(f"    ❌ 目的地不符 (期望: {expected_dest})")
        else:
            print(f"      原因: {validation.get('reason')}")
            if should_succeed:
                print(f"    ❌ 應該成功但失敗了")
            else:
                print(f"    ✅ 正確拒絕")

    return True


def test_complete_move_flow():
    """測試完整的移動流程（模擬 handle_shortcut + Observer + validate）"""
    print("\n" + "="*70)
    print("測試 4: 完整移動流程模擬")
    print("="*70)

    # 模擬用戶按 m 然後選擇 n
    print("\n場景: 用戶在山腳，按 'm' 然後選擇 'n'")
    print("-"*50)

    current_location = "qingyun_foot"
    user_choice = "n"

    print(f"1️⃣ 當前位置: {current_location}")
    print(f"2️⃣ 用戶選擇: {user_choice}")

    # Step 1: handle_shortcut 返回什麼？
    print(f"\n3️⃣ handle_shortcut() 會返回: '{user_choice}'")

    # Step 2: Observer 解析
    print(f"\n4️⃣ agent_observer('{user_choice}') 解析中...")
    intent = agent_observer(user_choice, recent_events=[])
    print(f"   解析結果: {intent}")

    # Step 3: 提取 target
    target = intent.get('target', '')
    print(f"\n5️⃣ 提取的 target: '{target}'")

    # Step 4: 標準化方向
    normalized = normalize_direction(target) if target else None
    print(f"6️⃣ normalize_direction('{target}') -> {normalized}")

    # Step 5: 驗證移動
    print(f"\n7️⃣ validate_movement('{current_location}', '{normalized or target}', 1.0)")
    validation = validate_movement(current_location, normalized or target, 1.0)
    print(f"   驗證結果: {validation}")

    # 總結
    print("\n" + "-"*50)
    if validation.get('valid'):
        print("✅ 完整流程成功！")
        print(f"   玩家將移動到: {validation.get('destination_name')}")
    else:
        print("❌ 完整流程失敗！")
        print(f"   失敗原因: {validation.get('reason')}")
        print("\n🔍 失敗點分析:")
        if intent.get('intent') != 'MOVE':
            print("   ⚠️ Observer 未正確識別為 MOVE 意圖")
        if not target:
            print("   ⚠️ Observer 未提取 target")
        if not normalized:
            print("   ⚠️ normalize_direction 無法轉換 target")

    return validation.get('valid', False)


def test_inspect_vs_move():
    """測試 INSPECT 和 MOVE 意圖的區別"""
    print("\n" + "="*70)
    print("測試 5: INSPECT vs MOVE 意圖識別")
    print("="*70)

    test_cases = [
        ("l", "INSPECT", "快捷鍵 l"),
        ("我要查看周圍環境", "INSPECT", "查看周圍"),
        ("觀察環境", "INSPECT", "觀察環境"),
        ("m", "MOVE", "快捷鍵 m（但會被 handle_shortcut 處理）"),
        ("我要往北走", "MOVE", "明確移動"),
        ("北", "MOVE", "單字方向"),
    ]

    for input_text, expected_intent, description in test_cases:
        print(f"\n測試: {description}")
        print(f"  輸入: '{input_text}'")

        intent = agent_observer(input_text, recent_events=[])
        actual_intent = intent.get('intent')

        if actual_intent == expected_intent:
            print(f"  ✅ 正確識別為 {expected_intent}")
        else:
            print(f"  ❌ 識別錯誤！期望 {expected_intent}，實際 {actual_intent}")

        print(f"  完整結果: {intent}")

    return True


if __name__ == "__main__":
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        道·衍 - 遊戲流程自動化測試                             ║")
    print("║        找出所有架構問題                                        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    try:
        # 測試 1: Observer 方向解析
        observer_results = test_observer_direction_parsing()

        # 測試 2: 方向標準化
        test_direction_normalization()

        # 測試 3: 移動驗證
        test_movement_validation()

        # 測試 4: 完整流程
        flow_success = test_complete_move_flow()

        # 測試 5: INSPECT vs MOVE
        test_inspect_vs_move()

        # 最終總結
        print("\n" + "="*70)
        print("最終總結")
        print("="*70)

        observer_success = sum(1 for r in observer_results if r['success'])
        observer_total = len(observer_results)

        print(f"\n✅ Observer 方向識別: {observer_success}/{observer_total} 成功")
        print(f"{'✅' if flow_success else '❌'} 完整移動流程: {'成功' if flow_success else '失敗'}")

        print("\n關鍵發現:")
        if observer_success < observer_total:
            print("  ⚠️ Observer 無法正確識別所有方向輸入")
            print("  → 建議: 在 handle_shortcut 中將方向轉換為完整指令")

        if not flow_success:
            print("  ⚠️ 完整移動流程存在問題")
            print("  → 需要修復 Observer 或 handle_shortcut")

    except KeyboardInterrupt:
        print("\n\n測試中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
