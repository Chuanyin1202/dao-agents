# npc_manager.py
# 道·衍 - NPC 管理系統

import json
import os
from typing import Dict, Any, Optional, List
import config

class NPCManager:
    def __init__(self):
        self.npcs: Dict[str, Dict[str, Any]] = {}
        self.load_npcs()
    
    def load_npcs(self):
        """從 JSON 文件加載 NPC 數據"""
        npc_file = config.DATA_PATH / "npcs.json"

        if not npc_file.exists():
            print(f"[WARNING] NPC 文件不存在: {npc_file}")
            print("[INFO] 請確保 data/npcs.json 檔案存在")
            return

        try:
            with open(npc_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.npcs = {npc['id']: npc for npc in data.get('npcs', [])}

            if config.DEBUG:
                print(f"[NPC] 成功加載 {len(self.npcs)} 個 NPC")
        except json.JSONDecodeError as e:
            print(f"[ERROR] NPC JSON 格式錯誤: {e}")
        except (IOError, OSError) as e:
            print(f"[ERROR] NPC 檔案讀取失敗: {type(e).__name__}: {e}")
    
    def get_npc(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """獲取單個 NPC"""
        return self.npcs.get(npc_id)
    
    def get_npc_by_name(self, npc_name: str) -> Optional[Dict[str, Any]]:
        """通過名稱查詢 NPC"""
        for npc in self.npcs.values():
            if npc_name in [npc.get('name'), npc.get('id')]:
                return npc
        return None
    
    def get_npcs_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """
        獲取某地點的所有 NPC（只使用 location_id）

        Args:
            location_id: 地點 ID（如 "qingyun_foot"）

        Returns:
            該地點的所有 NPC 列表
        """
        return [
            npc for npc in self.npcs.values()
            if npc.get('location_id') == location_id
        ]
    
    def get_all_npcs(self) -> List[Dict[str, Any]]:
        """獲取所有 NPC"""
        return list(self.npcs.values())

    def get_npc_id_by_name(self, name: str) -> Optional[str]:
        """
        根據 NPC 名稱查找 ID

        Args:
            name: NPC 名稱（如 "青雲門掌門"）

        Returns:
            NPC ID（如 "npc_001_master_qingyun"），如果沒找到則返回 None
        """
        for npc_id, npc_data in self.npcs.items():
            if npc_data.get('name') == name:
                return npc_id
        return None
    
    def format_npc_info(self, npc: Dict[str, Any]) -> str:
        """格式化 NPC 信息用於 AI 提示（顯示時轉換為中文）"""
        from world_data import get_location_name
        loc_name = get_location_name(npc.get('location_id', 'unknown'))

        return f"""
NPC: {npc.get('name')} ({npc.get('title', '無')})
ID: {npc.get('id')}
修為: {npc.get('tier')} ({npc.get('tier_name')})
位置: {loc_name}
性格: {npc.get('personality')}
背景: {npc.get('lore', '無')}
戰鬥風格: {npc.get('combat_style', '未知')}
"""


# 全局實例
npc_manager = NPCManager()
