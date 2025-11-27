# ✅ 道·衍 Phase 1 安裝校驗清單

## 文件完整性檢查

### 必須文件 (12 個)

在運行遊戲前，請確保你的項目目錄中有以下文件：

```
dao-agents/
├── main.py                    ✅ 遊戲主程序
├── config.py                  ✅ 配置文件
├── prompts.py                 ✅ AI Prompts (必須 > 200 行)
├── game_state.py              ✅ 數據庫管理
├── npc_manager.py             ✅ NPC 管理
├── agent.py                   ✅ 4 個 Agent 實現
├── requirements.txt           ✅ Python 依賴
├── .env.example              ✅ 環境範本
├── data/
│   └── npcs.json             ✅ 10 個 NPC (必須 > 400 行)
├── settings/
│   └── world_setting.md      ✅ 世界觀設定
├── README.md                 ✅ 完整說明
├── QUICKSTART.md             ✅ 快速開始
└── DELIVERY.md               ✅ 交付清單 (此文件)
```

**總計**：13 個文件

## 安裝步驟檢查

### ✓ Step 1: 環境準備

- [ ] 項目目錄結構完整（見上方）
- [ ] `mkdir -p data settings` 已執行
- [ ] `.env.example` 已複製為 `.env`
- [ ] `data_npcs.json` 已複製為 `data/npcs.json`

```bash
# 驗證命令
ls -la main.py config.py prompts.py
ls -la data/npcs.json settings/
```

### ✓ Step 2: Python 環境

- [ ] Python 版本 >= 3.8
  ```bash
  python --version  # 應顯示 3.8+
  ```

- [ ] pip 已安裝
  ```bash
  pip --version
  ```

- [ ] 虛擬環境（推薦）
  ```bash
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  # 或
  venv\Scripts\activate     # Windows
  ```

### ✓ Step 3: 依賴安裝

- [ ] requirements.txt 存在
  ```bash
  cat requirements.txt
  # 應包含:
  # openai>=1.3.0
  # python-dotenv>=1.0.0
  ```

- [ ] 依賴已安裝
  ```bash
  pip install -r requirements.txt
  ```

- [ ] 驗證安裝
  ```bash
  python -c "import openai; print(openai.__version__)"
  python -c "import dotenv; print('dotenv OK')"
  ```

### ✓ Step 4: API 配置

- [ ] `.env` 文件已創建
  ```bash
  cat .env
  ```

- [ ] `OPENAI_API_KEY` 已設置
  ```bash
  grep -i "OPENAI_API_KEY" .env
  # 應顯示: OPENAI_API_KEY=sk-...
  ```

- [ ] API Key 有效（可選測試）
  ```bash
  python -c "
  import os
  from dotenv import load_dotenv
  load_dotenv()
  key = os.getenv('OPENAI_API_KEY')
  print(f'API Key 已加載: {key[:20]}...')
  "
  ```

### ✓ Step 5: 數據文件驗證

- [ ] NPC 文件存在且有效
  ```bash
  python -c "
  import json
  with open('data/npcs.json', 'r', encoding='utf-8') as f:
    npcs = json.load(f)
    print(f'加載 {len(npcs[\"npcs\"])} 個 NPC')
    for npc in npcs['npcs'][:3]:
      print(f'  - {npc[\"name\"]} ({npc[\"tier\"]})')
  "
  ```

- [ ] 世界觀文件存在
  ```bash
  ls -l settings/world_setting.md  # 應 > 5KB
  ```

### ✓ Step 6: 代碼驗證

- [ ] 所有 Python 文件語法正確
  ```bash
  python -m py_compile config.py
  python -m py_compile prompts.py
  python -m py_compile game_state.py
  python -m py_compile npc_manager.py
  python -m py_compile agent.py
  python -m py_compile main.py
  ```

- [ ] 導入檢查
  ```bash
  python -c "import config; print('✓ config')"
  python -c "import prompts; print('✓ prompts')"
  python -c "import game_state; print('✓ game_state')"
  python -c "import npc_manager; print('✓ npc_manager')"
  python -c "import agent; print('✓ agent')"
  ```

## 首次運行檢查

### 運行遊戲

```bash
python main.py
```

### 期望看到的輸出

```
╔═══════════════════════════════════════════════════╗
║           道·衍 - 修仙多智能體 MUD              ║
║     AI-Driven Async Multiplayer Cultivation      ║
║              v2.0 (Native Python)                 ║
╚═══════════════════════════════════════════════════╝

[DB] 數據庫初始化完成
[NPC] 加載 10 個 NPC

【主菜單】
1. 新遊戲
2. 讀取存檔
3. 查看存檔列表
4. 退出

請選擇 (1-4): _
```

### 故障排除

| 錯誤訊息 | 原因 | 解決方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'openai'` | 依賴未安裝 | `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'dotenv'` | dotenv 未安裝 | `pip install python-dotenv` |
| `[WARNING] NPC 文件不存在` | `data/npcs.json` 不存在 | `cp data_npcs.json data/npcs.json` |
| `[ERROR] API 調用失敗: Invalid API key` | API Key 錯誤 | 檢查 `.env` 文件中的 Key |
| `FileNotFoundError: [Errno 2] No such file` | 目錄結構不完整 | `mkdir -p data settings` |

## 資源需求檢查

### 系統要求

- [ ] **CPU**: 1 核心+ (任何現代 CPU)
- [ ] **內存**: 512 MB+ (建議 2 GB+)
- [ ] **硬盤**: 100 MB+ (用於安裝 + 數據)
- [ ] **網絡**: 互聯網連接（OpenAI API 調用）

### Python 要求

- [ ] Python >= 3.8
- [ ] pip 或 conda

### 成本檢查

- [ ] OpenAI 賬戶已創建
- [ ] 成功添加支付方式
- [ ] 賬戶有正餘額（建議 $5+）

```bash
# 查詢使用情況（如果有 API 配置）
curl https://api.openai.com/dashboard/billing/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## 調試模式檢查

### 啟用調試模式

編輯 `config.py`：

```python
DEBUG = True              # 顯示每步分析
VERBOSE_API_CALLS = True  # 打印 API 調用
```

### 驗證調試輸出

運行遊戲並試著輸入一個命令：

```
你: 我想攻擊紅藝

【觀察者】正在分析: 我想攻擊紅藝
[API] 使用模型: gpt-4o-mini
[API] 系統提示長度: 850 字
[觀察者] 意圖: ATTACK

【邏輯派】正在分析行動可行性...
[邏輯派] 分析完成

... (更多輸出)
```

## 完整性簽核

### 代碼完整性

- [ ] 所有 6 個 Python 文件存在且 > 50 行
- [ ] 所有文件都有中文註釋
- [ ] 沒有阻塞性的 `TODO` 或 `FIXME` 標記（允許 Phase 2 預留功能）
- [ ] 所有 import 都能成功

### 數據完整性

- [ ] `npcs.json` 包含 10 個 NPC
- [ ] 每個 NPC 都有完整的字段
- [ ] JSON 格式有效（無語法錯誤）
- [ ] 所有中文字符編碼正確

### 文檔完整性

- [ ] README.md > 300 行
- [ ] QUICKSTART.md > 300 行
- [ ] world_setting.md > 400 行
- [ ] DELIVERY.md 完整

## 功能驗證

### 新遊戲流程

```bash
# 運行遊戲
python main.py

# 1. 選擇新遊戲
1

# 2. 輸入角色名
測試

# 3. 會顯示開局劇情
# 4. 可以輸入命令
幫我
save
quit
```

### 讀取存檔

```bash
# 運行遊戲
python main.py

# 1. 選擇讀取存檔
2

# 2. 輸入角色名
測試

# 3. 應該看到原來的狀態
```

### 保存驗證

```bash
# 檢查 SQLite 數據庫是否已創建
ls -la game_data.db

# 查詢玩家數據（如果有 sqlite3）
sqlite3 game_data.db "SELECT name, created_at FROM players"
```

## 性能基準

### 期望性能

| 指標 | 期望 | 實際 |
|------|------|------|
| 遊戲啟動時間 | < 2 秒 | ___ |
| 角色創建時間 | < 1 秒 | ___ |
| 開局劇情生成 | 3-5 秒 | ___ |
| 單個回合耗時 | 3-5 秒 | ___ |
| 自動保存時間 | < 100 ms | ___ |

## 最終檢查清單

- [ ] ✅ 所有 13 個文件已備齊
- [ ] ✅ Python 依賴已安裝
- [ ] ✅ API Key 已配置
- [ ] ✅ 代碼語法無誤
- [ ] ✅ 數據文件有效
- [ ] ✅ 遊戲能成功啟動
- [ ] ✅ 新遊戲流程完整
- [ ] ✅ 存檔讀取正常
- [ ] ✅ NPC 系統加載
- [ ] ✅ 所有文檔完整

## 🎉 認證完成

當所有檢查項都標記為 ✅ 時，你的 **道·衍 Phase 1** 已完全就緒！

現在可以：
1. 執行 `QUICKSTART.md` 中的 5 分鐘教程
2. 開始探索修仙世界
3. 根據 `README.md` 進行定制化開發

---

**祝你遊戲愉快！** 🧙‍♂️✨

檢查日期：________
檢查人：________
批准人：________
