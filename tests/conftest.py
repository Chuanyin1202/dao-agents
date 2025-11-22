# -*- coding: utf-8 -*-
"""
pytest 配置文件
提供全局 fixtures 和配置
"""

import sys
import os
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


# pytest 配置
def pytest_configure(config):
    """pytest 初始化配置"""
    config.addinivalue_line(
        "markers", "slow: 標記慢速測試（需要 API 調用）"
    )
    config.addinivalue_line(
        "markers", "integration: 標記整合測試"
    )
    config.addinivalue_line(
        "markers", "e2e: 標記端到端測試"
    )
    config.addinivalue_line(
        "markers", "consistency: 標記一致性測試"
    )


# 全局 fixtures
@pytest.fixture
def mock_env():
    """模擬環境變數（不使用真實 API）"""
    original_debug = os.getenv('DEBUG')
    original_mock = os.getenv('MOCK_AI')

    os.environ['DEBUG'] = 'true'
    os.environ['MOCK_AI'] = 'true'

    yield

    # 恢復原始環境
    if original_debug:
        os.environ['DEBUG'] = original_debug
    else:
        os.environ.pop('DEBUG', None)

    if original_mock:
        os.environ['MOCK_AI'] = original_mock
    else:
        os.environ.pop('MOCK_AI', None)


@pytest.fixture
def test_db_path(tmp_path):
    """提供臨時測試資料庫路徑"""
    db_path = tmp_path / "test_game_data.db"
    yield str(db_path)
    # pytest 會自動清理 tmp_path
