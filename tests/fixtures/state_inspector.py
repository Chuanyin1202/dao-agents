# -*- coding: utf-8 -*-
"""
StateInspector - 玩家狀態一致性檢查器
檢查 player_state 的完整性和一致性
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from world_data import WORLD_MAP, get_location_data, get_location_name


class StateInspector:
    """
    檢查玩家狀態的一致性

    使用方式：
        inspector = StateInspector()
        errors = inspector.check_all(player_state)
        if errors:
            print("發現問題:", errors)
    """

    def check_all(self, state: Dict[str, Any]) -> List[str]:
        """
        執行所有檢查

        Returns:
            錯誤列表（空列表表示無問題）
        """
        errors = []

        errors.extend(self.check_location_consistency(state))
        errors.extend(self.check_hp_mp_bounds(state))
        errors.extend(self.check_inventory_integrity(state))
        errors.extend(self.check_tier_validity(state))

        return errors

    def check_location_consistency(self, state: Dict[str, Any]) -> List[str]:
        """
        檢查位置一致性

        檢查項目：
        1. location 和 location_id 是否對應
        2. location_id 是否在地圖上存在
        3. player 的 tier 是否滿足 location 的要求
        """
        errors = []

        location_id = state.get('location_id')
        location_name = state.get('location')
        player_tier = state.get('tier', 1.0)

        # 檢查 1: location_id 是否存在
        if not location_id:
            errors.append("缺少 location_id 欄位")
            return errors  # 無法繼續檢查

        # 檢查 2: location_id 是否在地圖上
        loc_data = get_location_data(location_id)
        if not loc_data:
            errors.append(f"location_id '{location_id}' 不存在於地圖上")
            return errors  # 無法繼續檢查

        # 檢查 3: location 和 location_id 是否對應
        expected_name = loc_data.get('name')
        if location_name != expected_name:
            errors.append(
                f"位置名稱不一致: "
                f"location='{location_name}', "
                f"但 location_id='{location_id}' 對應的名稱是 '{expected_name}'"
            )

        # 檢查 4: tier 是否滿足要求
        required_tier = loc_data.get('tier_requirement', 1.0)
        if player_tier < required_tier:
            errors.append(
                f"玩家境界不足: "
                f"當前位置 '{expected_name}' 需要境界 {required_tier}, "
                f"但玩家境界只有 {player_tier}"
            )

        return errors

    def check_hp_mp_bounds(self, state: Dict[str, Any]) -> List[str]:
        """
        檢查 HP/MP 是否在合法範圍

        檢查項目：
        1. 0 <= hp <= max_hp
        2. 0 <= mp <= max_mp
        3. max_hp, max_mp 是否合理
        """
        errors = []

        hp = state.get('hp', 0)
        max_hp = state.get('max_hp', 100)
        mp = state.get('mp', 0)
        max_mp = state.get('max_mp', 100)

        # 檢查 HP
        if hp < 0:
            errors.append(f"HP 為負數: {hp}")
        if hp > max_hp:
            errors.append(f"HP 超過上限: hp={hp}, max_hp={max_hp}")
        if max_hp <= 0:
            errors.append(f"max_hp 無效: {max_hp}")

        # 檢查 MP
        if mp < 0:
            errors.append(f"MP 為負數: {mp}")
        if mp > max_mp:
            errors.append(f"MP 超過上限: mp={mp}, max_mp={max_mp}")
        if max_mp <= 0:
            errors.append(f"max_mp 無效: {max_mp}")

        return errors

    def check_inventory_integrity(self, state: Dict[str, Any]) -> List[str]:
        """
        檢查背包完整性

        檢查項目：
        1. inventory 是否為 list
        2. 物品名稱格式是否合法
        3. 是否有異常重複（目前不檢查，因為可能允許堆疊）
        """
        errors = []

        inventory = state.get('inventory')

        # 檢查 1: 類型
        if not isinstance(inventory, list):
            errors.append(f"inventory 類型錯誤: 期望 list, 實際 {type(inventory)}")
            return errors

        # 檢查 2: 物品名稱
        for i, item in enumerate(inventory):
            if not isinstance(item, str):
                errors.append(f"inventory[{i}] 類型錯誤: 期望 str, 實際 {type(item)}")
            elif not item.strip():
                errors.append(f"inventory[{i}] 為空字串")

        return errors

    def check_tier_validity(self, state: Dict[str, Any]) -> List[str]:
        """
        檢查境界合法性

        檢查項目：
        1. tier 是否在合理範圍（1.0 ~ 9.9）
        2. tier 格式是否正確（練氣期 1.0-1.9，築基期 2.0-2.9）
        """
        errors = []

        tier = state.get('tier', 1.0)

        # 檢查 1: 範圍
        if tier < 1.0:
            errors.append(f"tier 過低: {tier} (最低應為 1.0)")
        if tier >= 10.0:
            errors.append(f"tier 過高: {tier} (當前最高 9.9)")

        # 檢查 2: 小數部分是否在 0-9 範圍
        decimal_part = round((tier % 1) * 10)
        if decimal_part > 9:
            errors.append(f"tier 格式錯誤: {tier} (小數部分應為 0-9)")

        return errors

    def diff_states(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        對比兩個狀態，找出差異

        Returns:
            {
                "hp_change": int,
                "mp_change": int,
                "location_change": {"from": str, "to": str} or None,
                "items_gained": list,
                "items_lost": list,
                "tier_change": float,
                "unexpected_changes": dict  # 意外的欄位變化
            }
        """
        diff = {
            "hp_change": after.get('hp', 0) - before.get('hp', 0),
            "mp_change": after.get('mp', 0) - before.get('mp', 0),
            "location_change": None,
            "items_gained": [],
            "items_lost": [],
            "tier_change": after.get('tier', 1.0) - before.get('tier', 1.0),
            "unexpected_changes": {}
        }

        # 位置變化
        if before.get('location_id') != after.get('location_id'):
            diff["location_change"] = {
                "from": before.get('location_id'),
                "to": after.get('location_id'),
                "from_name": before.get('location'),
                "to_name": after.get('location')
            }

        # 物品變化
        before_items = set(before.get('inventory', []))
        after_items = set(after.get('inventory', []))

        diff["items_gained"] = list(after_items - before_items)
        diff["items_lost"] = list(before_items - after_items)

        # 意外變化（檢查所有欄位）
        expected_changes = {
            'hp', 'mp', 'location', 'location_id', 'inventory',
            'tier', 'karma', 'tick', 'max_hp', 'max_mp'
        }

        all_keys = set(before.keys()) | set(after.keys())
        for key in all_keys:
            if key not in expected_changes:
                before_val = before.get(key)
                after_val = after.get(key)
                if before_val != after_val:
                    diff["unexpected_changes"][key] = {
                        "before": before_val,
                        "after": after_val
                    }

        return diff

    def validate_state_update(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        expected_changes: Dict[str, Any]
    ) -> List[str]:
        """
        驗證狀態更新是否符合預期

        Args:
            before: 操作前狀態
            after: 操作後狀態
            expected_changes: 預期的變化
                例如: {
                    "hp_change": -10,
                    "location_to": "qingyun_plaza",
                    "items_gained": ["鐵劍"]
                }

        Returns:
            錯誤列表
        """
        errors = []
        diff = self.diff_states(before, after)

        # 檢查 HP 變化
        if "hp_change" in expected_changes:
            expected_hp = expected_changes["hp_change"]
            actual_hp = diff["hp_change"]

            # 支持範圍檢查
            if isinstance(expected_hp, dict):
                if "min" in expected_hp and actual_hp < expected_hp["min"]:
                    errors.append(
                        f"HP 變化過少: 期望 >= {expected_hp['min']}, 實際 {actual_hp}"
                    )
                if "max" in expected_hp and actual_hp > expected_hp["max"]:
                    errors.append(
                        f"HP 變化過多: 期望 <= {expected_hp['max']}, 實際 {actual_hp}"
                    )
            else:
                # 精確匹配
                if actual_hp != expected_hp:
                    errors.append(
                        f"HP 變化不符: 期望 {expected_hp}, 實際 {actual_hp}"
                    )

        # 檢查 MP 變化
        if "mp_change" in expected_changes:
            expected_mp = expected_changes["mp_change"]
            actual_mp = diff["mp_change"]

            if isinstance(expected_mp, dict):
                if "min" in expected_mp and actual_mp < expected_mp["min"]:
                    errors.append(
                        f"MP 變化過少: 期望 >= {expected_mp['min']}, 實際 {actual_mp}"
                    )
                if "max" in expected_mp and actual_mp > expected_mp["max"]:
                    errors.append(
                        f"MP 變化過多: 期望 <= {expected_mp['max']}, 實際 {actual_mp}"
                    )
            else:
                if actual_mp != expected_mp:
                    errors.append(
                        f"MP 變化不符: 期望 {expected_mp}, 實際 {actual_mp}"
                    )

        # 檢查位置變化
        if "location_to" in expected_changes:
            expected_loc = expected_changes["location_to"]
            actual_loc = after.get('location_id')

            if actual_loc != expected_loc:
                errors.append(
                    f"位置變化不符: 期望移動到 {expected_loc}, 實際 {actual_loc}"
                )

        # 檢查物品獲得
        if "items_gained" in expected_changes:
            expected_items = set(expected_changes["items_gained"])
            actual_items = set(diff["items_gained"])

            missing = expected_items - actual_items
            if missing:
                errors.append(f"缺少預期獲得的物品: {list(missing)}")

        # 檢查物品丟失
        if "items_lost" in expected_changes:
            expected_lost = set(expected_changes["items_lost"])
            actual_lost = set(diff["items_lost"])

            unexpected = actual_lost - expected_lost
            if unexpected:
                errors.append(f"意外丟失的物品: {list(unexpected)}")

        return errors
