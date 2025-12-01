# validators.py
# 道·衍 - 數據一致性驗證系統

"""
三層驗證策略：
- Level 1 (警告): 數值微差，記錄但放行
- Level 2 (嚴重錯誤): items_gained 缺失等，重試一次
- Level 3 (兜底): 重試仍失敗，Regex 強制提取
"""

from typing import Dict, List, Any, Tuple, Optional
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

    def validate(self, narrative: str, state_update: Dict[str, Any],
                 player_state: Optional[Dict[str, Any]] = None,
                 intent_type: Optional[str] = None) -> Dict[str, Any]:
        """
        執行驗證

        Args:
            narrative: 劇情敘述
            state_update: 狀態更新字典
            player_state: 玩家當前狀態（用於數值範圍檢查）
            intent_type: 玩家意圖類型（TALK, MOVE, ATTACK 等）

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

        # 1. 檢查物品獲得（TALK 和 INSPECT 意圖跳過此檢查）
        # 因為對話中的「獲得指導」「獲得啟發」不是實際物品
        skip_item_check = intent_type in ['TALK', 'INSPECT']

        gained_items = state_update.get('items_gained', [])
        if not skip_item_check:
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

        # 3. 檢查 HP 變化 (受傷檢查) - 雙向檢查
        hp_change = state_update.get('hp_change', 0)
        for keyword in self.hp_loss_keywords:
            if keyword in narrative_text:
                # 排除否定句
                if self._is_negative_context(narrative_text, keyword):
                    continue

                is_player_damaged = self._is_player_subject(narrative_text, keyword)

                # ✅ 玩家受傷但 HP 未扣減
                if is_player_damaged and hp_change >= 0:
                    errors.append(f"❌ 嚴重: 敘述提到玩家「{keyword}」但 HP 未扣減 (hp_change: {hp_change})")
                    break

                # ✅ NPC 受傷但誤扣玩家 HP
                elif not is_player_damaged and hp_change < 0:
                    errors.append(f"❌ 嚴重: NPC 受傷但誤扣玩家 HP (hp_change: {hp_change})")
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

        # 9. 檢測敘述中的疑似未註冊 NPC（警告層級）
        suspicious_npcs = detect_unregistered_npc_mentions(narrative_text)
        if suspicious_npcs:
            warnings.append(f"⚠️  敘述提到疑似未註冊 NPC: {suspicious_npcs}")
            # 注意：這裡只是警告，不算錯誤
            # 因為可能是合法的 NPC（如掌門、長老）
            # 但會提醒開發者檢查

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
        - "你一劍刺中霜焰獅，牠痛苦地吼叫" → False (NPC，以最近的主語為準)
        """
        from keyword_tables import NPC_INDICATORS, PLAYER_INDICATORS

        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return False

        # 向前檢查 30 個字符（擴大以涵蓋更多上下文）
        context_start = max(0, keyword_pos - 30)
        context_before = text[context_start:keyword_pos]

        # ✅ 檢查關鍵詞後文（用於「受傷的靈獸」這類形容詞修飾句式）
        context_after = text[keyword_pos:keyword_pos + 10]

        # ✅ 最優先：檢查是否有「XXX受傷」或「受傷的XXX」句式
        npc_indicator_words = ['靈獸', '妖獸', '魔獸', '野獸', '師兄', '師姐', '弟子', '對手', '敵人', '修士', '道人']

        # 情況1：檢查前文（如「靈獸受傷」）
        for npc_word in npc_indicator_words:
            if npc_word in context_before:
                npc_pos = context_before.rfind(npc_word)
                between = context_before[npc_pos + len(npc_word):]
                # 如果之間沒有明確的分隔符，判定為 NPC 受傷
                if not any(sep in between for sep in ['。', '，', '！', '？']):
                    return False  # NPC

        # 情況2：檢查後文（如「受傷的靈獸」）
        for npc_word in npc_indicator_words:
            if npc_word in context_after:
                # 檢查是否是「受傷的XXX」句式
                if '的' in context_after[:context_after.find(npc_word)]:
                    return False  # NPC

        # ✅ 次優先：檢查主語代詞
        primary_npc_pronouns = ['牠', '他', '她', '它']
        primary_player_pronouns = ['你', '您', '我']

        closest_pronoun = None
        closest_pos = -1

        for pronoun in primary_npc_pronouns + primary_player_pronouns:
            pos = context_before.rfind(pronoun)  # 從右往左找（最接近關鍵詞）
            if pos > closest_pos:
                closest_pos = pos
                closest_pronoun = pronoun

        # 根據最近的代詞判斷主語
        if closest_pronoun in primary_npc_pronouns:
            return False  # NPC
        elif closest_pronoun in primary_player_pronouns:
            return True  # 玩家

        # ✅ 次優先：使用統一的詞表檢查（移除了太寬泛的詞如「人」「獸」）
        # 如果上下文中有 NPC 指示詞，判定為 NPC 受傷
        for indicator in NPC_INDICATORS:
            if indicator in context_before:
                return False

        # 玩家指示詞（如果出現這些，確認是玩家）
        for indicator in PLAYER_INDICATORS:
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


def auto_fix_state(narrative: str, state_update: dict, intent_type: str = None) -> dict:
    """
    Level 3 兜底機制：使用 Regex 自動修復 state_update

    修改重點：
    - 使用翻譯層統一處理 location 格式
    - 過濾無效物品（抽象概念、被截斷的詞）
    - TALK/INSPECT 意圖跳過物品修復

    Args:
        narrative: 劇情敘述
        state_update: 原始狀態更新
        intent_type: 玩家意圖類型（用於跳過不適用的修復）

    Returns:
        修復後的狀態更新
    """
    from keyword_tables import (
        REGEX_ITEM_GAIN, REGEX_HP_DAMAGE, REGEX_MOVEMENT,
        INVALID_ITEM_WORDS, INVALID_ITEM_PATTERNS
    )

    fixed_update = state_update.copy()

    # TALK 和 INSPECT 意圖跳過物品修復
    # 因為「獲得指導」「獲得啟發」不是實際物品
    skip_item_fix = intent_type in ['TALK', 'INSPECT']

    # 修復物品獲得
    if not skip_item_fix and ('獲得' in narrative or '得到' in narrative or '賜予' in narrative):
        matches = re.findall(REGEX_ITEM_GAIN, narrative)

        if matches and not fixed_update.get('items_gained'):
            # 提取第二組（物品名）並過濾無效物品
            raw_items = list(set([match[1] for match in matches]))  # 去重

            # 過濾無效物品
            valid_items = []
            for item in raw_items:
                # 檢查是否在無效詞彙列表中
                if any(invalid_word in item for invalid_word in INVALID_ITEM_WORDS):
                    print(f"  ⚠️  過濾無效物品（抽象概念）: '{item}'")
                    continue

                # 檢查是否匹配無效模式
                is_invalid_pattern = False
                for pattern in INVALID_ITEM_PATTERNS:
                    if re.search(pattern, item):
                        print(f"  ⚠️  過濾無效物品（模式匹配）: '{item}'")
                        is_invalid_pattern = True
                        break

                if not is_invalid_pattern:
                    valid_items.append(item)

            if valid_items:
                fixed_update['items_gained'] = valid_items
                print(f"  🔧 自動修復: 添加物品 {valid_items}")

    # 修復 HP 扣減（只在有明確數值時修復）
    if ('受傷' in narrative or '疼痛' in narrative or '吐血' in narrative or '重傷' in narrative or '失去' in narrative) and fixed_update.get('hp_change', 0) >= 0:
        damage_match = re.search(REGEX_HP_DAMAGE, narrative)

        if damage_match:
            damage = int(damage_match.group(1))
            fixed_update['hp_change'] = -damage
            print(f"  🔧 自動修復: 設置 HP 扣減 -{damage}")
        else:
            # ❌ 禁用猜測行為 - 無法確定數值時不修復
            print(f"  ⚠️  無法自動修復 HP 扣減（敘述中未找到明確數值，且可能是 NPC 受傷）")

    # 修復移動（使用翻譯層）
    move_match = re.search(REGEX_MOVEMENT, narrative)

    if move_match and not fixed_update.get('location_new') and not fixed_update.get('location_id'):
        destination = move_match.group(2)
        # 提取到的是中文名稱，先暫存到 location_new
        fixed_update['location_new'] = destination
        print(f"  🔧 自動修復: 從敘述提取位置 '{destination}'")

    # ✅ 最後統一使用翻譯層處理
    fixed_update = normalize_location_update(fixed_update)

    return fixed_update


def detect_unregistered_npc_mentions(narrative: str) -> List[str]:
    """
    檢測敘述中是否提到未註冊的 NPC

    Args:
        narrative: 劇情敘述文本

    Returns:
        可疑的 NPC 提及列表
    """
    # 常見 NPC 關鍵詞（這些詞如果出現，需要檢查是否為已註冊 NPC）
    npc_patterns = [
        r'(師兄|師姐|師弟|師妹)',
        r'(修士|道人|道長|老者)',
        r'(弟子|門人|執事)',
        r'(白衣少女|侍從|隨從)',
        r'(掌門|長老)',  # 這些應該註冊
    ]

    suspicious_mentions = []
    for pattern in npc_patterns:
        matches = re.findall(pattern, narrative)
        suspicious_mentions.extend(matches)

    return list(set(suspicious_mentions))  # 去重


def validate_npc_existence(decision: Dict[str, Any],
                          recent_events: List[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    驗證 Decision 中的 NPC 是否都已註冊

    Args:
        decision: Director 輸出的決策 JSON
        recent_events: 最近的事件記錄（用於判斷合法 NPC）

    Returns:
        (is_valid, invalid_npcs)
            - is_valid: 是否所有 NPC 都合法
            - invalid_npcs: 不合法的 NPC 列表
    """
    from npc_manager import npc_manager

    invalid_npcs = []

    # 檢查 npc_relations_change 中的 NPC ID
    npc_relations = decision.get('state_update', {}).get('npc_relations_change', {})
    if isinstance(npc_relations, dict):
        for npc_id in npc_relations.keys():
            if not npc_manager.get_npc(npc_id):
                invalid_npcs.append(npc_id)
    else:
        # 不預期的格式，直接忽略並警告
        print("[validator] ⚠️  npc_relations_change 應為 dict，已忽略")

    # 檢查 narrative 中的 NPC 提及
    narrative = decision.get('narrative', '')
    detected_npcs = detect_unregistered_npc_mentions(narrative)

    # 建立最近事件中的合法 NPC 名稱集合
    recent_npc_names = set()
    if recent_events:
        for event in recent_events:
            npc_id = event.get('npc_involved')
            if npc_id:
                npc = npc_manager.get_npc(npc_id)
                if npc:
                    recent_npc_names.add(npc['name'])

    # 驗證每個檢測到的 NPC 提及
    for npc_mention in detected_npcs:
        # 檢查是否為已註冊 NPC（通過名稱查找）
        if not npc_manager.get_npc_id_by_name(npc_mention):
            # 檢查是否在最近事件中出現過
            if npc_mention not in recent_npc_names:
                invalid_npcs.append(npc_mention)

    return (len(invalid_npcs) == 0, invalid_npcs)


def validate_location_rules(intent_type: Optional[str],
                           state_update: Dict[str, Any],
                           location_id: str,
                           target_npc_id: Optional[str] = None) -> List[str]:
    """
    位置相關的合理性檢查（警告層級）：
    - 事件類型是否允許
    - 物品掉落是否在白名單內
    - NPC 是否允許出現在該地點

    目前僅產生警告，不阻擋流程。
    """
    from world_data import get_location_data

    warnings = []
    loc_data = get_location_data(location_id)

    if not loc_data:
        return warnings

    allowed_events = loc_data.get("allowed_events")
    if allowed_events and intent_type and intent_type not in allowed_events:
        warnings.append(f"事件類型 {intent_type} 在 {loc_data.get('name', location_id)} 不被允許")

    allowed_items = loc_data.get("allowed_item_drops") or []
    for item in state_update.get("items_gained", []) or []:
        if allowed_items and item not in allowed_items:
            warnings.append(f"物品『{item}』不應在 {loc_data.get('name', location_id)} 掉落")

    allowed_npcs = loc_data.get("allowed_npcs") or []
    if target_npc_id and allowed_npcs and target_npc_id not in allowed_npcs:
        warnings.append(f"NPC {target_npc_id} 不應出現在 {loc_data.get('name', location_id)}")

    return warnings


# 全局實例
validator = ConsistencyValidator()
