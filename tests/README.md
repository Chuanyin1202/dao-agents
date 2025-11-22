# 道·衍測試框架

## 📋 目錄結構

```
tests/
├── fixtures/              # 測試工具類
│   ├── game_simulator.py      # 遊戲環境模擬器
│   ├── state_inspector.py     # 狀態一致性檢查器
│   └── narrative_analyzer.py  # 劇情分析器
│
├── unit/                  # 單元測試
│   ├── test_validators.py     # 驗證器測試
│   ├── test_world_map.py      # 地圖功能測試
│   └── test_time_engine.py    # 時間引擎測試
│
├── integration/           # 整合測試（多組件協作）
│   └── (待實現)
│
├── e2e/                   # 端到端測試（完整用戶流程）
│   └── test_movement_scenarios.py  # 移動場景測試
│
├── consistency/           # 一致性測試（UI vs 實際）
│   ├── test_ui_consistency.py      # UI 提示一致性
│   └── test_narrative_state.py     # 劇情狀態一致性
│
└── regression/            # 回歸測試（防止 bug 復發）
    └── test_known_bugs.py          # 已知 bug 測試
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
source venv/bin/activate
pip install pytest pytest-cov pytest-html
```

### 2. 運行測試

```bash
# 查看幫助
./run_tests.sh help

# 快速測試（只跑單元測試）
./run_tests.sh quick

# 一致性測試（最關鍵！）
./run_tests.sh consistency

# 回歸測試（檢查已知 bug）
./run_tests.sh regression

# 完整測試
./run_tests.sh full

# 生成覆蓋率報告
./run_tests.sh coverage
```

### 3. 查看結果

測試完成後會生成：
- 終端輸出：即時測試結果
- `TEST_RESULTS.md`：詳細測試報告
- `test_report.html`：HTML 測試報告（coverage 模式）
- `htmlcov/index.html`：覆蓋率報告（coverage 模式）

## 📊 測試類型說明

### 單元測試 (Unit Tests)
測試單一函數的正確性

**特點**：
- 快速執行
- 測試單一功能
- 不依賴外部服務

**例子**：
```python
def test_normalize_direction():
    assert normalize_direction('n') == 'north'
    assert normalize_direction('北') == 'north'
```

### 整合測試 (Integration Tests)
測試多個組件協作

**特點**：
- 測試組件間交互
- 驗證數據流動
- 檢查接口兼容性

**例子**：
```python
def test_observer_to_validator_chain():
    intent = agent_observer('我要往北走')
    validation = validate_movement(current_loc, intent['target'], tier)
    assert validation['valid']
```

### 端到端測試 (E2E Tests)
模擬完整用戶操作

**特點**：
- 測試完整流程
- 最接近真實使用
- 可能需要 API Key

**例子**：
```python
def test_complete_movement_flow(game_sim):
    game_sim.simulate_input("m")  # 移動選單
    result = game_sim.simulate_input("n")  # 選擇北
    assert result["state_after"]["location_id"] == "qingyun_plaza"
```

### 一致性測試 (Consistency Tests)
**最重要的測試！**

檢查 UI 提示與實際功能、劇情與狀態的一致性

**特點**：
- 發現設計矛盾
- 檢測用戶體驗問題
- 驗證遊戲可玩性

**例子**：
```python
def test_ui_promises_n_works():
    # UI 提示：北 (n)
    # 用戶輸入：n
    # 期望：成功移動
    # 實際：失敗 ❌（測試會抓到這個問題）
```

### 回歸測試 (Regression Tests)
防止已修復 bug 復發

**特點**：
- 每個修復的 bug 都有對應測試
- 持續追蹤已知問題
- 確保修復有效

**例子**：
```python
def test_bug_20241122_npc_injury_misidentified():
    # Bug: NPC 受傷被誤判為玩家受傷
    # 修復日期: 2024-11-22
    # 此測試確保不會復發
```

## 🛠️ 測試工具

### GameSimulator
完整遊戲環境模擬器

```python
from fixtures import GameSimulator

sim = GameSimulator(mock_ai=True)
sim.create_test_player(location_id="qingyun_foot")
result = sim.simulate_input("m")
assert "可用方向" in result["output"]
```

### StateInspector
狀態一致性檢查器

```python
from fixtures import StateInspector

inspector = StateInspector()
errors = inspector.check_all(player_state)
diff = inspector.diff_states(state_before, state_after)
```

### NarrativeAnalyzer
劇情分析器

```python
from fixtures import NarrativeAnalyzer

analyzer = NarrativeAnalyzer()
result = analyzer.analyze_consistency(
    narrative="你被打傷了",
    state_update={'hp_change': -10},
    player_state_before=...,
    player_state_after=...
)
```

## 📝 編寫新測試

### 1. 選擇測試類型

根據測試目的選擇目錄：
- 測單一函數 → `tests/unit/`
- 測組件協作 → `tests/integration/`
- 測完整流程 → `tests/e2e/`
- 測 UI 一致性 → `tests/consistency/`
- 防 bug 復發 → `tests/regression/`

### 2. 創建測試文件

```python
# tests/consistency/test_my_feature.py

import pytest
from fixtures import GameSimulator

class TestMyFeature:
    def test_feature_works(self, game_sim):
        # Arrange
        game_sim.create_test_player()

        # Act
        result = game_sim.simulate_input("my_command")

        # Assert
        assert result["success"]
```

### 3. 運行測試

```bash
pytest tests/consistency/test_my_feature.py -v
```

## 🎯 測試最佳實踐

### ✅ 好的測試

```python
def test_user_can_move_north_from_foot():
    """
    測試：用戶從山腳往北移動

    預期：成功移動到外門廣場
    """
    # 測試完整流程
    # 清楚的期望
    # 有意義的失敗訊息
```

### ❌ 壞的測試

```python
def test_stuff():
    # 沒說明測什麼
    # 沒有清楚的期望
    # 失敗了不知道為什麼
```

### 測試命名規範

- `test_功能_場景_期望結果`
- 例如：`test_movement_single_letter_n_succeeds`
- 使用 docstring 說明測試目的

### 斷言訊息

```python
# ✅ 好
assert hp == 90, f"期望 HP=90, 實際 HP={hp}"

# ❌ 壞
assert hp == 90
```

## 🔍 調試測試

### 查看詳細輸出

```bash
pytest tests/consistency/ -v -s
```

### 只運行特定測試

```bash
pytest tests/consistency/test_ui_consistency.py::TestUIConsistency::test_observer_direction_recognition_rate -v -s
```

### 在失敗時進入調試器

```bash
pytest tests/consistency/ --pdb
```

## 📈 持續改進

### 每次修復 bug

1. 在 `tests/regression/test_known_bugs.py` 添加測試
2. 運行測試確保失敗（證明 bug 存在）
3. 修復 bug
4. 運行測試確保通過
5. 提交代碼

### 每次添加功能

1. 先寫測試（TDD）
2. 測試失敗（功能未實現）
3. 實現功能
4. 測試通過
5. 提交代碼

### 定期檢查

```bash
# 每週運行完整測試
./run_tests.sh full

# 每月生成覆蓋率報告
./run_tests.sh coverage
```

## 🎓 核心理念

### 為什麼之前的測試沒用？

```python
# ❌ 舊測試：只測函數
test normalize_direction('n') == 'north'  # ✅ 通過

# 但實際遊戲：
用戶輸入 'n' → Observer → INSPECT ❌ → 失敗
            （這一步沒測！）
```

### 新測試框架的優勢

```python
# ✅ 新測試：測完整流程
test_user_inputs_n_can_move()
  → 模擬完整輸入流程
  → 驗證最終結果
  → ❌ 失敗！立即發現問題！
```

**結論**：測試要反映真實使用場景，而非只測單一函數。

## 🆘 常見問題

### Q: 測試失敗了怎麼辦？

A:
1. 看失敗訊息，理解問題
2. 如果是真 bug → 修復代碼
3. 如果測試寫錯 → 修復測試
4. 如果是已知限制 → 標記為 `pytest.skip()`

### Q: 一致性測試都失敗正常嗎？

A:
**是的！** 這正是測試框架的目的。當前狀態：
- Observer 識別成功率：36.4%
- 測試通過率：35%

**這說明遊戲有嚴重問題**，測試成功發現了問題。

### Q: 測試跑太慢怎麼辦？

A:
- 使用 `pytest.mark.slow` 標記慢速測試
- 平時只跑快速測試：`./run_tests.sh quick`
- CI/CD 跑完整測試

### Q: 需要 API Key 嗎？

A:
- 單元測試：不需要
- 一致性測試：需要（會調用 Observer）
- 端到端測試：需要（會調用所有 AI agents）

設置方法：
```bash
export OPENAI_API_KEY=your_key_here
```

## 📚 延伸閱讀

- [pytest 官方文檔](https://docs.pytest.org/)
- [測試金字塔](https://martinfowler.com/articles/practical-test-pyramid.html)
- [TDD 實踐](https://www.jamesshore.com/v2/books/aoad1/test-driven-development)
