# action_cache.py
# 道·衍 - 智能快取系統

import time
import json
import hashlib
from typing import Dict, Any, Optional

# 只有這些「純查詢」行動可以快取
CACHEABLE_INTENTS = [
    'INSPECT',      # 查看物品/環境（不改變狀態）
]

# 這些行動「絕對不能」快取（會改變遊戲狀態）
NON_CACHEABLE_INTENTS = [
    'MOVE',         # 移動會改變位置
    'CULTIVATE',    # 修煉會改變經驗/法力
    'ATTACK',       # 戰鬥會改變狀態
    'USE_ITEM',     # 使用物品會改變背包
    'REST',         # 休息會恢復 HP/MP
    'SKILL_USE',    # 技能使用會消耗
    'TRADE',        # 交易會改變背包
    'TALK',         # 對話可能改變關係值
]


class ActionCache:
    """
    智能快取系統 - 只快取重複的簡單行動

    快取策略：
    1. 只快取「完全相同」的輸入和狀態
    2. 快取有效期 5 分鐘
    3. 狀態變化後自動失效
    """

    def __init__(self, ttl: int = 300):
        """
        Args:
            ttl: 快取有效期（秒），預設 5 分鐘
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        self.enabled = True  # 可透過 config 控制

    def generate_cache_key(self, user_input: str, player_state: Dict[str, Any]) -> str:
        """
        生成快取鍵（基於輸入和關鍵狀態）

        Args:
            user_input: 玩家輸入
            player_state: 玩家狀態

        Returns:
            快取鍵（SHA256 hash）
        """
        # 使用影響行動結果的所有關鍵狀態
        state_snapshot = {
            'hp': player_state.get('hp'),
            'mp': player_state.get('mp'),
            'location_id': player_state.get('location_id'),  # ✅ 改用 ID
            'tier': player_state.get('tier'),
            'karma': player_state.get('karma'),  # 影響奇遇機率
            'inventory': sorted(player_state.get('inventory', [])),  # ✅ 完整內容
            'skills': sorted(player_state.get('skills', []))  # ✅ 完整內容
        }

        # 組合輸入和狀態
        cache_data = f"{user_input}|{json.dumps(state_snapshot, sort_keys=True)}"

        # 生成 hash
        return hashlib.sha256(cache_data.encode('utf-8')).hexdigest()[:16]

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        獲取快取

        Args:
            key: 快取鍵

        Returns:
            快取的數據，如果不存在或已過期則返回 None
        """
        if not self.enabled:
            return None

        if key in self.cache:
            entry = self.cache[key]
            age = time.time() - entry['timestamp']

            if age < self.ttl:
                # 快取仍有效
                entry['hit_count'] = entry.get('hit_count', 0) + 1
                return entry['data']
            else:
                # 快取已過期，刪除
                del self.cache[key]

        return None

    def set(self, key: str, data: Dict[str, Any]):
        """
        設置快取

        Args:
            key: 快取鍵
            data: 要快取的數據
        """
        if not self.enabled:
            return

        self.cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'hit_count': 0
        }

    def clear(self):
        """清空所有快取"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        獲取快取統計

        Returns:
            快取統計信息
        """
        total_entries = len(self.cache)
        total_hits = sum(entry.get('hit_count', 0) for entry in self.cache.values())

        return {
            'total_entries': total_entries,
            'total_hits': total_hits,
            'enabled': self.enabled
        }

    def clean_expired(self):
        """清理過期的快取條目"""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry['timestamp'] >= self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)


# 全局實例
action_cache = ActionCache()
