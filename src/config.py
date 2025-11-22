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

# 模型配置
MODEL_OBSERVER = "gpt-4o-mini"      # 快速意圖解析
MODEL_LOGIC = "gpt-4o-mini"         # 規則驗證
MODEL_DRAMA = "gpt-4o-mini"         # 劇情生成
MODEL_DIRECTOR = "gpt-4o-mini"      # 最終決策（Phase 1 使用 mini 降低成本）

# ============ 遊戲配置 ============
GAME_TITLE = "道·衍 - 修仙多智能體 MUD"

# ============ 玩家初始狀態 ============
INITIAL_PLAYER_STATE = {
    "name": None,                    # 由玩家設定
    "tier": 1.0,                     # 練氣期初級
    "hp": 100,
    "max_hp": 100,
    "mp": 50,                        # 法力值
    "max_mp": 50,
    "inventory": ["布衣", "乾糧"],   # 初始物品
    "location": "青雲門·山腳",
    "karma": 0,                      # 氣運值（影響奇遇）
    "relations": {},                 # {npc_id: affinity_score}
    "skills": ["基礎劍法"],           # 技能列表
    "cultivation_progress": 0.0,     # 當前境界進度 (0.0-100.0)
    "experience": 0,
    "level": 1,
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
API_TEMPERATURE = 0.8               # Drama 創意度

# ============ 調試模式 ============
# 從環境變數讀取，預設為 False
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
VERBOSE_API_CALLS = os.getenv("VERBOSE_API_CALLS", "false").lower() == "true"