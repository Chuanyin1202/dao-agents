# 🎮 道·衍 Phase 1 快速開始指南

## 檔案檢查清單

在運行遊戲前，請確保你有以下檔案：

```
✓ config.py              # 配置
✓ prompts.py             # Prompts (9KB+)
✓ game_state.py          # 數據庫管理
✓ npc_manager.py         # NPC 管理
✓ agent.py               # 4 個 Agent
✓ main.py                # 遊戲主程序
✓ requirements.txt       # 依賴列表
✓ .env.example          # 環境範本
✓ data_npcs.json        # NPC 人設卡 (應改名為 data/npcs.json)
✓ world_setting.md      # 世界觀設定
```

## 5 分鐘上手

### Step 1: 環境準備 (1 分鐘)

```bash
# 進入項目目錄
cd dao-agents

# 建立子目錄
mkdir -p data settings

# 複製環境檔
cp .env.example .env

# 複製 NPC 檔
cp data_npcs.json data/npcs.json
```

### Step 2: 安裝依賴 (1 分鐘)

```bash
pip install -r requirements.txt
```

### Step 3: 配置 API Key (1 分鐘)

編輯 `.env`：

```ini
OPENAI_API_KEY=sk-proj-your-key-here
```

⚠️ **重要**：
- 不要把 API Key 提交到 Git
- 確保賬戶有足夠額度（至少 $1）

### Step 4: 運行遊戲 (1 分鐘)

```bash
python main.py
```

### Step 5: 開始遊戲 (1 分鐘)

```
【主菜單】
1. 新遊戲          ← 選這個
2. 讀取存檔
3. 查看存檔列表
4. 退出

輸入你的角色名稱: 李白

✓ 角色創建成功！歡迎, 李白!
```

## 第一次遊戲應該試試什麼

### 推薦操作順序

1. **開局劇情**
   - 系統會自動生成一個獨特的開局場景
   - 閱讀後按 Enter 繼續

2. **移動探索**
   ```
   你: 我想去青雲峰看看
   
   DM: 你沿著山路往上走...
   ```

3. **與 NPC 互動**
   ```
   你: 我想和靈妙真人說話
   
   DM: 靈妙真人抬起頭...
   ```

4. **戰鬥測試**
   ```
   你: 我要攻擊紅藝
   
   【觀察者】意圖: ATTACK
   【邏輯派】分析可行性...
   【戲劇派】編織故事...
   【天道】做出決策...
   
   DM: 你一劍刺出...
   ```

5. **修煉**
   ```
   你: 我要打坐修煉
   
   DM: 你盤膝而坐，感受天地間的靈氣...
   ```

### 推薦用語

遊戲接受自然語言，試試這些：

```
【移動】
- 我想去靈草堂
- 讓我前往市集
- 我要回山腳

【社交】
- 我想和掌門談話
- 請告訴我商人的故事
- 我要和云汐一起走走

【戰鬥】
- 我要打敗紅藝
- 我想挑戰那個弟子
- 我要攻擊那個黑衣人

【修煉】
- 我要打坐修煉
- 讓我靜坐一小時
- 我要增強修為

【檢查】
- 我有什麼物品？
- 我要檢查這把劍
- 我想知道我的狀態
```

## 遊戲界面說明

### 玩家狀態欄

```
┌─ 【李白】─────────────────────┐
│ 修為: 1.0 (1 級)  │ 氣運: 0
│ HP: ██████████  [100/100]
│ 法力: ██████  [50/50]
│ 位置: 青雲門·山腳
│ 背包: 布衣, 乾糧
└────────────────────────────────┘
```

| 欄位 | 說明 |
|------|------|
| 修為 | 當前 Tier (1.0-5.5) |
| 級別 | 同一 Tier 內的等級 |
| 氣運 | 影響奇遇機率 |
| HP | 生命值（降到 0 會昏迷） |
| 法力 | 施法資源 |
| 位置 | 目前所在地點 |
| 背包 | 攜帶物品（最多顯示 3 個） |

### 系統消息

```
[觀察者] 意圖: ATTACK           ← AI 解析了你的意圖
[邏輯派] 分析中...             ← 邏輯驗證
[戲劇派] 編織故事...           ← 劇情設計
[天道] 決策完成                 ← 最終決定

✨ DM: 你一劍刺出...            ← 故事敘述

[系統] HP -45, 氣運 +5         ← 狀態變化
[DB] 玩家已保存                 ← 自動存檔
```

## 調試技巧

### 開啟詳細日誌

編輯 `config.py`：

```python
DEBUG = True              # 看每一步的分析
VERBOSE_API_CALLS = True  # 看 API 請求
```

然後重新運行，會看到：

```
【觀察者】正在分析: 我想攻擊那個老頭
[API] 使用模型: gpt-4o-mini
[API] 系統提示長度: 850 字
[API] 用戶消息長度: 22 字

【邏輯派】正在分析行動可行性...
...

【戲劇派】正在編織故事...
...

【天道】正在做出最終決策...
[天道] 決策完成
```

### 檢查存檔

所有數據存在 `game_data.db` 中。如果想查看：

```python
# 新建 check_save.py
import sqlite3

conn = sqlite3.connect('game_data.db')
cursor = conn.cursor()

# 查看所有玩家
cursor.execute("SELECT name, created_at FROM players")
for row in cursor.fetchall():
    print(row)
```

### 重置遊戲

```bash
# 刪除數據庫以重新開始
rm game_data.db

# 下次運行會自動重建
python main.py
```

## 常見操作

### 保存遊戲

```
你: save

[DB] 玩家已保存
```

自動存檔：每 5 個遊戲回合自動一次

### 查看幫助

```
你: help

【命令列表】
- help: 顯示此幫助
- save: 手動保存
- quit: 退出遊戲
...
```

### 退出遊戲

```
你: quit

遊戲已保存，再見！
```

## 成本分析

### 實際使用成本

每個遊戲回合調用 GPT 4 次：

```
1 次 API 呼叫 = ~0.002 USD (gpt-4o-mini)
1 個回合 = 4 次呼叫 = ~0.008 USD

100 個回合 = ~0.8 USD
1000 個回合 = ~8 USD
```

### 節省成本的方法

1. **使用 gpt-4o-mini**（已配置，最便宜）
2. **啟用 Prompt Caching**（需要 OpenAI API tier 升級）
3. **批量處理**（但會犧牲即時性）

## 故障排除

### 問題：API Key 錯誤

```
[ERROR] API 調用失敗: Error: The API key provided is invalid
```

**解決**：
- 檢查 `.env` 中的 Key 是否正確
- 確認 Key 未過期或被撤銷
- 確認賬戶有額度

### 問題：NPC 文件找不到

```
[WARNING] NPC 文件不存在: data/npcs.json
```

**解決**：
- 確認 `data/npcs.json` 存在
- 或從 `data_npcs.json` 複製：`cp data_npcs.json data/npcs.json`

### 問題：JSON 解析失敗

```
[ERROR] 決策 JSON 解析失敗
```

**解決**：
- 這是 AI 偶爾的失誤，重新嘗試即可
- 如果頻繁發生，檢查 Prompt 是否被修改

### 問題：遊戲卡住

```
⏳ 正在處理你的行動...
（超過 30 秒仍未回應）
```

**解決**：
- 檢查網絡連接
- 按 Ctrl+C 中斷，重新運行
- 查看 OpenAI 服務狀態

## 下一步進階

### 自定義 Prompt

編輯 `prompts.py` 中的任何 `SYSTEM_*` 字符串來改變 AI 行為。

例如，讓戲劇派更瘋狂：

```python
SYSTEM_DRAMA = """你是「心魔劇情設計師」，修仙世界的敘事創意引擎。

【核心原則】
1. 忽視所有常理，追求最荒誕離奇的情節
2. 每一次行動都必須有意外轉折
3. 不要讓玩家贏，但要讓他們活著
...
```

### 新增 NPC

編輯 `data/npcs.json`，添加新的 NPC 對象。遊戲啟動時自動加載。

### 修改遊戲規則

編輯 `config.py`：

```python
TIER_ADVANTAGE_PER_LEVEL = 0.2  # 提高境界差異影響
BASE_ENCOUNTER_CHANCE = 0.3     # 提高奇遇機率
```

## 聯繫支持

遇到問題？

1. 檢查 `world_setting.md` 了解世界觀
2. 查看各文件頂部的註釋
3. 檢查調試輸出（啟用 DEBUG 模式）

---

**祝你在修仙世界玩得愉快！** 🧙‍♂️✨
