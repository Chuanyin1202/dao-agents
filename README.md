# 道·衍 (Dao Agents)

> AI 驅動的異步多人修仙 MUD - 基於多智能體辯論架構的文字遊戲

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 專案簡介

**道·衍** 是一個創新的文字冒險遊戲，使用多個 AI Agent 協作來創造動態、有深度的遊戲體驗。

### 核心特色

✨ **多 Agent 辯論系統**
- 4 個專業 AI Agent：觀察者、邏輯派、戲劇派、決策者
- 每個決策都經過「規則 vs 劇情」的辯論
- 既遵守數值平衡，又充滿戲劇張力

🎮 **原生 Python 架構**
- 零框架依賴（無 LangChain/AutoGPT）
- 完全可控的邏輯流程
- 易於調試和擴展

🌏 **完整的修仙世界**
- 10 個獨特 NPC，各有背景故事
- 9 個境界系統（練氣期 → 飛升期）
- 氣運機制、NPC 關係、事件日誌

💾 **持久化存檔**
- SQLite 數據庫
- 自動存檔（每 5 回合）
- 支援多角色存檔

---

## 🚀 快速開始

### 1. 環境需求

- Python 3.8+
- OpenAI API Key

### 2. 安裝步驟

```bash
# 克隆或下載專案
cd dao-agents

# 安裝依賴
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 編輯 .env，填入你的 OPENAI_API_KEY
```

### 3. 啟動遊戲

```bash
python run.py
```

### 4. 開始遊玩

```
╔═══════════════════════════════════════════════════╗
║           道·衍 - 修仙多智能體 MUD              ║
║     AI-Driven Async Multiplayer Cultivation      ║
║              v1.0.0 (Native Python)               ║
╚═══════════════════════════════════════════════════╝

【主菜單】
1. 新遊戲
2. 讀取存檔
3. 查看存檔列表
4. 退出

請選擇 (1-4):
```

---

## 📚 遊戲玩法

### 基本命令

遊戲使用**自然語言輸入**，AI 會理解你的意圖：

```
✅ 支援的命令類型：

移動：   "我要去靈草堂"
對話：   "我想和掌門談話"
攻擊：   "我要攻擊紅藝"
修煉：   "我要打坐修煉"
檢查：   "檢查背包"
使用：   "使用法力藥水"
```

### 系統命令

```
help  - 顯示幫助
save  - 手動保存
quit  - 退出遊戲
```

### 遊戲機制

#### 1. 境界系統
```
1.0 練氣期 → 2.0 築基期 → 3.0 金丹期 → 4.0 元嬰期
→ 5.0 化神期 → 6.0 度劫期 → ... → 9.0 飛升期
```

#### 2. 戰鬥系統
- 境界壓制：高境界對低境界有絕對優勢
- 同境界戰鬥：勝率 45-55%（引入隨機性）
- HP/MP 消耗：技能需要消耗法力值

#### 3. 氣運機制
- 氣運值影響奇遇觸發機率
- 好行為增加氣運，壞行為減少氣運
- 高氣運可能觸發「天降奇緣」

#### 4. NPC 關係
- 每個 NPC 都有好感度系統
- 互動會改變關係值
- 高好感度可能獲得秘傳或任務

---

## 🏗️ 專案架構

```
dao-agents/
├── src/                    # 核心代碼
│   ├── __init__.py        # 模組初始化
│   ├── main.py            # 遊戲主程序
│   ├── agent.py           # 4 個 AI Agent
│   ├── config.py          # 配置文件
│   ├── prompts.py         # AI Prompts
│   ├── game_state.py      # 狀態管理
│   └── npc_manager.py     # NPC 管理
├── data/                   # 遊戲數據
│   └── npcs.json          # NPC 定義
├── docs/                   # 文檔
│   ├── world_setting.md   # 世界觀設定
│   ├── QUICKSTART.md      # 快速上手
│   └── CHECKLIST.md       # 安裝檢查
├── tests/                  # 測試（待開發）
├── run.py                 # 入口檔案
├── requirements.txt       # 依賴列表
├── .env.example          # 環境變數範本
├── .gitignore            # Git 忽略清單
└── README.md             # 本文檔
```

### 技術架構

```
┌─────────────────────────────────────┐
│         使用者輸入 (自然語言)         │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   觀察者 Agent (Observer)           │
│   解析意圖 → JSON                   │
└─────────────┬───────────────────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
┌──────────┐  ┌──────────┐
│ 邏輯派   │  │ 戲劇派   │  (並行調用)
│ Logic    │  │ Drama    │
└────┬─────┘  └─────┬────┘
     │              │
     └──────┬───────┘
            ▼
┌─────────────────────────────────────┐
│   決策者 Agent (Director)           │
│   整合雙方意見 → 最終劇情 + 狀態更新  │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│   Python 執行層                      │
│   更新 HP/MP/物品/位置/關係          │
└─────────────┬───────────────────────┘
              │
              ▼
        顯示劇情給玩家
```

---

## 🎨 使用成本

### 預估費用（使用 gpt-4o-mini）

| 遊戲時長 | 回合數 | 預估成本 |
|---------|-------|---------|
| 1 小時  | ~12 回合 | $0.06-0.12 |
| 10 小時 | ~120 回合 | $0.6-1.2 |
| 100 小時 | ~1200 回合 | $6-12 |

**建議**：
- Phase 1 測試階段使用 `gpt-4o-mini`（已預設）
- 後續可在 `src/config.py` 中升級 `MODEL_DIRECTOR` 為 `gpt-4o`

---

## 🛠️ 開發指南

### 啟用調試模式

編輯 `.env` 文件：

```bash
DEBUG=true
VERBOSE_API_CALLS=true
```

### 自定義 NPC

編輯 `data/npcs.json`：

```json
{
  "id": "npc_011_custom",
  "name": "你的 NPC 名稱",
  "title": "NPC 頭銜",
  "tier": 2.5,
  "tier_name": "築基期",
  "location": "青雲門·某地",
  "personality": "性格描述",
  "lore": "背景故事",
  "combat_style": "戰鬥風格"
}
```

### 修改遊戲規則

編輯 `src/config.py`：

```python
# 戰鬥勝率計算
TIER_ADVANTAGE_PER_LEVEL = 0.15  # 每個小境界 15% 優勢

# 奇遇機率
BASE_ENCOUNTER_CHANCE = 0.1      # 基礎 10% 奇遇機率
KARMA_MULTIPLIER = 0.01          # 每點氣運 +1% 奇遇機率
```

### 修改 AI Prompt

編輯 `src/prompts.py` 中的各個 `SYSTEM_*` 常數

---

## 📖 延伸閱讀

- [世界觀設定](docs/world_setting.md) - 完整的修仙世界背景
- [快速上手指南](docs/QUICKSTART.md) - 5 分鐘入門教學
- [開發檢查清單](docs/CHECKLIST.md) - 安裝驗證步驟

---

## 🗺️ 開發路線圖

### ✅ Phase 1 - 單機閉環原型（已完成）
- [x] 4 個 AI Agent 協作系統
- [x] SQLite 持久化存檔
- [x] 10 個 NPC + 完整世界觀
- [x] 戰鬥/修煉/社交系統
- [x] 自然語言輸入解析
- [x] 強大的 JSON 解析機制

### 🔄 Phase 2 - 世界觀擴展（計劃中）
- [ ] 更多地點和 NPC
- [ ] 任務系統
- [ ] 技能樹
- [ ] 裝備系統
- [ ] 單元測試

### 🔮 Phase 3 - 異步多人（未來）
- [ ] 事件痕跡系統
- [ ] 玩家間接互動
- [ ] 世界事件
- [ ] FastAPI 後端

### 📱 Phase 4 - 客戶端（遠期）
- [ ] Flutter 移動端
- [ ] Web 版本
- [ ] 實時通知

---

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

### 貢獻方向

- 新增 NPC 和劇情
- 優化 AI Prompt
- 改進遊戲平衡性
- Bug 修復
- 文檔完善

---

## 📄 授權

MIT License

---

## 🙏 致謝

- OpenAI GPT-4o-mini API
- 所有測試玩家和貢獻者

---

**開始你的修仙之旅吧！** 🧙‍♂️✨
