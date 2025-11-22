# validators.py
# 道·衍 - 數據一致性驗證系統

"""
三層驗證策略：
- Level 1 (警告): 數值微差，記錄但放行
- Level 2 (嚴重錯誤): items_gained 缺失等，重試一次
- Level 3 (兜底): 重試仍失敗，Regex 強制提取
"""

from typing import Dict, List, Any, Tuple
import re


class ConsistencyValidator:
    """
    驗證 Director Agent 生成的敘述 (Narrative) 與 狀態更新 (State Update) 是否一致。
    """

    def __init__(self):
        # 定義關鍵詞映射
        self.gain_keywords = ['獲得', '得到', '撿起', '拾取', '賜予', '授予', '領悟', '取得', '收穫']
        self.lose_keywords = ['失去', '消耗', '用掉', '損壞', '丟失', '失落']
        self.hp_loss_keywords = ['受傷', '疼痛', '吐血', '重創', '震飛', '損傷', '受損', '流血']
        self.move_keywords = ['來到', '抵達', '進入', '前往', '到達', '走進', '踏入']
        self.skill_keywords = ['學會', '領悟', '習得', '掌握', '悟出']

    def validate(self, narrative: str, state_update: Dict[str, Any], player_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        執行驗證

        Args:
            narrative: 劇情敘述
            state_update: 狀態更新字典
            player_state: 玩家當前狀態（用於數值範圍檢查）

        Returns:
            {
                "valid": bool,
                "errors": List[str],   # 需要重試的嚴重錯誤
                "warnings": List[str]  # 僅做記錄的警告
            }
        """
        errors = []
        warnings = []

        narrative_text = narrative if narrative else ""

        # 1. 檢查物品獲得
        gained_items = state_update.get('items_gained', [])
        for keyword in self.gain_keywords:
            if keyword in narrative_text:
                # 排除否定句
                if self._is_negative_context(narrative_text, keyword):
                    continue

                # 如果敘述提到獲得，但列表為空 -> 嚴重錯誤
                if not gained_items:
                    errors.append(f"❌ 嚴重: 敘述提到「{keyword}」但 items_gained 為空")
                    break

        # 反向檢查：狀態有更新，但敘述沒提 (警告即可)
        for item in gained_items:
            if item not in narrative_text:
                warnings.append(f"⚠️  狀態增加了物品「{item}」但敘述中未提及")

        # 2. 檢查物品失去
        lost_items = state_update.get('items_lost', [])
        for keyword in self.lose_keywords:
            if keyword in narrative_text:
                # 排除否定句
                if self._is_negative_context(narrative_text, keyword):
                    continue

                if not lost_items:
                    warnings.append(f"⚠️  敘述提到「{keyword}」但 items_lost 為空")
                    break

        # 3. 檢查 HP 變化 (受傷檢查) - 只檢查玩家受傷
        hp_change = state_update.get('hp_change', 0)
        for keyword in self.hp_loss_keywords:
            if keyword in narrative_text:
                # 排除否定句
                if self._is_negative_context(narrative_text, keyword):
                    continue

                # 檢查是否為玩家受傷（而非 NPC）
                if not self._is_player_subject(narrative_text, keyword):
                    continue

                if hp_change >= 0:
                    errors.append(f"❌ 嚴重: 敘述提到「{keyword}」但 HP 未扣減 (當前 hp_change: {hp_change})")
                    break

        # 4. 檢查移動（支援新架構：同時檢查 location_new 和 location_id）
        new_loc_name = state_update.get('location_new')
        new_loc_id = state_update.get('location_id')

        # 如果有 location_id，反查中文名稱用於驗證
        if new_loc_id and not new_loc_name:
            from world_data import get_location_name
            new_loc_name = get_location_name(new_loc_id)

        for keyword in self.move_keywords:
            if keyword in narrative_text:
                # 排除「想要」「打算」等意圖詞
                if self._is_intention_context(narrative_text, keyword):
                    continue

                # 檢查是否有位置更新（location_new 或 location_id 至少有一個）
                if not new_loc_name and not new_loc_id:
                    errors.append(f"❌ 嚴重: 敘述提到「{keyword}」但 location_new/location_id 都為空")
                    break

        # 5. 檢查技能學習
        skills_gained = state_update.get('skills_gained', [])
        for keyword in self.skill_keywords:
            if keyword in narrative_text:
                if self._is_negative_context(narrative_text, keyword):
                    continue

                if not skills_gained:
                    errors.append(f"❌ 嚴重: 敘述提到「{keyword}」技能但 skills_gained 為空")
                    break

        # 6. 數值合理性檢查 (Sanity Check) - Level 1 警告
        if hp_change < -200:
            warnings.append(f"⚠️  HP 單次扣減過大: {hp_change}")

        if hp_change > 100:
            warnings.append(f"⚠️  HP 單次恢復過大: {hp_change}")

        karma_change = state_update.get('karma_change', 0)
        if abs(karma_change) > 50:
            warnings.append(f"⚠️  Karma 單次變化過大: {karma_change}")

        mp_change = state_update.get('mp_change', 0)
        if mp_change < -100:
            warnings.append(f"⚠️  法力單次消耗過大: {mp_change}")

        experience_gained = state_update.get('experience_gained', 0)
        if experience_gained > 500:
            warnings.append(f"⚠️  單次經驗獲得過大: {experience_gained}")

        # 7. 檢查 location_id 是否存在於地圖上
        if 'location_id' in state_update and state_update['location_id']:
            from world_data import WORLD_MAP
            if state_update['location_id'] not in WORLD_MAP:
                errors.append(f"❌ 嚴重: location_id 不存在於地圖: {state_update['location_id']}")

        # 8. 檢查數值範圍（需要 player_state）
        if player_state:
            # 檢查 MP 是否會變負數
            if 'mp_change' in state_update:
                current_mp = player_state.get('mp', 0)
                new_mp = current_mp + state_update['mp_change']
                if new_mp < 0:
                    errors.append(f"❌ 嚴重: 法力扣減過多，會變為負數: {current_mp} + {state_update['mp_change']} = {new_mp}")

            # 檢查 HP 是否會變負數或超過上限
            if 'hp_change' in state_update:
                current_hp = player_state.get('hp', 0)
                max_hp = player_state.get('max_hp', 100)
                new_hp = current_hp + state_update['hp_change']

                if new_hp < 0:
                    errors.append(f"❌ 嚴重: 生命扣減過多，會變為負數: {current_hp} + {state_update['hp_change']} = {new_hp}")
                elif new_hp > max_hp:
                    warnings.append(f"⚠️  生命恢復超過上限: {new_hp} > {max_hp}（將被限制為 {max_hp}）")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _is_negative_context(self, text: str, keyword: str) -> bool:
        """
        檢查關鍵詞是否在否定句中

        例如：「沒有獲得」「無法獲得」「未能獲得」
        """
        negative_words = ['沒有', '無法', '未能', '不曾', '並未', '從未']

        # 查找關鍵詞位置
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return False

        # 檢查關鍵詞前 10 個字符內是否有否定詞
        context_start = max(0, keyword_pos - 10)
        context = text[context_start:keyword_pos + len(keyword)]

        for neg_word in negative_words:
            if neg_word in context:
                return True

        return False

    def _is_player_subject(self, text: str, keyword: str) -> bool:
        """
        檢查關鍵詞的主語是否為玩家（而非 NPC）

        例如：
        - "你受了重傷" → True (玩家)
        - "霜焰獅受了重傷" → False (NPC)
        - "牠身上佈滿傷痕" → False (NPC)
        """
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return False

        # 向前檢查 20 個字符
        context_start = max(0, keyword_pos - 20)
        context_before = text[context_start:keyword_pos]

        # NPC 指示詞（如果出現這些，說明不是玩家）
        npc_indicators = ['牠', '他', '她', '它', '靈獸', '敵人', '師兄', '師姐', '長老', '弟子',
                         '霜焰獅', '妖獸', '魔獸', '對手', '修士', '獸', '人', '獅']

        # 如果上下文中有 NPC 指示詞，判定為 NPC 受傷
        for indicator in npc_indicators:
            if indicator in context_before:
                return False

        # 玩家指示詞（如果出現這些，確認是玩家）
        player_indicators = ['你', '自己', '你的', '身體', '傷口']

        for indicator in player_indicators:
            if indicator in context_before:
                return True

        # 如果既沒有玩家指示詞也沒有 NPC 指示詞，保守起見判定為玩家
        # （這樣可以觸發驗證，但後續 Director 可以修正）
        return True

    def _is_intention_context(self, text: str, keyword: str) -> bool:
        """
        檢查是否是意圖而非實際行動

        例如：「想要來到」「打算進入」「準備前往」
        """
        intention_words = ['想', '想要', '打算', '準備', '計劃', '希望', '試圖']

        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return False

        # 檢查關鍵詞前 8 個字符內是否有意圖詞
        context_start = max(0, keyword_pos - 8)
        context = text[context_start:keyword_pos]

        for intent_word in intention_words:
            if intent_word in context:
                return True

        return False


def normalize_location_update(state_update: dict) -> dict:
    """
    翻譯層：強制將 AI 輸出的中文地名轉為 location_id
    如果轉換失敗，拋出 ValueError

    這是【ID 為王，名稱為皮】架構的核心翻譯層
    """
    from world_data import WORLD_MAP

    if 'location_new' in state_update and state_update['location_new']:
        location_input = state_update['location_new']

        # 檢查是否已經是 ID
        if location_input in WORLD_MAP:
            state_update['location_id'] = location_input
            # 移除 location_new，只保留 ID
            del state_update['location_new']
            return state_update

        # 嘗試中文 → ID 轉換
        for loc_id, loc_data in WORLD_MAP.items():
            if loc_data['name'] == location_input:
                state_update['location_id'] = loc_id
                # 移除 location_new（只保留 ID）
                del state_update['location_new']
                return state_update

        # 轉換失敗 → 報錯（讓遊戲重試）
        print(f"❌ AI 輸出了無效地點: '{location_input}'")
        print(f"   該地點不在地圖上。將移除此更新，讓 AI 重試。")
        # 移除無效的 location_new
        del state_update['location_new']

    return state_update


def auto_fix_state(narrative: str, state_update: dict) -> dict:
    """
    Level 3 兜底機制：使用 Regex 自動修復 state_update

    修改重點：使用翻譯層統一處理 location 格式

    Args:
        narrative: 劇情敘述
        state_update: 原始狀態更新

    Returns:
        修復後的狀態更新
    """
    fixed_update = state_update.copy()

    # 修復物品獲得
    if '獲得' in narrative or '得到' in narrative or '賜予' in narrative:
        # 匹配「獲得XXX」「得到XXX」「賜予你XXX」等模式
        # 中文物品名通常 2-6 個字
        pattern = r'(獲得|得到|撿起|拾取|賜予|授予|取得)(?:了)?(?:你)?(?:一[個件把枚塊顆粒張本份])?([^，。！？\s]{2,6})'
        matches = re.findall(pattern, narrative)

        if matches and not fixed_update.get('items_gained'):
            # 提取第二組（物品名）
            items = list(set([match[1] for match in matches]))  # 去重
            fixed_update['items_gained'] = items
            print(f"  🔧 自動修復: 添加物品 {items}")

    # 修復 HP 扣減（只在有明確數值時修復）
    if ('受傷' in narrative or '疼痛' in narrative or '吐血' in narrative or '重傷' in narrative or '失去' in narrative) and fixed_update.get('hp_change', 0) >= 0:
        # 嘗試從敘述中提取傷害數值
        # 支援多種表達方式：「失去了 20 點生命」「損失20點生命」「失去20生命」等
        damage_pattern = r'(?:損失|扣除|減少|失去|扣|減)(?:了)?\s*(\d+)\s*(?:點)?\s*(?:生命|HP|血量|點生命)'
        damage_match = re.search(damage_pattern, narrative)

        if damage_match:
            damage = int(damage_match.group(1))
            fixed_update['hp_change'] = -damage
            print(f"  🔧 自動修復: 設置 HP 扣減 -{damage}")
        else:
            # ❌ 禁用猜測行為 - 無法確定數值時不修復
            print(f"  ⚠️  無法自動修復 HP 扣減（敘述中未找到明確數值，且可能是 NPC 受傷）")

    # 修復移動（使用翻譯層）
    move_pattern = r'(來到|抵達|進入|走進|踏入)(?:了)?([^，。！？\s]{2,10})'
    move_match = re.search(move_pattern, narrative)

    if move_match and not fixed_update.get('location_new') and not fixed_update.get('location_id'):
        destination = move_match.group(2)
        # 提取到的是中文名稱，先暫存到 location_new
        fixed_update['location_new'] = destination
        print(f"  🔧 自動修復: 從敘述提取位置 '{destination}'")

    # ✅ 最後統一使用翻譯層處理
    fixed_update = normalize_location_update(fixed_update)

    return fixed_update


# 全局實例
validator = ConsistencyValidator()
