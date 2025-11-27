# game_state.py
# 道·衍 - 玩家狀態管理 & 存檔系統

import sqlite3
import json
import copy
import shutil
import os
from datetime import datetime
from typing import Dict, Any, Optional
import config

# 資料庫 schema 版本（每次修改表結構時遞增）
# v3: 新增 cultivation_progress, breakthrough_attempts 欄位
DB_SCHEMA_VERSION = 3


class GameStateManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        self.init_database()

    def _get_schema_version(self, cursor: sqlite3.Cursor) -> int:
        """獲取當前資料庫 schema 版本"""
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='schema_version'
        """)
        if cursor.fetchone() is None:
            return 0  # 無版本表，視為版本 0

        cursor.execute("SELECT version FROM schema_version LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else 0

    def _set_schema_version(self, cursor: sqlite3.Cursor, version: int):
        """設置資料庫 schema 版本"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("DELETE FROM schema_version")
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))

    def _backup_database(self) -> str:
        """備份資料庫，返回備份檔案路徑"""
        if not os.path.exists(self.db_path):
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"
        shutil.copy2(self.db_path, backup_path)

        if config.DEBUG:
            print(f"[DB] 資料庫已備份至: {backup_path}")

        return backup_path

    def init_database(self):
        """初始化 SQLite 數據庫（帶版本控制和備份）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_version = self._get_schema_version(cursor)

        if current_version < DB_SCHEMA_VERSION:
            if current_version > 0:
                # 有舊版本資料，先備份
                conn.close()
                backup_path = self._backup_database()
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                if config.DEBUG:
                    print(f"[DB] 從版本 {current_version} 升級到 {DB_SCHEMA_VERSION}")

            # 重建所有表（開發階段採用重建策略）
            cursor.execute("DROP TABLE IF EXISTS players")
            cursor.execute("DROP TABLE IF EXISTS event_logs")
            cursor.execute("DROP TABLE IF EXISTS npc_relations")

        # 玩家表（新版）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                location_id TEXT NOT NULL DEFAULT 'qingyun_foot',
                tier REAL NOT NULL DEFAULT 1.0,
                current_tick INTEGER NOT NULL DEFAULT 0,
                state_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_save_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                playtime_seconds INTEGER DEFAULT 0
            )
        """)
        
        # 遊戲事件日誌（用於後續的多人互動）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                location TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                npc_involved TEXT,
                FOREIGN KEY(player_id) REFERENCES players(id)
            )
        """)
        
        # NPC 關係記錄
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS npc_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                npc_id TEXT NOT NULL,
                affinity_score INTEGER DEFAULT 0,
                FOREIGN KEY(player_id) REFERENCES players(id),
                UNIQUE(player_id, npc_id)
            )
        """)

        # 更新 schema 版本
        self._set_schema_version(cursor, DB_SCHEMA_VERSION)

        conn.commit()
        conn.close()
        if config.DEBUG:
            print(f"[DB] 數據庫初始化完成 (schema v{DB_SCHEMA_VERSION})")
    
    def create_new_player(self, player_name: str) -> Dict[str, Any]:
        """創建新玩家"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 深拷貝初始狀態（確保 list/dict 獨立）
        player_state = copy.deepcopy(config.INITIAL_PLAYER_STATE)
        player_state["name"] = player_name

        # 確保初始位置使用 location_id
        from world_data import get_starting_location
        initial_location_id = get_starting_location()
        player_state["location_id"] = initial_location_id
        player_state["current_tick"] = 0

        try:
            cursor.execute("""
                INSERT INTO players (name, location_id, tier, current_tick, state_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                player_name,
                initial_location_id,
                player_state.get("tier", 1.0),
                0,
                json.dumps(player_state, ensure_ascii=False)
            ))
            conn.commit()
            player_id = cursor.lastrowid

            if config.DEBUG:
                print(f"[DB] 創建新玩家: {player_name} (ID: {player_id})")

            return {"success": True, "player_id": player_id, "state": player_state}
        except sqlite3.IntegrityError:
            return {"success": False, "error": f"玩家名稱 '{player_name}' 已存在"}
        finally:
            conn.close()
    
    def load_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """讀取現有玩家"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, state_json FROM players WHERE name = ?", (player_name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            player_state = json.loads(row["state_json"])
            return {"player_id": row["id"], "state": player_state}
        return None
    
    def save_player(self, player_id: int, state: Dict[str, Any]) -> bool:
        """保存玩家狀態（同步更新 location_id, tier, current_tick）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 同步獨立欄位
            location_id = state.get("location_id", "qingyun_foot")
            tier = state.get("tier", 1.0)
            current_tick = state.get("current_tick", 0)

            cursor.execute("""
                UPDATE players
                SET location_id = ?,
                    tier = ?,
                    current_tick = ?,
                    state_json = ?,
                    last_save_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                location_id,
                tier,
                current_tick,
                json.dumps(state, ensure_ascii=False),
                player_id
            ))
            conn.commit()
            if config.DEBUG:
                print(f"[DB] 玩家 ID {player_id} 已保存")
            return True
        except (sqlite3.Error, TypeError, ValueError) as e:
            print(f"[ERROR] 保存失敗: {type(e).__name__}: {e}")
            return False
        finally:
            conn.close()

    def log_event(self, player_id: int, location: str, event_type: str,
                  description: str, npc_involved: Optional[str] = None) -> bool:
        """記錄遊戲事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO event_logs (player_id, location, event_type, description, npc_involved)
                VALUES (?, ?, ?, ?, ?)
            """, (player_id, location, event_type, description, npc_involved))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERROR] 事件記錄失敗: {type(e).__name__}: {e}")
            return False
        finally:
            conn.close()
    
    def get_location_history(self, player_id: int, location: str, limit: int = 5) -> list:
        """獲取某個地點的事件歷史"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_type, description, npc_involved, timestamp
            FROM event_logs
            WHERE player_id = ? AND location = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (player_id, location, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_recent_events(self, player_id: int, limit: int = 5) -> list:
        """獲取玩家最近的事件（不限地點，用於上下文記憶）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT event_type, description, location, timestamp
            FROM event_logs
            WHERE player_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (player_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_npc_relation(self, player_id: int, npc_id: str) -> int:
        """獲取與 NPC 的親密度"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT affinity_score FROM npc_relations WHERE player_id = ? AND npc_id = ?",
            (player_id, npc_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else 0
    
    def update_npc_relation(self, player_id: int, npc_id: str, delta: int) -> bool:
        """更新與 NPC 的親密度"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 先嘗試插入，如果已存在則更新
            cursor.execute(
                "SELECT affinity_score FROM npc_relations WHERE player_id = ? AND npc_id = ?",
                (player_id, npc_id)
            )
            
            if cursor.fetchone():
                # 已存在，更新
                cursor.execute(
                    "UPDATE npc_relations SET affinity_score = affinity_score + ? WHERE player_id = ? AND npc_id = ?",
                    (delta, player_id, npc_id)
                )
            else:
                # 不存在，插入
                cursor.execute(
                    "INSERT INTO npc_relations (player_id, npc_id, affinity_score) VALUES (?, ?, ?)",
                    (player_id, npc_id, delta)
                )
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERROR] 親密度更新失敗: {type(e).__name__}: {e}")
            return False
        finally:
            conn.close()

    def list_all_players(self) -> list:
        """列出所有玩家"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, created_at, last_save_at FROM players")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


# 全局實例
game_db = GameStateManager()
