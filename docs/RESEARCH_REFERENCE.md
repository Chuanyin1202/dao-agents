# Generative Agents 研究參考文獻

> 本文件記錄 Stanford Generative Agents 相關研究，作為 dao-agents 專案的架構參考。

---

## 目錄

1. [論文概述](#論文概述)
2. [核心架構](#核心架構)
3. [Memory Stream 記憶流](#memory-stream-記憶流)
4. [Reflection 反思機制](#reflection-反思機制)
5. [Planning 計劃系統](#planning-計劃系統)
6. [對 dao-agents 的啟發](#對-dao-agents-的啟發)
7. [實作建議](#實作建議)
8. [參考資源](#參考資源)

---

## 論文概述

### 主要論文

**Generative Agents: Interactive Simulacra of Human Behavior**
- 作者：Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein
- 機構：Stanford University, Google Research, Google DeepMind
- 發表：UIST '23, October 2023
- arXiv：2304.03442v2

### 核心貢獻

1. **Generative Agents**：能模擬可信人類行為的計算代理
2. **Memory Stream 架構**：自然語言記錄代理的完整經歷
3. **三維檢索機制**：結合 recency、relevance、importance
4. **Reflection 機制**：從記憶中合成高層次洞察
5. **Smallville 沙盒**：25 個代理的互動社區模擬

### 相關專案

| 專案 | 用途 | GitHub |
|------|------|--------|
| generative_agents | Smallville 原始實現 | joonspk-research/generative_agents |
| genagents | 模擬 1000 個真實受訪者 | StanfordHCI/genagents |

---

## 核心架構

```
┌─────────────────────────────────────────────────────────────┐
│                  Generative Agent Memory                     │
│  ┌─────────┐    ┌─────────────┐    ┌──────────┐    ┌─────┐ │
│  │ Perceive│───▶│Memory Stream│───▶│ Retrieve │───▶│ Act │ │
│  └─────────┘    └──────┬──────┘    └────┬─────┘    └─────┘ │
│                        │                │                    │
│                        ▼                │                    │
│                   ┌─────────┐           │                    │
│                   │ Reflect │◀──────────┘                    │
│                   └────┬────┘                                │
│                        │                                     │
│                        ▼                                     │
│                   ┌─────────┐                                │
│                   │  Plan   │                                │
│                   └─────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### 運作流程

1. **Perceive（感知）**：代理觀察環境和其他代理
2. **Memory Stream（記憶流）**：所有感知存入記憶流
3. **Retrieve（檢索）**：根據當前情境檢索相關記憶
4. **Act（行動）**：基於檢索的記憶決定行動
5. **Reflect（反思）**：定期從記憶中提煉高層洞察
6. **Plan（計劃）**：生成和維護長短期計劃

---

## Memory Stream 記憶流

### 記憶物件結構

```python
class MemoryObject:
    description: str      # 自然語言描述
    created: datetime     # 創建時間戳
    last_accessed: datetime  # 最後存取時間戳
    importance: int       # 重要性評分 (1-10)
    embedding: List[float]  # 文本嵌入向量（可選）
```

### 記憶類型

| 類型 | 說明 | 範例 |
|------|------|------|
| **Observation** | 直接感知的事件 | "Isabella Rodriguez is setting out the pastries" |
| **Reflection** | 高層次推論 | "Klaus Mueller is dedicated to his research" |
| **Plan** | 未來行動計劃 | "At 12pm, have lunch at Hobbs Cafe" |

### 三維檢索公式

```
score = α_recency × recency + α_importance × importance + α_relevance × relevance
```

#### Recency（時近性）

- 指數衰減函數
- decay factor = 0.995
- 基於遊戲時間（非真實時間）

```python
def recency_score(hours_since_access: float, decay: float = 0.995) -> float:
    return decay ** hours_since_access
```

#### Importance（重要性）

- 由 LLM 評分 1-10
- 創建記憶時生成

**評分 Prompt：**
```
On the scale of 1 to 10, where 1 is purely mundane
(e.g., brushing teeth, making bed) and 10 is extremely
poignant (e.g., a break up, college acceptance), rate
the likely poignancy of the following piece of memory.

Memory: {memory_description}
Rating: <fill in>
```

**評分範例：**
- "buying groceries" → 2
- "asking your crush out on a date" → 8

#### Relevance（相關性）

- 使用 embedding 向量的 cosine similarity
- 查詢記憶與目標記憶的語意相似度

```python
def relevance_score(query_embedding: List[float], memory_embedding: List[float]) -> float:
    return cosine_similarity(query_embedding, memory_embedding)
```

### 檢索流程

1. 對所有記憶計算三維分數
2. Min-max 正規化到 [0, 1]
3. 加權求和（預設 α 均為 1）
4. 取 top-k 放入 prompt context

---

## Reflection 反思機制

### 觸發條件

當最近事件的 importance 總和超過閾值（預設 150）時觸發。
實際運作中，代理約每天反思 2-3 次。

### 反思流程

```
步驟 1：生成反思問題
────────────────────
輸入：最近 100 條記憶
Prompt：「根據以上資訊，可以回答哪 3 個最顯著的高層問題？」
輸出：候選問題列表

步驟 2：檢索相關記憶
────────────────────
對每個問題執行記憶檢索

步驟 3：提煉洞察
────────────────────
Prompt：「從以下陳述中，可以推論出哪 5 個高層洞察？」
輸出格式：insight (because of 1, 5, 3)

步驟 4：存入記憶流
────────────────────
將洞察作為新記憶存入，包含來源記憶的指標
```

### 反思 Prompt 範例

```
Statements about Klaus Mueller
1. Klaus Mueller is writing a research paper
2. Klaus Mueller enjoys reading a book on gentrification
3. Klaus Mueller is conversing with Ayesha Khan about exercising [...]

What 5 high-level insights can you infer from the above statements?
(example format: insight (because of 1, 5, 3))
```

### 反思樹結構

```
                    [高層反思]
                   Klaus Mueller is
                highly dedicated to research
                    /          \
           [中層反思]          [中層反思]
        Klaus is dedicated    Klaus is engaging
          to research       in research activities
              |                    |
        ┌─────┴─────┐        ┌─────┴─────┐
   [觀察]      [觀察]    [觀察]      [觀察]
 writing    reading   making     searching
  paper    gentrification connections  articles
```

- **葉節點**：原始觀察（observations）
- **非葉節點**：反思（reflections）
- **特性**：反思可以基於其他反思，形成多層抽象

---

## Planning 計劃系統

### 遞迴分解策略

```
日計劃（broad strokes）
│
├── 1) wake up and complete morning routine at 8:00 am
├── 2) go to Oak Hill College to take classes at 10:00 am
├── 3) have lunch at 12:00 pm
├── 4) work on music composition from 1:00 pm to 5:00 pm
├── 5) have dinner at 5:30 pm
└── 6) finish assignments and sleep by 11:00 pm
        │
        ▼ 分解
小時計劃
│
├── 1:00 pm: start brainstorming ideas for composition
├── 2:00 pm: work on the melody
├── 3:00 pm: refine the harmony
└── 4:00 pm: take a break and recharge
        │
        ▼ 分解
分鐘計劃（5-15 分鐘）
│
├── 4:00 pm: grab a light snack
├── 4:05 pm: take a short walk
├── 4:15 pm: return to workspace
└── 4:50 pm: clean up workspace
```

### 計劃生成 Prompt

```
Name: Eddy Lin (age: 19)
Innate traits: friendly, outgoing, hospitable
Eddy Lin is a student at Oak Hill College studying music theory and composition...

On Tuesday February 12, Eddy 1) woke up and completed the morning routine at 7:00 am, [...]
6) got ready to sleep around 10 pm.

Today is Wednesday February 13. Here is Eddy's plan today in broad strokes: 1)
```

### 計劃更新機制

- 計劃存入記憶流，可被檢索
- 遇到新事件時，代理決定是否需要更新計劃
- 支援中途修改和重新規劃

---

## 對 dao-agents 的啟發

### 架構對比

| 層面 | dao-agents 現狀 | Generative Agents | 建議 |
|------|----------------|-------------------|------|
| **記憶存儲** | `recent_events` 列表 | Memory Stream + 結構化節點 | 升級為結構化記憶 |
| **記憶檢索** | 線性 `[-10:]` 取最近 | 三維加權檢索 | 實現 recency + relevance + importance |
| **重要性** | 無 | LLM 評分 1-10 | 為事件添加重要性評分 |
| **反思** | 無 | 定期反思機制 | NPC 對玩家形成「印象」 |
| **計劃** | 單一行動 | 遞迴分解計劃 | NPC 可有長期目標 |
| **信息擴散** | 無 | 代理間自然傳播 | 事件在 NPC 間傳播 |

### 修仙世界適配

#### Importance 評分適配

```python
IMPORTANCE_PROMPT_CULTIVATION = """
在 1-10 的量表上評估以下修仙世界事件的重要性：

1 = 完全平凡（走路、休息、日常對話）
3 = 輕微重要（獲得普通資源、遭遇普通妖獸）
5 = 中等重要（學會新功法、結識重要人物）
7 = 重要事件（突破境界、重大戰鬥勝利）
9 = 極為重大（獲得神器、生死大戰、渡劫）
10 = 命運轉折（飛升、隕落、大道感悟）

事件：{event_description}
評分：
"""
```

#### 記憶節點結構建議

```python
@dataclass
class CultivationMemoryNode:
    id: str
    event_type: str          # action / cultivation / combat / dialogue / discovery
    description: str
    importance: int          # 1-10
    tick_created: int
    embedding: Optional[List[float]]  # 用於語意檢索
    related_npcs: List[str]  # 相關 NPC
    location: str
    cultivation_realm: str   # 事件發生時的境界

    # 可選：用於反思追溯
    source_memories: List[str]  # 如果是反思，記錄來源記憶 ID
```

#### 反思機制應用

**NPC 對玩家的反思範例：**
```
基於觀察：
1. 玩家多次在危險時出手相助
2. 玩家對弱者展現同情
3. 玩家拒絕了不義之財

反思結果：
「此人行事光明磊落，似有正道風範，值得深交。」
```

**Drama Agent 的伏筆應用：**
```
基於反思「玩家與青雲門有宿怨」
可以在未來劇情中自然引入青雲門相關衝突
```

---

## 實作建議

### 優先級排序

```
高優先級（立即可做）
├── 1. 為事件添加 importance 評分
│   └── 修改 event_log 結構，添加 importance 欄位
├── 2. 改進記憶檢索
│   └── 實現加權公式：recency + importance
└── 3. NPC 記憶玩家的重大事件
    └── 重要性 >= 7 的事件長期保留

中優先級（架構調整）
├── 4. 反思機制
│   └── NPC 定期總結對玩家的「印象」
├── 5. 計劃系統
│   └── NPC 可有自己的長期目標
└── 6. 信息擴散
    └── 重大事件在 NPC 間傳播

低優先級（長期目標）
├── 7. Embedding 向量檢索
│   └── 需要額外基礎設施
└── 8. 多 NPC 協調
    └── 門派聯合行動、群體事件
```

### 最小可行實現

```python
# 第一步：簡化版三維檢索
def retrieve_memories(
    memories: List[dict],
    query: str,
    current_tick: int,
    top_k: int = 10,
    weights: Tuple[float, float, float] = (1.0, 1.0, 0.5)  # recency, importance, relevance
) -> List[dict]:
    """
    簡化版記憶檢索（不需要 embedding）
    """
    recency_w, importance_w, relevance_w = weights
    scored = []

    for mem in memories:
        # Recency: 指數衰減
        ticks_ago = current_tick - mem['tick']
        recency = 0.995 ** (ticks_ago / 10)  # 每 10 tick 衰減一次

        # Importance: 直接使用
        importance = mem.get('importance', 5) / 10  # 正規化到 0-1

        # Relevance: 簡化版 - 關鍵字匹配
        relevance = keyword_match_score(query, mem['description'])

        score = recency_w * recency + importance_w * importance + relevance_w * relevance
        scored.append((score, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mem for _, mem in scored[:top_k]]
```

---

## 參考資源

### 論文

1. **Generative Agents: Interactive Simulacra of Human Behavior**
   - arXiv: https://arxiv.org/abs/2304.03442
   - PDF: 2304.03442v2.pdf

### GitHub 專案

1. **generative_agents**（Smallville 原始實現）
   - https://github.com/joonspk-research/generative_agents
   - 技術棧：Python + Django + Phaser.js

2. **genagents**（模擬真實受訪者）
   - https://github.com/StanfordHCI/genagents
   - 核心檔案：
     - `genagents.py` - GenerativeAgent 類
     - `modules/memory_stream.py` - MemoryStream + ConceptNode
     - `modules/interaction.py` - 回應生成

### 關鍵程式碼參考

**genagents/modules/memory_stream.py 檢索演算法：**
```python
# 三維加權
for key in recency_out.keys():
    master_out[key] = (
        recency_w * recency_out[key] +
        relevance_w * relevance_out[key] +
        importance_w * importance_out[key]
    )
```

### 評估指標

論文中的評估方法：
1. **Interview Protocol**：用自然語言「訪談」代理
2. **TrueSkill Rating**：多條件排名評分
3. **Ablation Study**：移除各組件測試影響

評估類別：
- Self-knowledge（自我認知）
- Memory（記憶能力）
- Plans（計劃能力）
- Reactions（反應能力）
- Reflections（反思能力）

---

## 更新日誌

| 日期 | 更新內容 |
|------|---------|
| 2025-12-01 | 初始版本，整理論文核心架構和實作建議 |

---

## 附錄：論文圖表索引

| 圖表 | 內容 |
|------|------|
| Figure 1 | Smallville 沙盒環境概覽 |
| Figure 2 | 環境樹狀結構（區域、物件） |
| Figure 3 | John Lin 的一天生活 |
| Figure 4 | Valentine's Day Party 協調 |
| Figure 5 | **核心架構圖** |
| Figure 6 | Memory Stream 與檢索流程 |
| Figure 7 | **反思樹結構** |
| Figure 8 | 評估結果（TrueSkill 排名） |
| Figure 9 | 信息擴散路徑 |
