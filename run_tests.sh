#!/bin/bash
# 道·衍測試套件執行腳本

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              道·衍 - 結構化測試套件                            ║"
echo "║              Comprehensive Test Framework                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 未找到虛擬環境 venv${NC}"
    echo "請先執行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 啟動虛擬環境
source venv/bin/activate

# 檢查 pytest 是否安裝
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest 未安裝，正在安裝...${NC}"
    pip install pytest pytest-cov pytest-html
fi

# 解析參數
MODE=${1:-full}

if [ "$MODE" == "help" ] || [ "$MODE" == "-h" ] || [ "$MODE" == "--help" ]; then
    echo "使用方式:"
    echo "  ./run_tests.sh [mode]"
    echo ""
    echo "模式:"
    echo "  quick    - 快速測試 (只跑單元測試)"
    echo "  unit     - 單元測試"
    echo "  integration - 整合測試"
    echo "  e2e      - 端到端測試"
    echo "  consistency - 一致性測試"
    echo "  regression  - 回歸測試"
    echo "  full     - 完整測試 (預設)"
    echo "  coverage - 生成覆蓋率報告"
    echo ""
    echo "範例:"
    echo "  ./run_tests.sh quick      # 快速測試"
    echo "  ./run_tests.sh consistency # 只跑一致性測試"
    echo "  ./run_tests.sh coverage   # 完整測試 + 覆蓋率"
    exit 0
fi

# 測試函數
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    local marker=$3

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}▶  ${suite_name}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

    if [ -n "$marker" ]; then
        pytest "$test_path" -v -m "$marker" --tb=short || return 1
    else
        pytest "$test_path" -v --tb=short || return 1
    fi

    return 0
}

# 執行測試
case "$MODE" in
    quick)
        echo -e "${YELLOW}⚡ 快速測試模式${NC}"
        run_test_suite "單元測試" "tests/unit/" ""
        ;;

    unit)
        run_test_suite "單元測試" "tests/unit/" ""
        ;;

    integration)
        run_test_suite "整合測試" "tests/integration/" "integration"
        ;;

    e2e)
        echo -e "${YELLOW}注意: 端到端測試可能需要 API Key${NC}"
        if [ -z "$OPENAI_API_KEY" ]; then
            echo -e "${YELLOW}⚠️  OPENAI_API_KEY 未設置，某些測試可能跳過${NC}"
        fi
        run_test_suite "端到端測試" "tests/e2e/" "e2e"
        ;;

    consistency)
        run_test_suite "一致性測試" "tests/consistency/" "consistency"
        ;;

    regression)
        run_test_suite "回歸測試" "tests/regression/" ""
        ;;

    coverage)
        echo -e "${YELLOW}📊 完整測試 + 覆蓋率分析${NC}"
        pytest tests/ \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=html \
            --html=test_report.html \
            --self-contained-html \
            -v

        echo ""
        echo -e "${GREEN}✅ 測試完成！${NC}"
        echo -e "${BLUE}📊 查看報告:${NC}"
        echo "  - HTML 測試報告: test_report.html"
        echo "  - 覆蓋率報告: htmlcov/index.html"
        ;;

    full|*)
        echo -e "${BLUE}📋 完整測試流程${NC}"
        echo ""

        # 1. 單元測試
        if run_test_suite "1️⃣  單元測試" "tests/unit/" ""; then
            echo -e "${GREEN}✅ 單元測試通過${NC}"
        else
            echo -e "${RED}❌ 單元測試失敗${NC}"
            exit 1
        fi

        # 2. 整合測試
        if [ -d "tests/integration" ] && [ "$(ls -A tests/integration/*.py 2>/dev/null)" ]; then
            if run_test_suite "2️⃣  整合測試" "tests/integration/" ""; then
                echo -e "${GREEN}✅ 整合測試通過${NC}"
            else
                echo -e "${RED}❌ 整合測試失敗${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}⚠️  整合測試目錄為空，跳過${NC}"
        fi

        # 3. 端到端測試 (可能需要 API)
        if [ -z "$OPENAI_API_KEY" ]; then
            echo -e "${YELLOW}⚠️  跳過端到端測試 (需要 OPENAI_API_KEY)${NC}"
        else
            if run_test_suite "3️⃣  端到端測試" "tests/e2e/" ""; then
                echo -e "${GREEN}✅ 端到端測試通過${NC}"
            else
                echo -e "${RED}❌ 端到端測試失敗${NC}"
                exit 1
            fi
        fi

        # 4. 一致性測試 (核心測試！)
        if run_test_suite "4️⃣  一致性測試" "tests/consistency/" ""; then
            echo -e "${GREEN}✅ 一致性測試通過${NC}"
        else
            echo -e "${RED}❌ 一致性測試失敗${NC}"
            echo -e "${YELLOW}💡 一致性測試失敗通常表示 UI 提示與實際功能不符${NC}"
            exit 1
        fi

        # 5. 回歸測試 (檢查已知 bug)
        if run_test_suite "5️⃣  回歸測試" "tests/regression/" ""; then
            echo -e "${GREEN}✅ 回歸測試通過 (已知 bug 未復發)${NC}"
        else
            echo -e "${RED}❌ 回歸測試失敗 (已知 bug 可能復發)${NC}"
            exit 1
        fi

        echo ""
        echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ 所有測試通過！${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
        ;;
esac

echo ""
echo -e "${BLUE}💡 提示:${NC}"
echo "  - 生成覆蓋率報告: ./run_tests.sh coverage"
echo "  - 查看幫助: ./run_tests.sh help"
