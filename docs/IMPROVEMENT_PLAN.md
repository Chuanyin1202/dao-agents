# 道·衍 改善計劃

## 📋 當前問題總結

### 問題 1: 移動過度劇情化 ⚠️ 高優先級
**現象**：
- 玩家輸入簡單的移動指令（如 'm'），卻觸發大量劇情事件
- 出現「古樹」、「魔修」、「靈源玉」等不合理的隨機遭遇
- 移動應該是簡單的位置變化，而非劇情觸發器

**根本原因**：
1. **缺乏結構化地圖**：當前使用自由文字描述位置，AI 可以任意生成地點和事件
2. **Drama Agent 不理解移動語義**：心魔系統總是追求戲劇性，即使是普通移動
3. **Director 規則不夠強制**：雖然 prompt 有規則，但 AI 在複雜情況下會忽略

**影響**：
- 遊戲節奏被打亂
- 玩家失去對遊戲的掌控感
- 重複移動會產生大量無意義劇情

---

### 問題 2: 敘述與狀態不同步 🔴 嚴重
**現象**：
- narrative 說「獲得靈源玉」，但 `items_gained` 是空的
- 背包實際上沒有增加物品
- 玩家看到的故事和實際遊戲狀態不一致

**根本原因**：
1. **Director Agent 沒有嚴格遵守規則**：雖然 prompt 有檢查清單，AI 仍可能遺漏
2. **缺乏驗證層**：沒有代碼層面的檢查確保敘述和狀態一致
3. **Prompt 工程的侷限**：純靠文字指示，無法 100% 保證 AI 遵守

**影響**：
- 嚴重破壞遊戲邏輯
- 玩家困惑和不信任
- 潛在的存檔損壞風險

---

### 問題 3: Karma 異常增長
**現象**：
- 連續移動 4 次，karma 從 40 → 50 → 60 → 70 → 80
- 沒有實際的善行或惡行，只是移動

**根本原因**：
- Drama Agent 為了製造劇情，隨意增加 karma
- 缺乏 karma 變化的規則和限制

**影響**：
- 遊戲平衡被破壞
- karma 失去意義

---

## 🗺️ 核心解決方案：結構化世界地圖系統

### 設計理念
**從「自由生成」轉向「結構化探索」**：
- 預定義所有地點、連接關係、事件機率
- AI 負責敘事包裝，不負責世界結構
- 移動變成確定性操作 + 可選隨機事件

### 地圖數據結構

```python
# src/world_map.py

WORLD_MAP = {
    "青雲門·山腳": {
        "name": "青雲門·山腳",
        "description": "青雲門的入口，石階蜿蜒而上，霧氣繚繞。",
        "tier_requirement": 1.0,  # 最低境界要求
        "exits": {
            "north": "青雲門·外門廣場",
            "east": "青雲門·靈草堂",
        },
        "event_chance": 0.05,  # 5% 機率觸發隨機事件
        "available_npcs": ["npc_001_master_qingyun"],
        "features": ["靈氣充沛", "風景秀麗"],
    },

    "青雲門·外門廣場": {
        "name": "青雲門·外門廣場",
        "description": "寬闊的練武場，外門弟子們在此修煉。",
        "tier_requirement": 1.0,
        "exits": {
            "south": "青雲門·山腳",
            "north": "青雲門·內門",
            "west": "青雲門·藏經閣",
        },
        "event_chance": 0.10,  # 人多的地方事件機率高
        "available_npcs": ["npc_002_elder_wang", "npc_003_disciple_li"],
        "features": ["弟子眾多", "可以切磋"],
    },

    "青雲門·靈草堂": {
        "name": "青雲門·靈草堂",
        "description": "藥香四溢的藥堂，長老在此煉丹。",
        "tier_requirement": 1.0,
        "exits": {
            "west": "青雲門·山腳",
        },
        "event_chance": 0.02,
        "available_npcs": ["npc_004_herbalist_zhang"],
        "features": ["可以購買丹藥", "學習煉丹"],
    },

    "青雲門·藏經閣": {
        "name": "青雲門·藏經閣",
        "description": "古老的藏書樓，收藏著宗門秘籍。",
        "tier_requirement": 2.0,  # 需要築基期才能進入
        "exits": {
            "east": "青雲門·外門廣場",
        },
        "event_chance": 0.15,  # 秘籍之地，事件機率高
        "available_npcs": ["npc_005_librarian"],
        "features": ["可以學習技能", "需要貢獻點"],
    },

    "青雲門·內門": {
        "name": "青雲門·內門",
        "description": "內門弟子的修煉之地，靈氣濃郁。",
        "tier_requirement": 2.0,
        "exits": {
            "south": "青雲門·外門廣場",
            "north": "青雲門·掌門大殿",
        },
        "event_chance": 0.08,
        "available_npcs": [],
        "features": ["靈氣濃度 +50%", "修煉速度加成"],
    },
}

def validate_movement(current_location: str, direction: str, player_tier: float) -> dict:
    """
    驗證移動是否合法

    Returns:
        {
            "valid": bool,
            "reason": str,  # 如果 invalid
            "destination": str,  # 如果 valid
            "description": str,
        }
    """
    if current_location not in WORLD_MAP:
        return {"valid": False, "reason": f"未知地點: {current_location}"}

    location = WORLD_MAP[current_location]

    if direction not in location["exits"]:
        available = ", ".join(location["exits"].keys())
        return {"valid": False, "reason": f"此處無法往{direction}。可用方向: {available}"}

    destination_name = location["exits"][direction]
    destination = WORLD_MAP[destination_name]

    if player_tier < destination["tier_requirement"]:
        return {
            "valid": False,
            "reason": f"境界不足。需要 {destination['tier_requirement']}，當前 {player_tier}"
        }

    return {
        "valid": True,
        "destination": destination_name,
        "description": destination["description"],
    }

def should_trigger_random_event(location: str, player_karma: int) -> bool:
    """
    決定是否觸發隨機事件

    Args:
        location: 當前地點
        player_karma: 玩家 karma 值

    Returns:
        是否觸發事件
    """
    import random

    if location not in WORLD_MAP:
        return False

    base_chance = WORLD_MAP[location]["event_chance"]

    # karma 影響事件機率（最多 +10%）
    karma_bonus = min(player_karma / 1000, 0.10)

    final_chance = base_chance + karma_bonus

    return random.random() < final_chance
```

---

## 🔄 Multi-Agent 工作流程改進

### 當前流程（有問題）
```
玩家輸入 "往北走"
  ↓
Observer 解析 → intent: "MOVE", target: "north"
  ↓
Logic + Drama 並行處理
  ├─ Logic: "可行，移動會消耗體力"
  └─ Drama: "發現古樹！發現魔修！發現靈源玉！" ❌
  ↓
Director 合併 → 過度劇情化 ❌
```

### 新流程（結構化）
```
玩家輸入 "往北走"
  ↓
Observer 解析 → intent: "MOVE", target: "north"
  ↓
【新增】Map Validator 驗證
  - 檢查 current_location 的 exits 是否有 "north"
  - 檢查目的地的 tier_requirement
  - 決定是否觸發隨機事件
  ↓
如果 valid 且 no random event:
  → 直接返回簡單移動敘述（不調用 AI）✅

如果 valid 且 random event:
  ↓
  Logic: "移動可行，當前位置可能有事件"
  Drama: "設計簡短事件（不改變主線）" ✅
  ↓
  Director: "合併敘述 + 執行移動"

如果 invalid:
  → 直接返回錯誤訊息 ✅
```

---

## 📝 實施計劃

### Phase 1: 最小可行地圖 (2 小時)

**目標**：建立 10-15 個核心地點，實現基本移動系統

**任務清單**：
- [ ] 創建 `src/world_map.py`
  - [ ] 定義 WORLD_MAP 字典（10-15 個地點）
  - [ ] 實作 `validate_movement()` 函數
  - [ ] 實作 `should_trigger_random_event()` 函數
  - [ ] 實作 `get_location_info()` 函數

- [ ] 修改 `src/main.py`
  - [ ] 在 `process_action()` 中加入地圖驗證
  - [ ] MOVE 意圖優先調用 `validate_movement()`
  - [ ] 如果移動合法且無事件，直接返回簡單敘述
  - [ ] 只在隨機事件時調用 Drama Agent

- [ ] 修改 `src/prompts.py`
  - [ ] Logic Agent: 加入地圖驗證結果作為輸入
  - [ ] Drama Agent: 強調「只在隨機事件時生成劇情」
  - [ ] Director: 更新移動處理邏輯

- [ ] 測試
  - [ ] 測試合法移動（無事件）
  - [ ] 測試非法移動（方向錯誤）
  - [ ] 測試境界限制
  - [ ] 測試隨機事件觸發

**代碼示例（main.py 修改）**：
```python
from world_map import validate_movement, should_trigger_random_event

def process_action(self, user_input: str):
    # ... 現有代碼 ...

    intent = agent_observer(user_input, recent_events)
    intent_type = intent.get('intent')

    # 【新增】移動意圖的特殊處理
    if intent_type == 'MOVE':
        direction = intent.get('target')  # 'north', 'south', 'east', 'west'
        current_location = self.player_state['location']

        # 驗證移動
        validation = validate_movement(current_location, direction, self.player_state['tier'])

        if not validation['valid']:
            # 非法移動，直接返回錯誤
            print(f"\n❌ {validation['reason']}")
            return

        # 合法移動，檢查是否觸發事件
        trigger_event = should_trigger_random_event(
            validation['destination'],
            self.player_state['karma']
        )

        if not trigger_event:
            # 簡單移動，不調用 AI
            narrative = self._generate_simple_movement_narrative(
                current_location,
                validation['destination'],
                validation['description']
            )

            state_update = {
                'hp_change': 0,
                'mp_change': -5,  # 移動消耗少量法力
                'karma_change': 0,
                'items_gained': [],
                'location_new': validation['destination'],
                'cultivation_progress_change': 0,
            }

            self._apply_state_update(state_update)
            print(f"\n{narrative}")
            return

        # 有事件，繼續正常流程（調用 Drama）
        # ... 現有 Logic + Drama + Director 流程 ...

def _generate_simple_movement_narrative(self, from_loc: str, to_loc: str, description: str) -> str:
    """生成簡單移動敘述（不調用 AI）"""
    templates = [
        f"你沿著山路前行，{description}經過一段時間，你來到了{to_loc}。",
        f"你離開{from_loc}，向前走去。{description}不久，你抵達了{to_loc}。",
        f"你邁步前行，{description}片刻之後，你來到了{to_loc}。",
    ]
    import random
    return random.choice(templates)
```

---

### Phase 2: 隨機事件系統 (1 小時)

**目標**：為地圖添加豐富的隨機事件，但保持可控

**任務清單**：
- [ ] 創建 `src/world_events.py`
  - [ ] 定義每個地點的事件池
  - [ ] 事件分級（小事件、中事件、大事件）
  - [ ] 事件觸發條件（karma、tier、時間等）

- [ ] 修改 Drama Agent prompt
  - [ ] 輸入包含「事件類型」和「事件級別」
  - [ ] 強制遵守事件級別的影響範圍

**事件系統設計**：
```python
# src/world_events.py

LOCATION_EVENTS = {
    "青雲門·外門廣場": {
        "small": [  # 小事件：只有對話，無實質影響
            {
                "trigger": lambda state: state['tier'] >= 1.0,
                "description": "一位師兄正在指導新弟子劍法",
                "max_karma_change": 5,
                "max_items": 0,
            },
            {
                "trigger": lambda state: True,
                "description": "兩位弟子在切磋武藝",
                "max_karma_change": 3,
                "max_items": 0,
            },
        ],
        "medium": [  # 中事件：可能獲得物品或少量修煉進度
            {
                "trigger": lambda state: state['karma'] > 30,
                "description": "長老正在講解修煉心法",
                "max_karma_change": 10,
                "max_items": 1,
                "max_cultivation_progress": 20,
            },
        ],
        "major": [  # 大事件：顯著影響（極低機率）
            {
                "trigger": lambda state: state['karma'] > 60 and state['tier'] >= 2.0,
                "description": "宗門比武大會即將開始",
                "max_karma_change": 30,
                "max_items": 2,
                "max_cultivation_progress": 50,
            },
        ],
    },
}

def select_random_event(location: str, player_state: dict) -> dict:
    """
    隨機選擇一個適合的事件

    Returns:
        {
            "level": "small" | "medium" | "major",
            "description": str,
            "constraints": {
                "max_karma_change": int,
                "max_items": int,
                "max_cultivation_progress": int,
            }
        }
    """
    # 實作邏輯...
```

---

### Phase 3: 完整地圖擴展 (2-3 天)

**目標**：建立完整的修仙世界地圖

**任務清單**：
- [ ] 擴展到 30-50 個地點
  - [ ] 青雲門（10 個地點）
  - [ ] 附近城鎮（5 個地點）
  - [ ] 野外區域（10 個地點）
  - [ ] 秘境（5 個地點）
  - [ ] 其他宗門（10 個地點）

- [ ] 特殊機制
  - [ ] 傳送陣系統
  - [ ] 隱藏地點（需要特定物品或條件）
  - [ ] 危險區域（自動戰鬥觸發）
  - [ ] 安全區域（無法戰鬥）

- [ ] 地點效果
  - [ ] 靈氣濃度（影響修煉速度）
  - [ ] 環境加成/減益
  - [ ] 時間流速（某些秘境時間不同）

---

## 🔧 其他改進項目

### 改進 1: 敘述與狀態同步驗證層

**問題**：單靠 prompt 無法 100% 保證 AI 遵守規則

**解決方案**：在代碼層面驗證 Director 的輸出

```python
def validate_narrative_state_sync(narrative: str, state_update: dict) -> dict:
    """
    驗證敘述與狀態更新是否一致

    Returns:
        {
            "valid": bool,
            "warnings": List[str],  # 警告信息
            "errors": List[str],    # 錯誤信息
        }
    """
    warnings = []
    errors = []

    # 檢查 1: 敘述提到獲得物品，但 items_gained 是空的
    gain_keywords = ['獲得', '得到', '撿起', '拾取', '賜予']
    for keyword in gain_keywords:
        if keyword in narrative and not state_update.get('items_gained'):
            errors.append(f"敘述提到「{keyword}」但 items_gained 為空")

    # 檢查 2: items_gained 有物品，但敘述沒提到
    if state_update.get('items_gained'):
        for item in state_update['items_gained']:
            if item not in narrative:
                warnings.append(f"items_gained 包含「{item}」但敘述中未提及")

    # 檢查 3: 敘述提到移動，但 location_new 是 null
    move_keywords = ['來到', '抵達', '進入', '前往']
    for keyword in move_keywords:
        if keyword in narrative and not state_update.get('location_new'):
            errors.append(f"敘述提到「{keyword}」但 location_new 為空")

    # 檢查 4: 數值變化的合理性
    if state_update.get('hp_change', 0) < -100:
        warnings.append(f"HP 變化過大: {state_update['hp_change']}")

    if state_update.get('karma_change', 0) > 20:
        warnings.append(f"單次 karma 變化過大: {state_update['karma_change']}")

    return {
        'valid': len(errors) == 0,
        'warnings': warnings,
        'errors': errors,
    }
```

**整合到 main.py**：
```python
def process_action(self, user_input: str):
    # ... 獲得 Director 的結果 ...

    narrative = result.get('narrative')
    state_update = result.get('state_update')

    # 驗證一致性
    validation = validate_narrative_state_sync(narrative, state_update)

    if not validation['valid']:
        print("\n⚠️ AI 輸出驗證失敗，正在重試...")
        for error in validation['errors']:
            print(f"   ❌ {error}")

        # 重試一次（帶著錯誤信息）
        result = self._retry_director_with_feedback(validation['errors'])

    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"   ⚠️ {warning}")

    # 繼續正常流程...
```

---

### 改進 2: Karma 變化規則

**當前問題**：karma 隨意變化，失去意義

**解決方案**：在 Logic Agent 中強制 karma 規則

```python
# 在 prompts.py 的 SYSTEM_LOGIC 中加入

【Karma 變化規則】（必須遵守）
1. 普通移動：karma_change = 0（絕對不能變）
2. 普通對話：karma_change = ±5 以內
3. 善行（幫助他人、捐獻、救人）：+10 到 +20
4. 惡行（殺人、搶劫、破壞）：-20 到 -50
5. 重大善行（拯救村莊、擊敗大魔頭）：+50 到 +100
6. 修煉、休息、查看背包：karma_change = 0

**強制規則**：如果行動不符合以上類別，karma_change 必須為 0
```

---

### 改進 3: 經驗值系統標準化

**當前問題**：修煉獲得的經驗值不一致

**解決方案**：建立經驗值獲得標準

```python
# config.py

EXPERIENCE_REWARDS = {
    'CULTIVATE': {
        'base': 10,  # 基礎修煉
        'deep': 20,  # 深度修煉（靈氣充沛之地）
        'breakthrough': 50,  # 突破關鍵期
    },
    'COMBAT': {
        'win_equal': 30,  # 戰勝同階
        'win_higher': 100,  # 戰勝更高階
        'win_lower': 5,  # 戰勝低階（經驗很少）
    },
    'QUEST': {
        'minor': 20,  # 小任務
        'major': 100,  # 主要任務
        'epic': 500,  # 史詩任務
    },
}
```

---

## 🎯 優先級排序

### 🔴 高優先級（本週完成）
1. **結構化地圖系統 Phase 1**（解決移動問題）
2. **敘述與狀態同步驗證層**（解決物品不同步問題）
3. **Karma 變化規則強化**（解決 karma 異常問題）

### 🟡 中優先級（下週完成）
4. **隨機事件系統 Phase 2**
5. **經驗值系統標準化**
6. **Drama/Logic Agent prompt 優化**

### 🟢 低優先級（未來 2-3 週）
7. **完整地圖擴展 Phase 3**
8. **特殊機制（傳送陣、隱藏地點）**
9. **地點效果系統**

---

## 📊 預期效果

實施以上改進後，預期達成：

**移動系統**：
- ✅ 99% 的普通移動不會觸發劇情
- ✅ 移動延遲從 6-10 秒降低到 < 1 秒（直接返回）
- ✅ 隨機事件可控且有意義

**數據一致性**：
- ✅ 敘述提到的物品 100% 出現在背包
- ✅ 所有數值變化都有敘述支持
- ✅ 驗證層自動捕捉錯誤

**遊戲平衡**：
- ✅ Karma 變化有意義且可預測
- ✅ 經驗值獲得標準化
- ✅ 境界提升速度合理

**整體體驗**：
- ✅ 玩家有掌控感
- ✅ 世界感覺真實且一致
- ✅ AI 敘事保持高質量，但在結構化框架內

---

## 🔄 遷移策略

**現有存檔處理**：
- 由於是早期開發階段，不保留向後兼容
- 實施地圖系統後，現有存檔的 `location` 欄位需要對應到新地圖
- 如果 `location` 在新地圖中不存在，重置到 "青雲門·山腳"

**遷移腳本**（可選）：
```python
# scripts/migrate_saves.py

def migrate_location(old_location: str) -> str:
    """將舊地點名稱對應到新地圖"""
    mapping = {
        "青雲門": "青雲門·外門廣場",
        "靈草堂": "青雲門·靈草堂",
        # ... 更多對應
    }

    return mapping.get(old_location, "青雲門·山腳")
```

---

## 📝 後續文檔需求

- [ ] `docs/WORLD_MAP.md` - 完整地圖文檔
- [ ] `docs/EVENT_SYSTEM.md` - 事件系統設計文檔
- [ ] `docs/GAME_BALANCE.md` - 遊戲平衡數值表
- [ ] `docs/AI_AGENT_GUIDE.md` - 各 Agent 的詳細職責和規則

---

**最後更新**：2025-01-22
**狀態**：待實施
**預計完成**：Phase 1 (2 小時) | Phase 2 (1 小時) | Phase 3 (2-3 天)
