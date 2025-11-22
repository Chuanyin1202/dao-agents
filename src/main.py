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
from world_map import (
    validate_movement, should_trigger_random_event,
    get_location_context, get_simple_movement_narrative,
    get_location_mp_cost, get_location_time_cost
)
from world_data import get_location_name, normalize_direction
from time_engine import advance_game_time, load_game_time

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

        # 獲取時間描述
        from time_engine import get_current_game_time
        time_info = get_current_game_time()

        print(f"""
┌─ 【{state.get('name', '未命名')}】─────────────────────┐
│ 修為: {state.get('tier')} ({state.get('level')} 級)  │ 氣運: {state.get('karma')}
│ HP: {hp_bar}  [{state.get('hp')}/{state.get('max_hp')}]
│ 法力: {mp_bar}  [{state.get('mp')}/{state.get('max_mp')}]
│ 位置: {state.get('location', get_location_name(state.get('location_id', 'qingyun_foot')))}
│ 時間: {time_info['description']}
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

        # 載入時間系統
        current_tick = self.player_state.get('current_tick', 0)
        load_game_time(current_tick)

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

            # 🎯 核心修復：檢查是否為方向輸入
            # 方向輸入直接處理，不需要經過 Observer（繞過 AI）
            if self.is_direction_input(processed_input):
                if self.handle_direction_movement(processed_input):
                    turn_count += 1
                    # 每 3 回合自動存檔
                    if turn_count % 3 == 0:
                        self.save_game()
                        print(f"[系統] 自動存檔完成（回合 {turn_count}）")
                continue  # 方向移動已處理完成，跳過 AI 流程

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

        # 【新增】移動意圖的特殊處理（地圖驗證）
        if intent_type == 'MOVE':
            direction = normalize_direction(intent.get('target', ''))
            current_location_id = self.player_state.get('location_id', 'qingyun_foot')

            # 驗證移動
            validation = validate_movement(
                current_location_id,
                direction if direction else intent.get('target', ''),
                self.player_state.get('tier', 1.0)
            )

            if not validation['valid']:
                # 非法移動，直接返回錯誤
                print(f"\n❌ {validation['reason']}")
                return

            # 合法移動，檢查是否觸發事件（新手降低機率）
            trigger_event = should_trigger_random_event(
                validation['destination_id'],
                self.player_state.get('karma', 0),
                self.player_state.get('tier', 1.0)
            )

            if not trigger_event:
                # 簡單移動，不調用 AI（極速響應）
                narrative = get_simple_movement_narrative(
                    current_location_id,
                    validation['destination_id'],
                    direction if direction else intent.get('target', '')
                )

                # 計算消耗
                mp_cost = get_location_mp_cost(current_location_id, validation['destination_id'])
                time_cost = get_location_time_cost(current_location_id, validation['destination_id'])

                state_update = {
                    'hp_change': 0,
                    'mp_change': -mp_cost,
                    'karma_change': 0,
                    'items_gained': [],
                    'location_new': validation['destination_name'],
                    'experience_gained': 0,
                }

                # 更新位置 ID
                self.player_state['location_id'] = validation['destination_id']
                self.player_state['location'] = validation['destination_name']

                # 推進時間
                time_result = advance_game_time('MOVE')
                self.player_state['current_tick'] = time_result['new_tick']

                self.apply_state_update(state_update)
                print(f"\n{narrative}")
                print(f"⏱️  {time_result['time_description']}")

                # 記錄事件
                game_db.log_event(
                    self.player_id,
                    validation['destination_name'],
                    'MOVE',
                    narrative[:150]
                )
                return

            # 有隨機事件，繼續正常流程（會調用 Drama）
            print(f"\n✨ 在前往 {validation['destination_name']} 的路上，發生了一些事...")

        # 查詢目標 NPC
        target_npc = None
        if intent.get('target'):
            target_npc = npc_manager.get_npc(intent['target']) or \
                        npc_manager.get_npc_by_name(intent['target'])

        # 構建地圖上下文（傳遞給 Logic Agent）
        current_location_id = self.player_state.get('location_id', 'qingyun_foot')
        world_map_context = get_location_context(current_location_id)

        # 第 2 步：邏輯 + 戲劇（平行調用，帶上下文 + 地圖約束）
        if config.DEBUG:
            print("\n⏳ 平行調用邏輯派和戲劇派...")

        logic_report, drama_proposal = call_logic_and_drama_parallel(
            self.player_state, intent, target_npc, recent_events, world_map_context  # ← 傳遞地圖約束
        )

        # 顯示 Agent 辯論過程（核心特色）
        self.display_agent_debate(logic_report, drama_proposal)

        # 第 3 步：決策（帶上下文）
        decision = agent_director(
            self.player_state, logic_report, drama_proposal,
            intent, target_npc, recent_events  # ← 傳遞上下文
        )

        # 第 3.5 步：數據一致性驗證（三層策略）
        narrative = decision.get('narrative', '發生了某件奇異的事情。')
        state_update = decision.get('state_update', {})

        from validators import validator, auto_fix_state

        validation = validator.validate(narrative, state_update)

        # 顯示警告（Level 1 - 不阻止）
        if validation['warnings']:
            for warning in validation['warnings']:
                if config.DEBUG:
                    print(f"  {warning}")

        # 處理嚴重錯誤（Level 2 & 3）
        if not validation['valid']:
            print("\n⚠️  檢測到數據不一致，正在修正...")
            for error in validation['errors']:
                print(f"  {error}")

            # Level 2: 重試一次
            if config.DEBUG:
                print("\n  🔄 Level 2: 重新調用 Director...")

            error_feedback = "\n".join(validation['errors'])

            # 重新調用 Director（帶錯誤信息）
            decision = agent_director(
                self.player_state, logic_report, drama_proposal,
                intent, target_npc, recent_events,
                error_feedback=error_feedback  # 傳遞錯誤反饋
            )

            narrative = decision.get('narrative', '發生了某件奇異的事情。')
            state_update = decision.get('state_update', {})

            # 重新驗證
            validation = validator.validate(narrative, state_update)

            if not validation['valid']:
                # Level 3: Regex 兜底
                if config.DEBUG:
                    print("\n  🔧 Level 3: 自動修復...")

                state_update = auto_fix_state(narrative, state_update)

                # 最後一次驗證（記錄結果）
                final_validation = validator.validate(narrative, state_update)
                if not final_validation['valid']:
                    print("  ⚠️  自動修復後仍有錯誤（已盡力）")
                else:
                    print("  ✅ 自動修復成功")

        # 第 4 步：應用狀態更新
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
        
        # 移動位置（只使用 location_id，自動同步 location 中文名）
        if 'location_id' in update and update['location_id']:
            self.player_state['location_id'] = update['location_id']
            # 同步更新中文名稱（用於顯示）
            from world_data import get_location_name
            self.player_state['location'] = get_location_name(update['location_id'])
        
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
            update.get('location_id'),  # 移動位置
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
        npcs_here = npc_manager.get_npcs_by_location(self.player_state.get('location_id', 'qingyun_foot'))

        print("\n【快捷命令】")
        print("  m=移動  a=攻擊  t=對話  c=修煉  i=背包  l=查看周圍")

        # 如果有 NPC，顯示可對話對象
        if npcs_here:
            print("\n【附近的 NPC】")
            for i, npc in enumerate(npcs_here[:3], 1):  # 最多顯示 3 個
                print(f"  t{i} - 與 {npc['name']} 對話")

        print("\n  💡 或輸入完整命令（如：\"我要去靈草堂\"）")

    def is_direction_input(self, user_input: str) -> bool:
        """
        判斷輸入是否為方向指令

        方向輸入包括：
        - 單字母：n, s, e, w
        - 英文：north, south, east, west
        - 中文：北, 南, 東, 西
        - 短語：往北, 往南, 向東, 向西

        Returns:
            True 如果是方向輸入
        """
        from world_map import normalize_direction

        # 嘗試標準化，如果能標準化就是方向輸入
        normalized = normalize_direction(user_input)
        return normalized is not None

    def handle_direction_movement(self, direction_input: str) -> bool:
        """
        直接處理方向移動（繞過 Observer）

        這是核心修復：單字母/簡短方向不需要 AI 解析

        Args:
            direction_input: 方向輸入（'n', '北', 'north' 等）

        Returns:
            True 如果成功處理
            False 如果失敗
        """
        from world_map import normalize_direction, validate_movement, get_simple_movement_narrative
        from world_map import get_location_mp_cost, get_location_time_cost

        # 標準化方向
        direction = normalize_direction(direction_input)

        if not direction:
            print(f"\n❌ 無法識別方向 '{direction_input}'")
            return False

        # 驗證移動
        current_location_id = self.player_state.get('location_id', 'qingyun_foot')
        player_tier = self.player_state.get('tier', 1.0)

        validation = validate_movement(current_location_id, direction, player_tier)

        if not validation['valid']:
            print(f"\n❌ {validation['reason']}")
            return False

        # 計算消耗
        mp_cost = get_location_mp_cost(current_location_id, validation['destination_id'])
        time_cost = get_location_time_cost(current_location_id, validation['destination_id'])

        # 檢查法力
        current_mp = self.player_state.get('mp', 0)
        if current_mp < mp_cost:
            print(f"\n❌ 法力不足。需要 {mp_cost} 點，當前 {current_mp} 點。")
            return False

        # 生成移動敘述
        narrative = get_simple_movement_narrative(
            current_location_id,
            validation['destination_id'],
            direction
        )

        # 應用狀態更新
        state_update = {
            'location_new': validation['destination_name'],
            'location_id': validation['destination_id'],
            'mp_change': -mp_cost,
            'tick_increase': time_cost
        }

        # 顯示敘述
        print(f"\n{narrative}")

        # 更新狀態
        self.apply_state_update(state_update)

        # 保存事件
        game_db.log_event(
            player_id=self.player_id,
            location=validation['destination_name'],
            event_type='MOVE',
            description=narrative
        )

        # 顯示新位置
        self.print_status()

        return True

    def handle_shortcut(self, user_input: str) -> Optional[str]:
        """
        處理快捷命令，轉換為完整指令

        Returns:
            str: 轉換後的完整指令
            None: 無效命令，跳過此回合
        """
        # 特殊處理：移動命令（顯示方向選單）
        if user_input == 'm':
            from world_data import get_location_data, get_location_name

            current_loc_id = self.player_state.get('location_id', 'qingyun_foot')
            loc_data = get_location_data(current_loc_id)

            if not loc_data:
                print("\n[錯誤] 無法識別當前位置。")
                return None

            exits = loc_data.get('exits', {})

            if not exits:
                print("\n[提示] 這裡似乎沒有出路...")
                return None

            print(f"\n【可用方向】")
            direction_map = {'north': '北', 'south': '南', 'east': '東', 'west': '西'}
            for direction, dest_id in exits.items():
                dest_name = get_location_name(dest_id)
                dir_chinese = direction_map.get(direction, direction)
                print(f"  {dir_chinese} ({direction[0]}) → {dest_name}")

            choice = input("\n請選擇方向 (或按 Enter 取消): ").strip()
            if not choice:
                return None

            return choice  # 返回用戶選擇的方向

        # 基礎快捷命令映射
        shortcuts = {
            'c': "我要打坐修煉",
            'i': "查看我的背包",
            'l': "我要查看周圍環境"
        }

        # 處理基礎快捷命令
        if user_input in shortcuts:
            return shortcuts[user_input]

        # 特殊處理：攻擊命令（需要驗證目標）
        if user_input == 'a':
            npcs_here = npc_manager.get_npcs_by_location(self.player_state.get('location_id', 'qingyun_foot'))
            if not npcs_here:
                print("\n[提示] 附近沒有可攻擊的目標。")
                return None  # 返回 None 表示跳過
            else:
                return f"我要攻擊 {npcs_here[0]['name']}"  # 攻擊第一個 NPC

        # 處理 NPC 對話快捷命令（t1, t2, t3）
        if user_input.startswith('t') and len(user_input) == 2 and user_input[1].isdigit():
            npc_index = int(user_input[1]) - 1
            npcs_here = npc_manager.get_npcs_by_location(self.player_state.get('location_id', 'qingyun_foot'))

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
