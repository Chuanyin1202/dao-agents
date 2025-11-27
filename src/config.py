# config.py
# 道·衍 多智能體系統 - 配置文件

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# ============ 路徑配置 ============
# 專案根目錄（dao-agents/）
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data"
SETTINGS_PATH = PROJECT_ROOT / "settings"
DB_PATH = DATA_PATH / "game_data.db"

# ============ OpenAI 配置 ============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API Key 驗證函數（延遲檢查，允許測試環境導入）
def validate_api_key():
    """驗證 API Key 是否設定（在實際使用前調用）"""
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-api-key-here":
        raise ValueError(
            "\n" + "=" * 60 + "\n"
            "❌ 錯誤：未設定 OpenAI API Key\n"
            "=" * 60 + "\n"
            "請按照以下步驟設定：\n"
            "1. 複製 .env.example 為 .env\n"
            "2. 編輯 .env，填入你的 OpenAI API Key\n"
            "3. API Key 可從 https://platform.openai.com/api-keys 獲取\n"
            "=" * 60
        )

# 警告：API Key 未設定（但允許導入模組）
if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-api-key-here":
    import warnings
    warnings.warn(
        "OpenAI API Key 未設定。遊戲將無法運行，但可以導入模組進行測試。",
        RuntimeWarning
    )

# 模型配置（Phase 1 統一使用 mini 降低成本）
DEFAULT_MODEL = "gpt-4o-mini"
# 未來可按需調整各 Agent 的模型
MODEL_OBSERVER = DEFAULT_MODEL
MODEL_LOGIC = DEFAULT_MODEL
MODEL_DRAMA = DEFAULT_MODEL
MODEL_DIRECTOR = DEFAULT_MODEL

# ============ 遊戲配置 ============
GAME_TITLE = "道·衍 - 修仙多智能體 MUD"

# ============ 玩家初始狀態 ============
INITIAL_PLAYER_STATE = {
    "name": None,                    # 由玩家設定
    "tier": 1.0,                     # 練氣期初級（1.0-1.9 練氣，2.0-2.9 築基...）
    "hp": 100,
    "max_hp": 100,
    "mp": 50,                        # 法力值
    "max_mp": 50,
    "inventory": ["布衣", "乾糧"],   # 初始物品
    "location_id": "qingyun_foot",   # ✅ 使用英文 ID
    "location": "青雲門·山腳",        # ✅ 保留中文名（顯示用）
    "karma": 0,                      # 氣運值（影響突破成功率）
    "relations": {},                 # {npc_id: affinity_score}
    "skills": ["基礎劍法"],           # 技能列表
    "cultivation_progress": 0,       # 修煉進度（累積到所需值後可嘗試突破）
    "breakthrough_attempts": 0,      # 突破嘗試次數（用於劇情）
}

# ============ 遊戲規則 ============
# 戰鬥勝率計算
TIER_ADVANTAGE_PER_LEVEL = 0.15     # 每個小境界 15% 優勢
TIER_MAJOR_PENALTY = 0.85           # 跨大境界懲罰係數

# 奇遇機率
BASE_ENCOUNTER_CHANCE = 0.1         # 基礎 10% 奇遇機率
KARMA_MULTIPLIER = 0.01             # 每點氣運 +1% 奇遇機率

# ============ API 超參數 ============
API_TIMEOUT = 30
API_MAX_RETRIES = 3
API_RETRY_BASE_DELAY = 1.0          # 重試基礎延遲（秒），使用指數退避
API_TEMPERATURE = 0.8               # Drama 創意度

# ============ 遊戲機制參數 ============
REST_MP_RECOVERY = 20               # 休息恢復的法力值
AUTO_SAVE_INTERVAL = 3              # 自動存檔間隔（回合數）

# ============ 調試模式 ============
# 從環境變數讀取，預設為 False
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# 所有開發用日誌統一由 DEBUG 控制
VERBOSE_API_CALLS = DEBUG
