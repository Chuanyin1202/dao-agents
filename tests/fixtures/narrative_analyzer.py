# -*- coding: utf-8 -*-
"""
NarrativeAnalyzer - 劇情與狀態一致性分析器
分析劇情敘述與狀態更新是否一致
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from world_data import WORLD_MAP


class NarrativeAnalyzer:
    """
    分析劇情敘述與狀態更新的一致性

    使用方式：
        analyzer = NarrativeAnalyzer()
        result = analyzer.analyze_consistency(
            narrative="你往北走去,來到了青雲門·外門廣場",
            state_update={"location_new": "青雲門·外門廣場"},
            player_state_before=...,
            player_state_after=...
        )
        if not result["consistent"]:
            print("發現不一致:", result["errors"])
    """

    # 關鍵詞定義
    DAMAGE_KEYWORDS = [
        '受傷', '疼痛', '吐血', '重創', '負傷', '流血',
        '傷口', '痛苦', '受創', '損傷', '擊傷'
    ]

    MOVEMENT_KEYWORDS = [
        '來到', '抵達', '進入', '走進', '前往', '移動',
        '到達', '踏入', '闖入', '離開', '走出'
    ]

    ITEM_GAIN_KEYWORDS = [
        '獲得', '得到', '拾取', '撿到', '拿到', '獲取',
        '收到', '取得', '發現', '找到'
    ]

    ITEM_LOSS_KEYWORDS = [
        '失去', '丟失', '掉落', '遺失', '被搶', '損壞',
        '消耗', '使用', '交給', '送出'
    ]

    def analyze_consistency(
        self,
        narrative: str,
        state_update: Dict[str, Any],
        player_state_before: Dict[str, Any],
        player_state_after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        全面分析一致性

        Returns:
            {
                "consistent": bool,
                "errors": [錯誤列表],
                "warnings": [警告列表],
                "suggestions": [建議列表]
            }
        """
        errors = []
        warnings = []
        suggestions = []

        # 檢查 HP 一致性
        hp_result = self._check_hp_consistency(
            narrative, state_update, player_state_before, player_state_after
        )
        errors.extend(hp_result["errors"])
        warnings.extend(hp_result["warnings"])

        # 檢查位置一致性
        location_result = self._check_location_consistency(
            narrative, state_update, player_state_before, player_state_after
        )
        errors.extend(location_result["errors"])
        warnings.extend(location_result["warnings"])

        # 檢查物品一致性
        item_result = self._check_item_consistency(
            narrative, state_update, player_state_before, player_state_after
        )
        errors.extend(item_result["errors"])
        warnings.extend(item_result["warnings"])

        return {
            "consistent": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _check_hp_consistency(
        self,
        narrative: str,
        state_update: Dict,
        state_before: Dict,
        state_after: Dict
    ) -> Dict:
        """檢查 HP 變化一致性"""
        errors = []
        warnings = []

        hp_change = state_update.get('hp_change', 0)
        actual_hp_change = state_after.get('hp', 0) - state_before.get('hp', 0)

        # 檢查劇情是否提到受傷
        mentions_damage = any(kw in narrative for kw in self.DAMAGE_KEYWORDS)

        # 檢查主語（是玩家受傷還是 NPC）
        if mentions_damage:
            is_player_damaged = self._is_player_subject(narrative, self.DAMAGE_KEYWORDS)

            if is_player_damaged and hp_change >= 0:
                errors.append(
                    f"劇情提到玩家受傷，但 hp_change={hp_change} (應為負數)"
                )
            elif is_player_damaged and hp_change < 0:
                # 檢查數值是否合理
                damage_hint = self.extract_damage_hints(narrative)
                if damage_hint and abs(hp_change) != damage_hint:
                    warnings.append(
                        f"劇情暗示傷害為 {damage_hint}，但實際 hp_change={hp_change}"
                    )

        # 檢查是否有未解釋的 HP 變化
        if actual_hp_change < 0 and not mentions_damage:
            warnings.append(
                f"HP 減少了 {abs(actual_hp_change)} 點，但劇情未提到受傷"
            )

        return {"errors": errors, "warnings": warnings}

    def _check_location_consistency(
        self,
        narrative: str,
        state_update: Dict,
        state_before: Dict,
        state_after: Dict
    ) -> Dict:
        """檢查位置變化一致性"""
        errors = []
        warnings = []

        location_new = state_update.get('location_new')
        location_id_new = state_update.get('location_id')

        # 檢查劇情是否提到移動
        mentions_movement = any(kw in narrative for kw in self.MOVEMENT_KEYWORDS)

        # 提取劇情中提到的地點
        mentioned_locations = self.extract_mentioned_locations(narrative)

        if location_new and not mentions_movement:
            warnings.append(
                f"位置變為 {location_new}，但劇情未提到移動"
            )

        if mentions_movement and not location_new:
            warnings.append(
                "劇情提到移動，但位置未變化"
            )

        # 檢查劇情提到的地點是否與實際位置一致
        if location_new and mentioned_locations:
            if location_new not in mentioned_locations:
                # 檢查 location_id 對應的名稱
                found_match = False
                for loc_id, loc_data in WORLD_MAP.items():
                    if loc_data['name'] == location_new:
                        if loc_data['name'] in mentioned_locations:
                            found_match = True
                            break

                if not found_match:
                    warnings.append(
                        f"劇情提到地點 {mentioned_locations}，但實際位置為 {location_new}"
                    )

        return {"errors": errors, "warnings": warnings}

    def _check_item_consistency(
        self,
        narrative: str,
        state_update: Dict,
        state_before: Dict,
        state_after: Dict
    ) -> Dict:
        """檢查物品變化一致性"""
        errors = []
        warnings = []

        items_gained = state_update.get('items_gained', [])
        items_lost = state_update.get('items_lost', [])

        # 檢查劇情是否提到獲得物品
        mentions_gain = any(kw in narrative for kw in self.ITEM_GAIN_KEYWORDS)
        mentioned_items = self.extract_mentioned_items(narrative)

        if items_gained and not mentions_gain:
            warnings.append(
                f"獲得物品 {items_gained}，但劇情未提到"
            )

        if mentions_gain and not items_gained:
            warnings.append(
                "劇情提到獲得物品，但背包未變化"
            )

        # 檢查物品名稱一致性
        if items_gained and mentioned_items:
            for item in items_gained:
                if item not in mentioned_items:
                    warnings.append(
                        f"獲得物品 '{item}'，但劇情未提到此物品（提到: {mentioned_items}）"
                    )

        return {"errors": errors, "warnings": warnings}

    def _is_player_subject(
        self,
        narrative: str,
        keywords: List[str]
    ) -> bool:
        """
        檢查關鍵詞的主語是否為玩家

        Returns:
            True - 玩家是主語
            False - NPC 是主語
        """
        for keyword in keywords:
            if keyword not in narrative:
                continue

            # 找到關鍵詞位置
            keyword_pos = narrative.find(keyword)

            # 檢查前文（20 個字符）
            context_start = max(0, keyword_pos - 20)
            context_before = narrative[context_start:keyword_pos]

            # NPC 指示詞
            npc_indicators = [
                '牠', '他', '她', '它', '靈獸', '敵人', '師兄', '師姐',
                '長老', '弟子', '霜焰獅', '妖獸', '魔獸', '對手', '修士',
                '獸', '人', '獅', '虎', '狼', '蛇', '龍', '鳳'
            ]

            for indicator in npc_indicators:
                if indicator in context_before:
                    return False  # NPC 是主語

            # 玩家指示詞
            player_indicators = ['你', '自己', '你的', '身體', '傷口', '雙手']

            for indicator in player_indicators:
                if indicator in context_before:
                    return True  # 玩家是主語

        # 保守預設：認為是玩家
        return True

    def extract_mentioned_locations(self, narrative: str) -> List[str]:
        """從劇情中提取提到的地點"""
        locations = []

        # 從地圖數據中獲取所有地點名稱
        all_location_names = [loc['name'] for loc in WORLD_MAP.values()]

        for loc_name in all_location_names:
            if loc_name in narrative:
                locations.append(loc_name)

        return locations

    def extract_mentioned_items(self, narrative: str) -> List[str]:
        """
        從劇情中提取提到的物品

        簡化版本：提取常見物品關鍵詞
        """
        items = []

        # 常見物品模式
        item_patterns = [
            r'「(.+?)」',  # 引號中的內容
            r'『(.+?)』',  # 書名號中的內容
            r'獲得(.{1,10})',  # "獲得" 後的內容
            r'得到(.{1,10})',
            r'拾取(.{1,10})',
        ]

        for pattern in item_patterns:
            matches = re.findall(pattern, narrative)
            items.extend(matches)

        # 去重並清理
        items = [item.strip() for item in items if item.strip()]
        return list(set(items))

    def extract_damage_hints(self, narrative: str) -> Optional[int]:
        """
        從劇情中提取傷害提示

        例如：
        - "你失去了 20 點生命"
        - "扣除 15 HP"
        - "損失 10 點血量"

        Returns:
            傷害數值（正數），如果未找到則返回 None
        """
        damage_patterns = [
            r'失去(?:了)?(\d+)(?:點)?(?:生命|HP|血量)',
            r'損失(?:了)?(\d+)(?:點)?(?:生命|HP|血量)',
            r'扣除(?:了)?(\d+)(?:點)?(?:生命|HP|血量)',
            r'減少(?:了)?(\d+)(?:點)?(?:生命|HP|血量)',
            r'受到(?:了)?(\d+)(?:點)?(?:傷害|損傷)',
            r'造成(?:了)?(\d+)(?:點)?(?:傷害)',
        ]

        for pattern in damage_patterns:
            match = re.search(pattern, narrative)
            if match:
                return int(match.group(1))

        return None

    def extract_movement_destination(self, narrative: str) -> Optional[str]:
        """
        從劇情中提取移動目的地

        例如：
        - "你來到了青雲門·外門廣場"
        - "抵達靈草堂"
        """
        movement_patterns = [
            r'(?:來到|抵達|進入|走進|前往)(?:了)?(.{1,20})',
            r'(?:到達|踏入)(?:了)?(.{1,20})',
        ]

        for pattern in movement_patterns:
            match = re.search(pattern, narrative)
            if match:
                destination = match.group(1).strip()
                # 清理標點
                destination = destination.rstrip('。，、！？')
                return destination

        return None

    def suggest_hp_change(self, narrative: str) -> Optional[int]:
        """
        根據劇情建議 HP 變化數值

        返回負數表示扣血，正數表示加血
        """
        # 檢查是否提到受傷
        mentions_damage = any(kw in narrative for kw in self.DAMAGE_KEYWORDS)

        if mentions_damage and self._is_player_subject(narrative, self.DAMAGE_KEYWORDS):
            # 嘗試提取明確數值
            damage_hint = self.extract_damage_hints(narrative)
            if damage_hint:
                return -damage_hint

            # 根據嚴重程度估計
            severity_keywords = {
                '重創': -30,
                '重傷': -25,
                '吐血': -20,
                '受傷': -10,
                '疼痛': -5,
            }

            for keyword, damage in severity_keywords.items():
                if keyword in narrative:
                    return damage

        return None
