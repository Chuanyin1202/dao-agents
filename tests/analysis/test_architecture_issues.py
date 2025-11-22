#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架構問題深度分析
找出指令系統的所有不一致和矛盾
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import agent_observer
from world_data import DIRECTION_ALIASES, get_location_data, WORLD_MAP

def analyze_observer_target_extraction():
    """分析 Observer 的 target 提取問題"""
    print("\n" + "="*70)
    print("問題分析 1: Observer 的 target 提取不一致")
    print("="*70)

    test_cases = [
        ("n", "應該提取為 'n' 或 'north'"),
        ("北", "應該提取為 '北' 或 '北方'"),
        ("往北", "應該提取為 '往北' 或 '北'"),
        ("我要往北走", "應該提取為 '北' 或 'north'"),
        ("north", "應該提取為 'north'"),
        ("我要去靈草堂", "應該提取為 '靈草堂'"),
    ]

    print("\n測試 Observer 對不同輸入的 target 提取:")
    problems = []

    for input_text, expected_behavior in test_cases:
        intent = agent_observer(input_text, recent_events=[])
        target = intent.get('target')
        intent_type = intent.get('intent')

        print(f"\n  輸入: '{input_text}'")
        print(f"    intent: {intent_type}")
        print(f"    target: {target}")
        print(f"    期望: {expected_behavior}")

        # 檢查問題
        if intent_type == 'MOVE' and target is None:
            problems.append(f"'{input_text}' 被識別為 MOVE 但 target 為 None")
            print(f"    ❌ 問題: target 為 None!")

        if intent_type == 'MOVE' and target:
            # 檢查 target 能否被 normalize_direction 轉換
            from world_map import normalize_direction
            normalized = normalize_direction(target)
            if normalized:
                print(f"    ✅ target '{target}' 能轉換為 '{normalized}'")
            else:
                problems.append(f"'{input_text}' 的 target '{target}' 無法被標準化")
                print(f"    ❌ 問題: target '{target}' 無法被標準化!")

    print("\n" + "-"*70)
    print(f"發現 {len(problems)} 個問題:")
    for p in problems:
        print(f"  • {p}")

    return problems


def analyze_direction_normalization_gaps():
    """分析方向標準化的漏洞"""
    print("\n" + "="*70)
    print("問題分析 2: 方向標準化的缺口")
    print("="*70)

    from world_map import normalize_direction

    print("\n檢查 DIRECTION_ALIASES 是否完整:")
    print(f"  當前有 {len(DIRECTION_ALIASES)} 個映射")

    # Observer 可能返回的 target 值
    possible_targets = [
        "n", "north", "北", "北方", "往北", "向北",
        "s", "south", "南", "南方", "往南", "向南",
        "e", "east", "東", "東方", "往東", "向東",
        "w", "west", "西", "西方", "往西", "向西",
        "None", None, "",  # 異常情況
    ]

    print("\n測試所有可能的 target 值:")
    missing = []
    for target in possible_targets:
        if target in [None, ""]:
            continue

        normalized = normalize_direction(target)
        if normalized:
            print(f"  ✅ '{target}' -> '{normalized}'")
        else:
            missing.append(target)
            print(f"  ❌ '{target}' -> None (缺少映射!)")

    print("\n" + "-"*70)
    if missing:
        print(f"發現 {len(missing)} 個缺少的映射:")
        for m in missing:
            print(f"  • '{m}' 需要添加到 DIRECTION_ALIASES")
    else:
        print("✅ 所有常見方向都能正確轉換")

    return missing


def analyze_location_display_inconsistency():
    """分析位置顯示的不一致"""
    print("\n" + "="*70)
    print("問題分析 3: 位置顯示名稱 vs ID 的不一致")
    print("="*70)

    print("\n檢查所有地點的 ID 和名稱:")
    for loc_id, loc_data in WORLD_MAP.items():
        name = loc_data.get('name')
        print(f"  ID: {loc_id:<20} 名稱: {name}")

    print("\n檢查玩家可能遇到的問題:")
    problems = []

    # 場景 1: 玩家在「青雲門·外門廣場」想往北
    print("\n場景 1: 玩家在外門廣場 (qingyun_plaza) 想往北")
    plaza = get_location_data("qingyun_plaza")
    exits = plaza.get('exits', {})
    print(f"  可用出口: {exits}")

    if 'north' in exits:
        dest_id = exits['north']
        dest_name = WORLD_MAP[dest_id]['name']
        print(f"  往北會到: {dest_name} ({dest_id})")

        # 模擬 Observer 可能返回的 target
        possible_observer_targets = [
            ("n", "單字母"),
            ("北", "中文"),
            ("青雲門·內門", "目的地名稱"),
            (dest_name, "完整目的地名稱"),
        ]

        for target, description in possible_observer_targets:
            from world_map import normalize_direction
            normalized = normalize_direction(target)

            if normalized:
                print(f"    ✅ Observer 返回 '{target}' ({description}) -> 能轉換為 '{normalized}'")
            else:
                # 檢查是否為地點名稱
                if target == dest_name or target in [d['name'] for d in WORLD_MAP.values()]:
                    print(f"    ⚠️ Observer 返回 '{target}' ({description}) -> 這是地點名稱，不是方向!")
                    problems.append(f"Observer 可能把方向解析為地點名稱: '{target}'")
                else:
                    print(f"    ❌ Observer 返回 '{target}' ({description}) -> 無法處理!")
                    problems.append(f"Observer 返回無法處理的 target: '{target}'")

    print("\n" + "-"*70)
    if problems:
        print(f"發現 {len(problems)} 個問題:")
        for p in problems:
            print(f"  • {p}")

    return problems


def analyze_error_message_confusion():
    """分析錯誤訊息的混淆"""
    print("\n" + "="*70)
    print("問題分析 4: 錯誤訊息的混淆與誤導")
    print("="*70)

    print("\n當前錯誤訊息格式分析:")

    # 模擬用戶在外門廣場輸入 'n'
    print("\n場景: 用戶在外門廣場 (qingyun_plaza)，輸入 'n'")

    # Observer 誤判
    intent = agent_observer("n", recent_events=[])
    print(f"\n  Observer 解析結果: {intent}")

    # 如果 target 是地點名稱
    if intent.get('target') and '門' in str(intent.get('target')):
        target_location = intent.get('target')
        print(f"\n  ❌ 問題: Observer 把方向 'n' 解析成地點名稱 '{target_location}'")
        print(f"  結果: 系統認為玩家想從外門廣場移動到 {target_location}")
        print(f"  但玩家已經在外門廣場了！")
        print(f"\n  錯誤訊息會顯示:")
        print(f"    ❌ 此處無法往{target_location}。可用方向: 南, 北, 西")
        print(f"\n  這非常誤導！應該顯示:")
        print(f"    ℹ️  無法識別方向 'n'。可用方向: 南(south), 北(north), 西(west)")

    return True


def analyze_handle_shortcut_issues():
    """分析 handle_shortcut 的設計問題"""
    print("\n" + "="*70)
    print("問題分析 5: handle_shortcut 的設計缺陷")
    print("="*70)

    print("\n當前 handle_shortcut 的流程:")
    print("  1. 用戶按 'm'")
    print("  2. 顯示方向選單（提示可以輸入 'n'）")
    print("  3. 用戶輸入 'n'")
    print("  4. handle_shortcut 返回 'n'")
    print("  5. 'n' 被送到 agent_observer 解析")
    print("  6. ❌ Observer 無法正確識別單字母方向")

    print("\n設計缺陷:")
    print("  ❌ 問題 1: 提示說可以輸入 'n'，但系統無法處理")
    print("  ❌ 問題 2: handle_shortcut 返回的是用戶原始輸入，而非標準化指令")
    print("  ❌ 問題 3: 依賴 AI 解析單字母，但 AI 無法可靠識別")
    print("  ❌ 問題 4: 沒有統一的「方向輸入」處理層")

    print("\n應該的設計:")
    print("  ✅ 方案 A: handle_shortcut 直接轉換為完整指令")
    print("     'm' + 'n' -> '我要往北走'")
    print("     然後送給 Observer，AI 能正確識別")
    print("\n  ✅ 方案 B: 跳過 AI，直接處理方向輸入")
    print("     'm' + 'n' -> 直接調用 validate_movement('當前位置', 'north', tier)")
    print("     不經過 Observer")

    return True


if __name__ == "__main__":
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        道·衍 - 架構問題深度分析                               ║")
    print("║        找出指令系統的所有不一致和矛盾                          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    all_problems = []

    try:
        # 問題 1: Observer target 提取
        problems_1 = analyze_observer_target_extraction()
        all_problems.extend(problems_1)

        # 問題 2: 方向標準化缺口
        problems_2 = analyze_direction_normalization_gaps()
        all_problems.extend([f"缺少映射: {m}" for m in problems_2])

        # 問題 3: 位置顯示不一致
        problems_3 = analyze_location_display_inconsistency()
        all_problems.extend(problems_3)

        # 問題 4: 錯誤訊息混淆
        analyze_error_message_confusion()

        # 問題 5: handle_shortcut 設計缺陷
        analyze_handle_shortcut_issues()

        # 最終報告
        print("\n" + "="*70)
        print("最終架構問題報告")
        print("="*70)

        print(f"\n發現 {len(all_problems)} 個具體問題:")
        for i, problem in enumerate(all_problems, 1):
            print(f"  {i}. {problem}")

        print("\n" + "="*70)
        print("核心架構缺陷:")
        print("="*70)
        print("""
1. 【指令處理不一致】
   • 有些指令由 AI 解析（自然語言）
   • 有些指令應該直接處理（方向、快捷鍵）
   • 但目前所有指令都強制經過 AI，導致單字母無法識別

2. 【提示與實際處理脫節】
   • 提示說可以輸入 'n'
   • 但系統無法正確處理 'n'
   • 用戶體驗極差

3. 【Observer 的 target 提取不穩定】
   • 有時返回 None
   • 有時返回方向（'北方'）
   • 有時返回地點名稱（'青雲門·內門'）
   • 無法可靠預測

4. 【缺少統一的方向處理層】
   • normalize_direction 只負責標準化
   • 但沒有統一入口處理所有方向輸入
   • 導致處理邏輯分散在多處

建議的重構方案:
  → 詳見 ARCHITECTURE_REFACTOR.md
        """)

    except Exception as e:
        print(f"\n❌ 分析過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
