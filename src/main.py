# main.py
# 道·衍 - 多智能體修仙 MUD 主程序

import sys
import json
import time
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
        from cultivation import get_tier_display_name, get_cultivation_status
        time_info = get_current_game_time()

        # 獲取境界和修煉狀態
        tier_name = get_tier_display_name(state.get('tier', 1.0))
        cult_status = get_cultivation_status(state)
        progress_pct = cult_status['progress_percent']
        progress_bar = "█" * (progress_pct // 10) + "░" * (10 - progress_pct // 10)

        # 突破提示
        breakthrough_hint = " ✨可突破" if cult_status['can_breakthrough'] else ""

        print(f"""
┌─ 【{state.get('name', '未命名')}】─────────────────────┐
│ 境界: {tier_name} ({state.get('tier')})  │ 氣運: {state.get('karma')}
│ HP: {hp_bar}  [{state.get('hp')}/{state.get('max_hp')}]
│ 法力: {mp_bar}  [{state.get('mp')}/{state.get('max_mp')}]
│ 修煉: {progress_bar}  [{cult_status['progress']}/{cult_status['required']}]{breakthrough_hint}
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
            'rest': self._handle_rest,
            'r': self._handle_rest,
            '休息': self._handle_rest,
            'c': self._handle_cultivate,
            '修煉': self._handle_cultivate,
            'b': self._handle_breakthrough,
            '突破': self._handle_breakthrough,
        }

        if user_input.lower() in instant_actions:
            action_fn = instant_actions[user_input.lower()]

            # 檢查行為是否允許
            if action_fn == self._handle_rest and not self._is_action_allowed('REST'):
                print("\n[提示] 此地無法休息。")
                return True
            if action_fn == self._handle_cultivate and not self._is_action_allowed('CULTIVATE'):
                print("\n[提示] 此地無法修煉。")
                return True

            action_fn()
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

    def _handle_rest(self):
        """處理休息指令（恢復 MP）"""
        from world_data import get_location_data

        if not self._is_action_allowed('REST'):
            print("\n❌ 此地無法休息。")
            return

        # 檢查是否在安全區域
        current_loc_id = self.player_state.get('location_id', 'qingyun_foot')
        loc_data = get_location_data(current_loc_id)

        if not loc_data or not loc_data.get('safe', False):
            print("\n❌ 此地不安全，無法休息！")
            print("💡 提示：前往有【安全區域】標記的地點才能休息")
            return

        # 檢查 MP 是否已滿
        current_mp = self.player_state.get('mp', 0)
        max_mp = self.player_state.get('max_mp', 50)

        if current_mp >= max_mp:
            print("\n💤 你的法力已經充沛，不需要休息")
            return

        # 恢復 MP
        new_mp = min(current_mp + config.REST_MP_RECOVERY, max_mp)
        actual_recovery = new_mp - current_mp

        self.player_state['mp'] = new_mp

        # 推進時間
        time_result = advance_game_time('REST')
        self.player_state['current_tick'] = time_result['new_tick']

        # 輸出結果
        print(f"\n💤 你在{get_location_name(current_loc_id)}休息了片刻...")
        print(f"✨ 恢復了 {actual_recovery} 點法力 ({current_mp} → {new_mp})")
        print(f"⏱️  {time_result['time_description']}")

        # 記錄事件
        game_db.log_event(
            self.player_id,
            self.player_state.get('location', '未知'),
            'REST',
            f"在{get_location_name(current_loc_id)}休息，恢復了{actual_recovery}點法力"
        )

        # 存檔
        self.save_game()

    def _handle_cultivate(self):
        """處理修煉指令（累積修煉進度）"""
        from cultivation import cultivate, get_cultivation_status
        from time_engine import advance_game_time

        location_id = self.player_state.get('location_id', 'qingyun_foot')

        # 執行修煉
        result = cultivate(self.player_state, location_id)

        if not result['success']:
            print(f"\n❌ {result['message']}")
            return

        # 應用狀態變更
        state_changes = result['state_changes']
        if 'mp_change' in state_changes:
            self.player_state['mp'] = max(0, self.player_state['mp'] + state_changes['mp_change'])
        if 'cultivation_progress' in state_changes:
            self.player_state['cultivation_progress'] = state_changes['cultivation_progress']

        # 推進時間
        time_result = advance_game_time('CULTIVATE')
        self.player_state['current_tick'] = time_result['new_tick']

        # 輸出結果
        print(f"\n🧘 {result['message']}")
        print(f"⏱️  {time_result['time_description']}")

        # 檢查是否可以突破
        cult_status = get_cultivation_status(self.player_state)
        if cult_status['can_breakthrough']:
            print(f"\n✨ 修煉圓滿！輸入 'b' 嘗試突破（成功率 {cult_status['success_rate']:.1f}%）")

        # 記錄事件
        game_db.log_event(
            self.player_id,
            self.player_state.get('location', '未知'),
            'CULTIVATE',
            f"修煉獲得 {result['progress_gained']} 點進度"
        )

        # 存檔
        self.save_game()

    def _handle_breakthrough(self):
        """處理突破指令（嘗試境界突破）"""
        from cultivation import can_breakthrough, attempt_breakthrough, get_tier_display_name

        # 檢查是否可以突破
        can_break, reason = can_breakthrough(self.player_state)
        if not can_break:
            print(f"\n❌ 無法突破：{reason}")
            return

        # 確認突破
        from cultivation import calculate_breakthrough_rate
        tier = self.player_state.get('tier', 1.0)
        karma = self.player_state.get('karma', 0)
        success_rate = calculate_breakthrough_rate(tier, karma)

        print(f"\n⚡ 準備突破 {get_tier_display_name(tier)}")
        print(f"   當前成功率：{success_rate:.1f}%")
        confirm = input("   確定要嘗試突破嗎？(y/n): ").strip().lower()

        if confirm != 'y':
            print("   取消突破。")
            return

        # 執行突破
        result = attempt_breakthrough(self.player_state)

        # 應用狀態變更
        state_changes = result['state_changes']

        if result['success']:
            # 成功：更新所有屬性
            self.player_state['tier'] = state_changes['tier']
            self.player_state['cultivation_progress'] = state_changes['cultivation_progress']
            self.player_state['max_hp'] += state_changes.get('max_hp_change', 0)
            self.player_state['max_mp'] += state_changes.get('max_mp_change', 0)
            self.player_state['hp'] = state_changes.get('hp', self.player_state['hp'])
            self.player_state['mp'] = state_changes.get('mp', self.player_state['mp'])
            self.player_state['breakthrough_attempts'] = state_changes.get('breakthrough_attempts', 0)

            print(f"\n🎉 {result['message']}")
            print(f"   擲骰：{result['roll']:.1f} < {result['success_rate']:.1f} = 成功！")
        else:
            # 失敗：扣血和進度
            if 'hp_change' in state_changes:
                self.player_state['hp'] = max(1, self.player_state['hp'] + state_changes['hp_change'])
            self.player_state['cultivation_progress'] = state_changes.get('cultivation_progress', 0)
            self.player_state['breakthrough_attempts'] = state_changes.get('breakthrough_attempts', 0)

            print(f"\n💥 {result['message']}")
            print(f"   擲骰：{result['roll']:.1f} >= {result['success_rate']:.1f} = 失敗...")

        # 記錄事件
        event_type = 'BREAKTHROUGH_SUCCESS' if result['success'] else 'BREAKTHROUGH_FAIL'
        game_db.log_event(
            self.player_id,
            self.player_state.get('location', '未知'),
            event_type,
            result['narrative_hint']
        )

        # 存檔
        self.save_game()

    def show_thinking_tip(self):
        """顯示隨機提示（在 AI 處理期間減少等待感）"""
        import random
        from cultivation import get_tier_display_name

        tier_name = get_tier_display_name(self.player_state.get('tier', 1.0))

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

    def _is_action_allowed(self, intent: str) -> bool:
        """檢查當前地點是否允許指定意圖"""
        from world_data import get_location_data

        loc_data = get_location_data(self.player_state.get('location_id', 'qingyun_foot'))
        allowed = loc_data.get('allowed_events') if loc_data else None

        if not allowed:
            return True
        return intent in allowed

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
                    # 定期自動存檔
                    if turn_count % config.AUTO_SAVE_INTERVAL == 0:
                        self.save_game()
                        print(f"[系統] 自動存檔完成（回合 {turn_count}）")
                continue  # 方向移動已處理完成，跳過 AI 流程

            # 遊戲主流程（需要 AI 推理）
            self.process_action(processed_input)

            turn_count += 1

            # 定期自動存檔（降低丟失進度的風險）
            if turn_count % config.AUTO_SAVE_INTERVAL == 0:
                self.save_game()
                print(f"[系統] 自動存檔完成（回合 {turn_count}）")
    
    def process_action(self, user_input: str):
        """處理玩家行動（帶上下文記憶 + 智能快取）"""
        start_time = time.perf_counter()
        print("\n⏳ 正在處理你的行動...")
        self.show_thinking_tip()

        try:
            # 第 0 步：查詢最近的事件（上下文記憶）
            recent_events = game_db.get_recent_events(self.player_id, limit=5)

            # 第 1 步：觀察（帶上下文）
            intent = agent_observer(user_input, recent_events)

            if intent.get('confidence', 0) < 0.3:
                print("DM: 我沒有理解你的意思。能再說一遍嗎？")
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

                    time_result = advance_game_time(intent.get('intent', 'GENERAL'))
                    self.player_state['current_tick'] = time_result['new_tick']
                    print(f"⏱️  {time_result['time_description']}")
                    return

            # 移動意圖的特殊處理（地圖驗證）
            if intent_type == 'MOVE':
                direction = normalize_direction(intent.get('target', ''))
                current_location_id = self.player_state.get('location_id', 'qingyun_foot')

                validation = validate_movement(
                    current_location_id,
                    direction if direction else intent.get('target', ''),
                    self.player_state.get('tier', 1.0)
                )

                if not validation['valid']:
                    print(f"\n❌ {validation['reason']}")
                    return

                trigger_event = should_trigger_random_event(
                    validation['destination_id'],
                    self.player_state.get('karma', 0),
                    self.player_state.get('tier', 1.0)
                )

                if not trigger_event:
                    narrative = get_simple_movement_narrative(
                        current_location_id,
                        validation['destination_id'],
                        direction if direction else intent.get('target', '')
                    )

                    mp_cost = get_location_mp_cost(current_location_id, validation['destination_id'])

                    current_mp = self.player_state.get('mp', 0)
                    if current_mp < mp_cost:
                        print(f"\n❌ 法力不足。需要 {mp_cost} 點，當前 {current_mp} 點。")
                        return

                    state_update = {
                        'hp_change': 0,
                        'mp_change': -mp_cost,
                        'karma_change': 0,
                        'items_gained': [],
                        'location_new': validation['destination_name'],
                        'experience_gained': 0,
                    }

                    self.player_state['location_id'] = validation['destination_id']
                    self.player_state['location'] = validation['destination_name']

                    time_result = advance_game_time('MOVE')
                    self.player_state['current_tick'] = time_result['new_tick']

                    self.apply_state_update(state_update)
                    print(f"\n{narrative}")
                    print(f"⏱️  {time_result['time_description']}")

                    game_db.log_event(
                        self.player_id,
                        validation['destination_name'],
                        'MOVE',
                        narrative[:150]
                    )
                    return

                print(f"\n✨ 在前往 {validation['destination_name']} 的路上，發生了一些事...")

            # 查詢目標 NPC
            target_npc = None
            if intent.get('target'):
                target_npc = npc_manager.get_npc(intent['target']) or \
                            npc_manager.get_npc_by_name(intent['target'])

            # 構建地圖上下文
            current_location_id = self.player_state.get('location_id', 'qingyun_foot')
            world_map_context = get_location_context(current_location_id)

            # 第 2 步：邏輯 + 戲劇（平行調用）
            if config.DEBUG:
                print("\n⏳ 平行調用邏輯派和戲劇派...")

            logic_report, drama_proposal = call_logic_and_drama_parallel(
                self.player_state, intent, target_npc, recent_events, world_map_context
            )

            if config.DEBUG:
                self.display_agent_debate(logic_report, drama_proposal)

            # 第 3 步：決策（帶上下文）
            decision = agent_director(
                self.player_state, logic_report, drama_proposal,
                intent, target_npc, recent_events
            )

            # 第 3.5 步：數據一致性驗證（三層策略）
            narrative = decision.get('narrative', '發生了某件奇異的事情。')
            state_update = decision.get('state_update', {})

            from validators import (
                validator, auto_fix_state, validate_npc_existence,
                validate_location_rules
            )

            # NPC 白名單驗證
            is_npc_valid, invalid_npcs = validate_npc_existence(decision, recent_events)
            if not is_npc_valid:
                if config.DEBUG:
                    print(f"  ⚠️  檢測到未註冊 NPC: {invalid_npcs}")

                for npc_name in invalid_npcs:
                    narrative = narrative.replace(npc_name, "某人")

                if isinstance(state_update.get('npc_relations_change'), dict):
                    state_update['npc_relations_change'] = {
                        k: v for k, v in state_update['npc_relations_change'].items()
                        if k not in invalid_npcs
                    }
                else:
                    state_update['npc_relations_change'] = {}

                decision['narrative'] = narrative
                decision['state_update'] = state_update

            validation = validator.validate(narrative, state_update, self.player_state)

            # 顯示警告（Level 1 - 不阻止）
            if config.DEBUG and validation['warnings']:
                for warning in validation['warnings']:
                    print(f"  {warning}")

            # 地點規則警告
            if config.DEBUG:
                loc_warnings = validate_location_rules(
                    intent_type,
                    state_update,
                    self.player_state.get('location_id', 'qingyun_foot'),
                    target_npc.get('id') if target_npc else None
                )
                for warning in loc_warnings:
                    print(f"⚠️  {warning}")

            # 處理嚴重錯誤（Level 2 & 3）
            if not validation['valid']:
                if config.DEBUG:
                    print("\n⚠️  檢測到數據不一致，正在修正...")
                    for error in validation['errors']:
                        print(f"  {error}")
                    print("\n  🔄 Level 2: 重新調用 Director...")

                error_feedback = "\n".join(validation['errors'])

                decision = agent_director(
                    self.player_state, logic_report, drama_proposal,
                    intent, target_npc, recent_events,
                    error_feedback=error_feedback
                )

                narrative = decision.get('narrative', '發生了某件奇異的事情。')
                state_update = decision.get('state_update', {})

                validation = validator.validate(narrative, state_update, self.player_state)

                if not validation['valid']:
                    if config.DEBUG:
                        print("\n  🔧 Level 3: 自動修復...")

                    state_update = auto_fix_state(narrative, state_update)

                    final_validation = validator.validate(narrative, state_update, self.player_state)
                    if not final_validation['valid']:
                        print("  ⚠️  自動修復後仍有錯誤（已盡力）")
                    elif config.DEBUG:
                        print("  ✅ 自動修復成功")

            # 第 4 步：應用狀態更新
            self.apply_state_update(state_update)

            # 第 4.5 步：推進時間
            action_type = intent.get('intent', 'GENERAL')
            time_result = advance_game_time(action_type)
            self.player_state['current_tick'] = time_result['new_tick']

            # 第 5 步：輸出
            print(f"\n✨ DM: {narrative}")
            print(f"⏱️  {time_result['time_description']}")

            # 記錄事件
            game_db.log_event(
                self.player_id,
                self.player_state['location'],
                intent.get('intent', 'UNKNOWN'),
                narrative,
                target_npc.get('id') if target_npc else None
            )

            # 快取結果
            if cache_key and intent_type not in NON_CACHEABLE_INTENTS:
                from validators import normalize_location_update
                validated_update = normalize_location_update(state_update.copy())

                action_cache.set(cache_key, {
                    'narrative': narrative,
                    'state_update': validated_update,
                    'event_type': intent.get('intent', 'ACTION')
                })

        finally:
            duration = time.perf_counter() - start_time
            print(f"\n⌚ 指令處理耗時 {duration:.2f} 秒")
    
    def apply_state_update(self, update: Dict[str, Any]):
        """應用狀態更新"""
        # 第一步：翻譯層處理（統一入口，將 location_new 轉為 location_id）
        from validators import normalize_location_update
        update = normalize_location_update(update)

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
        if isinstance(update.get('npc_relations_change'), dict):
            for npc_id, delta in update['npc_relations_change'].items():
                game_db.update_npc_relation(self.player_id, npc_id, delta)
        
        # 獲得技能
        if 'skills_gained' in update:
            for skill in update['skills_gained']:
                if skill not in self.player_state['skills']:
                    self.player_state['skills'].append(skill)

        # 修煉進度（AI 決策可能會給予進度加成）
        if 'cultivation_progress_change' in update:
            current = self.player_state.get('cultivation_progress', 0)
            self.player_state['cultivation_progress'] = max(0, current + update['cultivation_progress_change'])

        # 境界變更（罕見情況，如奇遇）
        if 'tier_change' in update:
            new_tier = round(self.player_state.get('tier', 1.0) + update['tier_change'], 1)
            self.player_state['tier'] = max(1.0, new_tier)

        # max_hp/max_mp 變更
        if 'max_hp_change' in update:
            self.player_state['max_hp'] = max(10, self.player_state['max_hp'] + update['max_hp_change'])
        if 'max_mp_change' in update:
            self.player_state['max_mp'] = max(10, self.player_state['max_mp'] + update['max_mp_change'])

        # 智能存檔：狀態重大變化時立即存檔
        should_save = any([
            update.get('hp_change', 0) < -20,  # 受到重傷
            update.get('items_gained'),  # 獲得物品
            update.get('location_id'),  # 移動位置
            update.get('skills_gained'),  # 獲得技能
            update.get('tier_change'),  # 境界變化
            update.get('cultivation_progress_change', 0) >= 20  # 獲得大量修煉進度
        ])

        if should_save:
            self.save_game()
            if config.DEBUG:
                print("[系統] 狀態重大變化，自動存檔")

    def show_quick_commands(self):
        """顯示快捷命令"""
        from world_data import get_location_data

        loc_id = self.player_state.get('location_id', 'qingyun_foot')
        loc_data = get_location_data(loc_id) or {}
        allowed_events = set(loc_data.get('allowed_events', []))
        allow_all = not allowed_events  # 若未定義，視為全允許
        npcs_here = npc_manager.get_npcs_by_location(loc_id)
        can_rest = ('REST' in allowed_events or allow_all) and loc_data.get('safe', False) and self.player_state.get('mp', 0) < self.player_state.get('max_mp', 50)

        def allowed(intent: str) -> bool:
            return allow_all or intent in allowed_events

        cmds = []
        if allowed('MOVE'):
            cmds.append('m=移動')
        if allowed('ATTACK') and npcs_here:
            cmds.append('a=攻擊')
        if allowed('TALK') and npcs_here:
            cmds.append('t=對話')
        if allowed('CULTIVATE'):
            cmds.append('c=修煉')

        # 檢查是否可以突破
        from cultivation import can_breakthrough
        can_break, _ = can_breakthrough(self.player_state)
        if can_break:
            cmds.append('b=突破✨')

        if can_rest:
            cmds.append('r=休息(回復法力)')
        if allowed('INSPECT'):
            cmds.append('l=查看周圍')

        # 背包不受 allowed_events 限制
        cmds.append('i=背包')

        print("\n【快捷命令】")
        if cmds:
            print("  " + "  ".join(cmds))

        if npcs_here and allowed('TALK'):
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
            'location_id': validation['destination_id'],
            'mp_change': -mp_cost
        }

        # 顯示敘述
        print(f"\n{narrative}")

        # 更新狀態
        self.apply_state_update(state_update)

        # 推進時間（方向移動是即時行動，需要手動推進時間）
        time_result = advance_game_time('MOVE')
        self.player_state['current_tick'] = time_result['new_tick']
        print(f"⏱️  {time_result['time_description']}")

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

            if not self._is_action_allowed('MOVE'):
                print("\n[提示] 此地無法移動。")
                return None

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

        # 處理單獨的 t 命令（對話）
        if user_input == 't':
            if not self._is_action_allowed('TALK'):
                print("\n[提示] 此地無法對話。")
                return None
            npcs_here = npc_manager.get_npcs_by_location(self.player_state.get('location_id', 'qingyun_foot'))
            if not npcs_here:
                print("\n[提示] 這裡沒有人可以對話。")
                return None  # 跳過此回合
            else:
                # 如果有 NPC，默認與第一個對話
                return f"我要和{npcs_here[0]['name']}對話"

        # 處理基礎快捷命令
        if user_input in shortcuts:
            if user_input == 'c' and not self._is_action_allowed('CULTIVATE'):
                print("\n[提示] 此地無法修煉。")
                return None
            if user_input == 'l' and not self._is_action_allowed('INSPECT'):
                print("\n[提示] 此地無法查看周圍。")
                return None
            return shortcuts[user_input]

        # 特殊處理：攻擊命令（需要驗證目標）
        if user_input == 'a':
            if not self._is_action_allowed('ATTACK'):
                print("\n[提示] 此地無法攻擊。")
                return None
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
  r - 休息（安全區域且地點允許時可用）
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
