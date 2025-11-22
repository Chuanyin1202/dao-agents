# agent.py
# 道·衍 - 四個 Agent 的實現

import json
import re
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
import config
from prompts import (
    SYSTEM_OBSERVER, SYSTEM_LOGIC, SYSTEM_DRAMA, 
    SYSTEM_DIRECTOR, SYSTEM_OPENING_SCENE
)
from npc_manager import npc_manager

client = OpenAI(api_key=config.OPENAI_API_KEY)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    從文本中提取 JSON 對象（更強大的版本）
    嘗試多種策略提取 JSON
    """
    # 檢查 text 是否為 None 或空
    if not text:
        return None

    # 策略 1: 直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 策略 2: 查找 ```json 代碼塊
    json_code_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_code_match:
        try:
            return json.loads(json_code_match.group(1))
        except json.JSONDecodeError:
            pass

    # 策略 3: 查找第一個完整的 {} 對象
    brace_count = 0
    start_idx = -1

    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                try:
                    return json.loads(text[start_idx:i+1])
                except json.JSONDecodeError:
                    pass

    return None


def call_gpt(system_prompt: str, user_message: str, model: str = "gpt-4o-mini",
             temperature: float = 0.7) -> str:
    """通用 GPT 調用函數"""
    try:
        if config.VERBOSE_API_CALLS:
            print(f"\n[API] 使用模型: {model}")
            print(f"[API] 系統提示長度: {len(system_prompt)} 字")
            print(f"[API] 用戶消息長度: {len(user_message)} 字")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            timeout=config.API_TIMEOUT
        )
        
        result = response.choices[0].message.content

        # 檢查 API 返回的內容是否為 None
        if result is None:
            print(f"[WARNING] API 返回了 None，可能是內容過濾或其他問題")
            return ""

        if config.VERBOSE_API_CALLS:
            print(f"[API] 回應長度: {len(result)} 字")

        return result
    except Exception as e:
        print(f"[ERROR] API 調用失敗: {e}")
        return ""


def agent_observer(player_input: str, recent_events: list = None) -> Dict[str, Any]:
    """
    觀察者 Agent - 解析玩家意圖（帶上下文記憶）

    Args:
        player_input: 玩家輸入
        recent_events: 最近 3-5 回合的事件記錄

    輸出：JSON 格式的意圖指令
    """
    if config.DEBUG:
        print(f"\n【觀察者】正在分析: {player_input}")

    # 構建上下文
    context_text = ""
    if recent_events and len(recent_events) > 0:
        context_text = "\n【最近發生的事情】\n"
        for i, event in enumerate(reversed(recent_events), 1):
            context_text += f"{i}. {event['description'][:80]}...\n"
        context_text += "\n"

    # 使用分隔符防止 Prompt Injection
    user_message = f"""{context_text}【玩家輸入開始】
{player_input}
【玩家輸入結束】

請基於上下文理解玩家意圖。如果玩家的輸入指向「最近發生的事情」中的元素（如人物、物品、事件），請在 target 欄位中標註。"""

    response = call_gpt(
        system_prompt=SYSTEM_OBSERVER,
        user_message=user_message,
        model=config.MODEL_OBSERVER,
        temperature=0.5
    )
    
    # 提取 JSON
    intent_dict = extract_json_from_text(response)

    if intent_dict:
        if config.DEBUG:
            print(f"[觀察者] 意圖: {intent_dict.get('intent')}")
        return intent_dict
    else:
        if config.DEBUG:
            print(f"[觀察者] JSON 解析失敗，返回默認值")
            print(f"[觀察者] 原始回應: {response[:200]}")
        return {"intent": "UNKNOWN", "target": None, "confidence": 0.0}


def agent_logic(player_state: Dict[str, Any], intent: Dict[str, Any],
                npc: Optional[Dict[str, Any]] = None,
                recent_events: list = None,
                world_map_context: str = None) -> str:
    """
    邏輯分析者 Agent - 規則驗證（帶上下文記憶 + 地圖約束）

    Args:
        player_state: 玩家狀態
        intent: 意圖字典
        npc: 目標 NPC
        recent_events: 最近事件記錄
        world_map_context: 地圖約束信息（可行方向、境界要求等）

    輸出：分析報告（文本）
    """
    if config.DEBUG:
        print(f"\n【邏輯派】正在分析行動可行性...")

    context = f"""
玩家狀態：
- 名稱: {player_state.get('name')}
- 修為: {player_state.get('tier')} ({player_state.get('level')} 級)
- HP: {player_state.get('hp')}/{player_state.get('max_hp')}
- 法力: {player_state.get('mp')}/{player_state.get('max_mp')}
- 位置: {player_state.get('location')}

意圖分析：
- 類型: {intent.get('intent')}
- 目標: {intent.get('target')}
- 詳情: {intent.get('details')}
"""

    if npc:
        context += f"""
目標 NPC：
- 名稱: {npc.get('name')} ({npc.get('title')})
- 修為: {npc.get('tier')} ({npc.get('tier_name')})
- 戰鬥風格: {npc.get('combat_style')}
"""

    # 添加上下文
    if recent_events and len(recent_events) > 0:
        context += "\n【最近發生的事情】\n"
        for event in reversed(recent_events):
            context += f"- {event['description'][:100]}...\n"

    # 添加地圖約束（如果提供）
    if world_map_context:
        context += f"\n【地圖資訊】\n{world_map_context}\n"

    response = call_gpt(
        system_prompt=SYSTEM_LOGIC,
        user_message=context,
        model=config.MODEL_LOGIC,
        temperature=0.5
    )
    
    if config.DEBUG:
        print(f"[邏輯派] 分析完成")
    
    return response


def agent_drama(player_state: Dict[str, Any], intent: Dict[str, Any],
                npc: Optional[Dict[str, Any]] = None,
                recent_events: list = None) -> str:
    """
    戲劇設計者 Agent - 創意劇情（帶上下文記憶）

    Args:
        player_state: 玩家狀態
        intent: 意圖字典
        npc: 目標 NPC
        recent_events: 最近事件記錄

    輸出：劇情提案（文本）
    """
    if config.DEBUG:
        print(f"\n【戲劇派】正在編織故事...")

    context = f"""
場景背景：
- 玩家: {player_state.get('name')} (修為 {player_state.get('tier')})
- 位置: {player_state.get('location')}
- 目標行動: {intent.get('intent')}

玩家背景：
- 氣運值: {player_state.get('karma')}
- 當前心境: 新手充滿好奇心
"""

    if npc:
        context += f"""
遭遇 NPC: {npc.get('name')} ({npc.get('title')})
性格特徵: {npc.get('personality')}
背景故事: {npc.get('lore')}
"""

    # 添加劇情連貫性提示（最重要！）
    if recent_events and len(recent_events) > 0:
        context += "\n【劇情連貫性】最近發生的事件：\n"
        for event in reversed(recent_events):
            context += f"- {event['description']}\n"
        context += "\n⚠️ 重要：請確保新劇情與以上事件連貫！如果玩家的行動明確指向某個已出現的元素（如人物、物品、事件），必須延續該劇情線，不要憑空生成無關的新劇情。\n"
    
    response = call_gpt(
        system_prompt=SYSTEM_DRAMA,
        user_message=context,
        model=config.MODEL_DRAMA,
        temperature=config.API_TEMPERATURE
    )
    
    if config.DEBUG:
        print(f"[戲劇派] 劇情提案完成")
    
    return response


def agent_director(player_state: Dict[str, Any], logic_report: str,
                  drama_proposal: str, intent: Dict[str, Any],
                  npc: Optional[Dict[str, Any]] = None,
                  recent_events: list = None,
                  error_feedback: str = None) -> Dict[str, Any]:
    """
    決策者 Agent - 最終決策（帶上下文記憶 + 錯誤修正）

    Args:
        player_state: 玩家狀態
        logic_report: 邏輯派分析報告
        drama_proposal: 戲劇派劇情提案
        intent: 意圖字典
        npc: 目標 NPC
        recent_events: 最近事件記錄
        error_feedback: 上一次輸出的錯誤反饋（用於重試）

    輸出：JSON 格式的故事 + 狀態更新
    """
    if config.DEBUG:
        if error_feedback:
            print(f"\n【天道】正在修正錯誤並重新決策...")
        else:
            print(f"\n【天道】正在做出最終決策...")

    context = f"""
【邏輯分析】
{logic_report}

【戲劇提案】
{drama_proposal}

【玩家當前狀態】
- 名稱: {player_state.get('name')}
- 修為: {player_state.get('tier')}
- HP: {player_state.get('hp')}/{player_state.get('max_hp')}
- 位置: {player_state.get('location')}
- 氣運: {player_state.get('karma')}
- 當前意圖: {intent.get('intent')}
"""

    # 添加上下文摘要（用於保持劇情連貫）
    if recent_events and len(recent_events) > 0:
        context += "\n【最近的劇情】\n"
        for event in reversed(recent_events):
            context += f"- {event['description'][:150]}...\n"

    # 添加錯誤反饋（如果是重試）
    if error_feedback:
        context += f"\n⚠️ 【上一次輸出的錯誤】\n{error_feedback}\n"
        context += "請修正以上錯誤，確保敘述與狀態更新完全一致。\n"

    context += "\n請綜合上述信息，輸出最終決策 JSON。"
    
    response = call_gpt(
        system_prompt=SYSTEM_DIRECTOR,
        user_message=context,
        model=config.MODEL_DIRECTOR,
        temperature=0.7
    )
    
    # 提取 JSON
    decision = extract_json_from_text(response)

    if decision:
        if config.DEBUG:
            print(f"[天道] 決策完成")
        return decision
    else:
        print(f"[ERROR] 決策 JSON 解析失敗")
        if config.DEBUG:
            print(f"[天道] 原始回應: {response[:300]}")
        return {
            "narrative": "某種不可名狀的力量阻止了你的行動。天機不可洩露。",
            "state_update": {}
        }


def generate_opening_scene(player_name: str) -> str:
    """
    生成開局劇情
    """
    if config.DEBUG:
        print(f"\n【敘事大師】正在編織開局場景...")
    
    context = f"""
新弟子名稱: {player_name}
初始修為: 練氣期 1.0
初始位置: 青雲門·山腳

請為這位新弟子生成一個引人入勝的開局場景。
"""
    
    response = call_gpt(
        system_prompt=SYSTEM_OPENING_SCENE,
        user_message=context,
        model=config.MODEL_DRAMA,
        temperature=0.9
    )
    
    return response


# 並行調用優化（如果需要加速）
def call_logic_and_drama_parallel(player_state: Dict[str, Any],
                                  intent: Dict[str, Any],
                                  npc: Optional[Dict[str, Any]] = None,
                                  recent_events: list = None,
                                  world_map_context: str = None) -> Tuple[str, str]:
    """
    並行調用 Logic 和 Drama（帶上下文記憶 + 地圖約束）

    Args:
        player_state: 玩家狀態
        intent: 意圖字典
        npc: 目標 NPC
        recent_events: 最近事件記錄
        world_map_context: 地圖約束信息

    Returns:
        (logic_report, drama_proposal)
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        logic_future = executor.submit(agent_logic, player_state, intent, npc, recent_events, world_map_context)
        drama_future = executor.submit(agent_drama, player_state, intent, npc, recent_events)
        
        logic_report = logic_future.result()
        drama_proposal = drama_future.result()
    
    return logic_report, drama_proposal
