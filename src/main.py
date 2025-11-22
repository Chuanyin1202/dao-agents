# main.py
# 道·衍 - 多智能體修仙 MUD 主程序

import sys
import json
from typing import Dict, Any, Optional
import config
from game_state import game_db
from npc_manager import npc_manager
from action_cache import action_cache, NON_CACHEABLE_INTENTS
from agent import (
    agent_observer, agent_logic, agent_drama,
    agent_director, generate_opening_scene,
    call_logic_and_drama_parallel
)

class DaoGame:
    def __init__(self):
        self.player_id: Optional[int] = None
        self.player_state: Optional[Dict[str, Any]] = None
        self.is_new_game = False
    
    def print_banner(self):
        """顯示標題"""
        banner = """
╔═══════════════════════════════════════════════════╗
║           道·衍 - 修仙多智能體 MUD              ║
║     AI-Driven Async Multiplayer Cultivation      ║
║              v2.0 (Native Python)                 ║
╚═══════════════════════════════════════════════════╝
"""
        print(banner)
    
    def print_status(self):
        """顯示玩家狀態"""
        if not self.player_state:
            return

        state = self.player_state
        hp_bar = "█" * (state['hp'] // 10) + "░" * ((state['max_hp'] - state['hp']) // 10)
        mp_bar = "█" * (state['mp'] // 5) + "░" * ((state['max_mp'] - state['mp']) // 5)

        print(f"""
┌─ 【{state.get('name', '未命名')}】─────────────────────┐
│ 修為: {state.get('tier')} ({state.get('level')} 級)  │ 氣運: {state.get('karma')}
│ HP: {hp_bar}  [{state.get('hp')}/{state.get('max_hp')}]
│ 法力: {mp_bar}  [{state.get('mp')}/{state.get('max_mp')}]
│ 位置: {state.get('location')}
│ 背包: {', '.join(state.get('inventory', [])[:3])}{'...' if len(state.get('inventory', [])) > 3 else ''}
└────────────────────────────────────────────┘
""")

    def handle_instant_action(self, user_input: str) -> bool:
        """
        處理即時響應的簡單行動（不調用 AI）

        這些行動不需要 AI 推理，可以直接顯示結果，大幅減少延遲。

        Args:
            user_input: 用戶輸入

        Returns:
            True: 已處理完成，跳過 AI 流程
            False: 需要 AI 處理
        """
        instant_actions = {
            'i': self._show_inventory_instant,
            's': self._show_status_instant,
        }

        if user_input in instant_actions:
            instant_actions[user_input]()
            return True
        return False

    def _show_inventory_instant(self):
        """即時顯示背包（0.1 秒響應）"""
        items = self.player_state.get('inventory', [])
        skills = self.player_state.get('skills', [])

        print("\n" + "═" * 50)
        print("【背包】")
        print("═" * 50)

        if items:
            print("\n📦 物品：")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")
        else:
            print("\n📦 物品：(空)")

        if skills:
            print("\n⚔️  技能：")
            for i, skill in enumerate(skills, 1):
                print(f"  {i}. {skill}")
        else:
            print("\n⚔️  技能：(尚未習得)")

        print("═" * 50)

    def _show_status_instant(self):
        """即時顯示狀態（復用現有方法）"""
        self.print_status()

    def get_tier_name(self, tier: float) -> str:
        """根據 tier 值獲取境界名稱"""
        tier_int = int(tier)
        tier_names = {
            1: "練氣期",
            2: "築基期",
            3: "金丹期",
            4: "元嬰期",
            5: "化神期",
            6: "煉虛期",
            7: "合體期",
            8: "大乘期",
            9: "渡劫期"
        }
        return tier_names.get(tier_int, "未知境界")

    def show_thinking_tip(self):
        """顯示隨機提示（在 AI 處理期間減少等待感）"""
        import random

        tier_name = self.get_tier_name(self.player_state.get('tier', 1.0))

        tips = [
            "「天道酬勤，地道酬善，人道酬誠」",
            "「道生一，一生二，二生三，三生萬物」",
            "「上善若水，水善利萬物而不爭」",
            "「知人者智，自知者明；勝人者有力，自勝者強」",
            "「大道至簡，衍化至繁」",
            f"💡 當前境界：{tier_name}",
            "💡 試試 'help' 查看更多命令",
            "💡 使用快捷命令（i/s/m/c）可節省時間"
        ]

        print(f"   {random.choice(tips)}")

    def main_menu(self):
        """主菜單"""
        print("\n【主菜單】")
        print("1. 新遊戲")
        print("2. 讀取存檔")
        print("3. 查看存檔列表")
        print("4. 退出")
        
        choice = input("請選擇 (1-4): ").strip()
        return choice
    
    def character_creation(self) -> bool:
        """角色創建"""
        print("\n╔═ 【角色創建】 ═╗")
        player_name = input("請輸入角色名稱 (2-8 字): ").strip()
        
        if len(player_name) < 2 or len(player_name) > 8:
            print("[ERROR] 角色名稱長度不符")
            return False
        
        result = game_db.create_new_player(player_name)
        if not result.get('success'):
            print(f"[ERROR] {result.get('error')}")
            return False
        
        self.player_id = result['player_id']
        self.player_state = result['state']
        self.is_new_game = True
        
        print(f"\n✓ 角色創建成功！歡迎, {player_name}!")
        return True
    
    def load_game(self) -> bool:
        """讀取存檔"""
        print("\n【讀取存檔】")
        player_name = input("輸入角色名稱: ").strip()
        
        result = game_db.load_player(player_name)
        if not result:
            print("[ERROR] 找不到該角色")
            return False
        
        self.player_id = result['player_id']
        self.player_state = result['state']
        self.is_new_game = False
        
        print(f"✓ 讀取成功！歡迎回來, {player_name}!")
        return True
    
    def list_saves(self):
        """列出所有存檔"""
        print("\n【存檔列表】")
        players = game_db.list_all_players()
        
        if not players:
            print("(沒有存檔)")
            return
        
        for i, p in enumerate(players, 1):
            print(f"{i}. {p['name']} - 創建於 {p['created_at']} | 最後保存 {p['last_save_at']}")
    
    def generate_opening(self):
        """開局劇情"""
        print("\n╔═ 【開局劇情】 ═╗\n")
        opening = generate_opening_scene(self.player_state['name'])
        print(opening)
        print("\n" + "─" * 50)
        input("\n按 Enter 繼續...")
    
    def game_loop(self):
        """主遊戲迴圈"""
        if self.is_new_game:
            self.generate_opening()
        
        print(f"\n歡迎來到 {config.GAME_TITLE}")
        print("輸入 'help' 查看命令，輸入 'quit' 退出遊戲\n")
        
        turn_count = 0
        
        while True:
            self.print_status()
            self.show_quick_commands()  # 顯示快捷命令

            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                self.save_game()
                print("\n遊戲已保存，再見！")
                break
            
            if user_input.lower() == "help":
                self.print_help()
                continue
            
            if user_input.lower() == "save":
                self.save_game()
                continue

            # 優先檢查即時行動（不需要 AI 處理）
            if self.handle_instant_action(user_input):
                continue  # 已處理完成，跳過 AI 流程

            # 處理快捷命令
            processed_input = self.handle_shortcut(user_input)

            # 如果返回 None，表示無效命令，跳過此回合
            if processed_input is None:
                continue

            # 遊戲主流程（需要 AI 推理）
            self.process_action(processed_input)
            
            turn_count += 1

            # 每 3 回合自動存檔（降低丟失進度的風險）
            if turn_count % 3 == 0:
                self.save_game()
                print(f"[系統] 自動存檔完成（回合 {turn_count}）")
    
    def process_action(self, user_input: str):
        """處理玩家行動（帶上下文記憶 + 智能快取）"""
        # 正常 AI 處理流程
        print("\n⏳ 正在處理你的行動...")
        self.show_thinking_tip()  # 顯示隨機提示，減少等待感

        # 第 0 步：查詢最近的事件（上下文記憶）
        recent_events = game_db.get_recent_events(self.player_id, limit=5)

        # 第 1 步：觀察（帶上下文）
        intent = agent_observer(user_input, recent_events)

        if intent.get('confidence', 0) < 0.3:
            print(f"DM: 我沒有理解你的意思。能再說一遍嗎？")
            return

        # 檢查快取（只在「意圖解析後」且「行動可快取」時）
        intent_type = intent.get('intent')
        cache_key = None

        if intent_type not in NON_CACHEABLE_INTENTS:
            cache_key = action_cache.generate_cache_key(user_input, self.player_state)
            cached_result = action_cache.get(cache_key)

            if cached_result:
                print("\n⚡ 使用快取結果（秒回）")
                self.apply_state_update(cached_result['state_update'])
                game_db.log_event(
                    self.player_id, self.player_state['location'],
                    cached_result.get('event_type', 'ACTION'),
                    cached_result['narrative'][:150]
                )
                print(f"\n{cached_result['narrative']}")
                return

        # 查詢目標 NPC
        target_npc = None
        if intent.get('target'):
            target_npc = npc_manager.get_npc(intent['target']) or \
                        npc_manager.get_npc_by_name(intent['target'])

        # 第 2 步：邏輯 + 戲劇（平行調用，帶上下文）
        if config.DEBUG:
            print("\n⏳ 平行調用邏輯派和戲劇派...")

        logic_report, drama_proposal = call_logic_and_drama_parallel(
            self.player_state, intent, target_npc, recent_events  # ← 傳遞上下文
        )

        # 顯示 Agent 辯論過程（核心特色）
        self.display_agent_debate(logic_report, drama_proposal)

        # 第 3 步：決策（帶上下文）
        decision = agent_director(
            self.player_state, logic_report, drama_proposal,
            intent, target_npc, recent_events  # ← 傳遞上下文
        )
        
        # 第 4 步：應用狀態更新
        narrative = decision.get('narrative', '發生了某件奇異的事情。')
        state_update = decision.get('state_update', {})
        
        self.apply_state_update(state_update)
        
        # 第 5 步：輸出
        print(f"\n✨ DM: {narrative}")

        # 記錄事件
        game_db.log_event(
            self.player_id,
            self.player_state['location'],
            intent.get('intent', 'UNKNOWN'),
            narrative,
            target_npc.get('id') if target_npc else None
        )

        # 快取結果（只快取「可快取行動」）
        if cache_key and intent_type not in NON_CACHEABLE_INTENTS:
            action_cache.set(cache_key, {
                'narrative': narrative,
                'state_update': state_update,
                'event_type': intent.get('intent', 'ACTION')
            })
    
    def apply_state_update(self, update: Dict[str, Any]):
        """應用狀態更新"""
        if not update:
            return
        
        # HP 變更（下限 0，上限 max_hp）
        if 'hp_change' in update:
            new_hp = self.player_state['hp'] + update['hp_change']
            self.player_state['hp'] = max(0, min(new_hp, self.player_state['max_hp']))

        # 法力變更（下限 0，上限 max_mp）
        if 'mp_change' in update:
            new_mp = self.player_state['mp'] + update['mp_change']
            self.player_state['mp'] = max(0, min(new_mp, self.player_state['max_mp']))
        
        # 氣運變更
        if 'karma_change' in update:
            self.player_state['karma'] += update['karma_change']
        
        # 獲得物品
        if 'items_gained' in update:
            for item in update['items_gained']:
                self.player_state['inventory'].append(item)
        
        # 失去物品
        if 'items_lost' in update:
            for item in update['items_lost']:
                if item in self.player_state['inventory']:
                    self.player_state['inventory'].remove(item)
        
        # 移動位置
        if 'location_new' in update and update['location_new']:
            self.player_state['location'] = update['location_new']
        
        # NPC 關係變更
        if 'npc_relations_change' in update:
            for npc_id, delta in update['npc_relations_change'].items():
                game_db.update_npc_relation(self.player_id, npc_id, delta)
        
        # 獲得技能
        if 'skills_gained' in update:
            for skill in update['skills_gained']:
                if skill not in self.player_state['skills']:
                    self.player_state['skills'].append(skill)
        
        # 經驗值
        if 'experience_gained' in update:
            self.player_state['experience'] += update['experience_gained']

        # 智能存檔：狀態重大變化時立即存檔
        should_save = any([
            update.get('hp_change', 0) < -20,  # 受到重傷
            update.get('items_gained'),  # 獲得物品
            update.get('location_new'),  # 移動位置
            update.get('skills_gained'),  # 獲得技能
            update.get('experience_gained', 0) >= 20  # 獲得大量經驗
        ])

        if should_save:
            self.save_game()
            if config.DEBUG:
                print("[系統] 狀態重大變化，自動存檔")

    def show_quick_commands(self):
        """顯示快捷命令"""
        # 獲取當前位置的 NPC
        npcs_here = npc_manager.get_npcs_by_location(self.player_state['location'])

        print("\n【快捷命令】")
        print("  m=移動  a=攻擊  t=對話  c=修煉  i=背包  l=查看周圍")

        # 如果有 NPC，顯示可對話對象
        if npcs_here:
            print("\n【附近的 NPC】")
            for i, npc in enumerate(npcs_here[:3], 1):  # 最多顯示 3 個
                print(f"  t{i} - 與 {npc['name']} 對話")

        print("\n  💡 或輸入完整命令（如：\"我要去靈草堂\"）")

    def handle_shortcut(self, user_input: str) -> Optional[str]:
        """
        處理快捷命令，轉換為完整指令

        Returns:
            str: 轉換後的完整指令
            None: 無效命令，跳過此回合
        """
        # 基礎快捷命令映射
        shortcuts = {
            'm': "我要移動到其他地方",
            'c': "我要打坐修煉",
            'i': "查看我的背包",
            'l': "我要查看周圍環境"
        }

        # 處理基礎快捷命令
        if user_input in shortcuts:
            return shortcuts[user_input]

        # 特殊處理：攻擊命令（需要驗證目標）
        if user_input == 'a':
            npcs_here = npc_manager.get_npcs_by_location(self.player_state['location'])
            if not npcs_here:
                print("\n[提示] 附近沒有可攻擊的目標。")
                return None  # 返回 None 表示跳過
            else:
                return f"我要攻擊 {npcs_here[0]['name']}"  # 攻擊第一個 NPC

        # 處理 NPC 對話快捷命令（t1, t2, t3）
        if user_input.startswith('t') and len(user_input) == 2 and user_input[1].isdigit():
            npc_index = int(user_input[1]) - 1
            npcs_here = npc_manager.get_npcs_by_location(self.player_state['location'])

            if 0 <= npc_index < len(npcs_here):
                npc = npcs_here[npc_index]
                return f"我要和{npc['name']}對話"
            else:
                print(f"\n[提示] 沒有第 {user_input[1]} 個 NPC。")
                return None  # 無效索引

        # 如果不是快捷命令，原樣返回
        return user_input

    def display_agent_debate(self, logic_report: str, drama_proposal: str):
        """顯示 Agent 辯論過程（核心特色）"""
        print("\n" + "═" * 70)
        print("【🤖 多 Agent 辯論】")
        print("═" * 70)

        # 邏輯派
        print("\n📐 邏輯派分析：")
        # 截取前 150 字，避免過長
        logic_preview = logic_report[:150] + "..." if len(logic_report) > 150 else logic_report
        print(f"   {logic_preview}")

        # 戲劇派
        print("\n🎭 戲劇派提案：")
        drama_preview = drama_proposal[:150] + "..." if len(drama_proposal) > 150 else drama_proposal
        print(f"   {drama_preview}")

        # 決策中
        print("\n⚖️  天道正在整合雙方意見，做出最終決策...")
        print("═" * 70)

    def save_game(self):
        """保存遊戲"""
        if self.player_id:
            game_db.save_player(self.player_id, self.player_state)
    
    def print_help(self):
        """顯示幫助"""
        print("""
╔════════════════════════════════════════════════════════════╗
║                      【遊戲指令說明】                        ║
╚════════════════════════════════════════════════════════════╝

【系統命令】
  help   - 顯示此幫助
  save   - 手動保存遊戲
  status - 查看角色狀態
  quit   - 退出遊戲（會自動存檔）

【快捷命令】（推薦使用，節省輸入時間）
  m - 移動到其他地方
  a - 攻擊
  t - 與 NPC 對話
  c - 打坐修煉
  i - 查看背包
  l - 查看周圍環境

【情境快捷】（當有 NPC 在附近時）
  t1 - 與第 1 個 NPC 對話
  t2 - 與第 2 個 NPC 對話
  t3 - 與第 3 個 NPC 對話

【自然語言命令】（完全自由輸入）
  "我要去靈草堂"
  "我要攻擊紅藝"
  "我想和掌門談談修煉的事"
  "我要使用背包裡的靈丹"

💡 提示：你可以混合使用快捷命令和自然語言！
""")
    
    def run(self):
        """主程序入口"""
        # 驗證 API Key（實際運行時檢查）
        try:
            config.validate_api_key()
        except ValueError as e:
            print(str(e))
            sys.exit(1)

        self.print_banner()

        while True:
            choice = self.main_menu()
            
            if choice == "1":
                if self.character_creation():
                    self.game_loop()
            
            elif choice == "2":
                if self.load_game():
                    self.game_loop()
            
            elif choice == "3":
                self.list_saves()
            
            elif choice == "4":
                print("感謝遊玩！")
                sys.exit(0)
            
            else:
                print("[ERROR] 無效選擇")


if __name__ == "__main__":
    game = DaoGame()
    game.run()
