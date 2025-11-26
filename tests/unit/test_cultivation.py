# -*- coding: utf-8 -*-
"""
境界修煉系統單元測試
測試 cultivation.py 的核心功能
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cultivation import (
    get_major_tier,
    get_sub_tier_name,
    get_tier_info,
    get_tier_display_name,
    calculate_breakthrough_rate,
    can_breakthrough,
    attempt_breakthrough,
    cultivate,
    get_cultivation_status,
    TIER_CONFIG,
    CULTIVATE_MP_COST,
    CULTIVATE_BASE_PROGRESS,
    LOCATION_CULTIVATION_BONUS,
)


class TestTierSystem:
    """測試境界系統"""

    def test_get_major_tier(self):
        """測試大境界提取"""
        assert get_major_tier(1.0) == 1
        assert get_major_tier(1.5) == 1
        assert get_major_tier(1.9) == 1
        assert get_major_tier(2.0) == 2
        assert get_major_tier(3.3) == 3

    def test_get_sub_tier_name(self):
        """測試小境界名稱"""
        assert get_sub_tier_name(1.0) == "初期"
        assert get_sub_tier_name(1.2) == "初期"
        assert get_sub_tier_name(1.3) == "中期"
        assert get_sub_tier_name(1.5) == "中期"
        assert get_sub_tier_name(1.6) == "後期"
        assert get_sub_tier_name(1.9) == "後期"

    def test_get_tier_info(self):
        """測試境界資訊獲取"""
        info = get_tier_info(1.5)
        assert info["major_tier"] == 1
        assert info["tier_name"] == "練氣期"
        assert info["sub_tier_name"] == "中期"
        assert info["full_name"] == "練氣期中期"
        assert info["required_progress"] == 100
        assert info["base_success_rate"] == 70

    def test_get_tier_display_name(self):
        """測試境界顯示名稱"""
        assert get_tier_display_name(1.0) == "練氣期初期"
        assert get_tier_display_name(2.5) == "築基期中期"
        assert get_tier_display_name(3.8) == "元嬰期後期"


class TestBreakthroughRate:
    """測試突破成功率計算"""

    def test_base_rate(self):
        """測試基礎成功率"""
        # 練氣期基礎 70%
        rate = calculate_breakthrough_rate(1.0, karma=0)
        assert rate == 70.0

        # 築基期基礎 60%
        rate = calculate_breakthrough_rate(2.0, karma=0)
        assert rate == 60.0

    def test_karma_bonus(self):
        """測試氣運加成"""
        # 每點氣運 +0.5%
        rate = calculate_breakthrough_rate(1.0, karma=10)
        assert rate == 75.0  # 70 + 10*0.5 = 75

        rate = calculate_breakthrough_rate(1.0, karma=50)
        assert rate == 95.0  # 70 + 25 = 95（封頂）

    def test_rate_limits(self):
        """測試成功率上下限"""
        # 最低 5%
        rate = calculate_breakthrough_rate(6.0, karma=-100)
        assert rate == 5.0

        # 最高 95%
        rate = calculate_breakthrough_rate(1.0, karma=100)
        assert rate == 95.0


class TestCanBreakthrough:
    """測試突破條件檢查"""

    def test_insufficient_progress(self):
        """測試進度不足"""
        state = {
            "tier": 1.0,
            "cultivation_progress": 50,
            "hp": 100,
            "max_hp": 100,
        }
        can_break, reason = can_breakthrough(state)
        assert can_break is False
        assert "進度不足" in reason

    def test_sufficient_progress(self):
        """測試進度充足"""
        state = {
            "tier": 1.0,
            "cultivation_progress": 100,
            "hp": 100,
            "max_hp": 100,
        }
        can_break, reason = can_breakthrough(state)
        assert can_break is True

    def test_low_hp(self):
        """測試生命值過低"""
        state = {
            "tier": 1.0,
            "cultivation_progress": 100,
            "hp": 40,
            "max_hp": 100,
        }
        can_break, reason = can_breakthrough(state)
        assert can_break is False
        assert "生命值過低" in reason

    def test_max_tier(self):
        """測試已達最高境界"""
        state = {
            "tier": 6.9,
            "cultivation_progress": 9999,
            "hp": 100,
            "max_hp": 100,
        }
        can_break, reason = can_breakthrough(state)
        assert can_break is False
        assert "度劫期巔峰" in reason


class TestAttemptBreakthrough:
    """測試突破嘗試"""

    def test_breakthrough_result_structure(self):
        """測試突破結果結構"""
        state = {
            "tier": 1.0,
            "cultivation_progress": 100,
            "hp": 100,
            "max_hp": 100,
            "max_mp": 50,
            "karma": 0,
            "breakthrough_attempts": 0,
        }
        result = attempt_breakthrough(state)

        # 檢查必要欄位
        assert "success" in result
        assert "state_changes" in result
        assert "narrative_hint" in result
        assert "message" in result
        assert "success_rate" in result
        assert "roll" in result

    def test_success_changes(self):
        """測試成功時的狀態變更（使用確定性測試）"""
        # 注意：由於使用 random，這裡測試結構而非具體值
        state = {
            "tier": 1.0,
            "cultivation_progress": 100,
            "hp": 100,
            "max_hp": 100,
            "max_mp": 50,
            "karma": 100,  # 高氣運確保成功率高
            "breakthrough_attempts": 0,
        }

        # 多次嘗試，至少應該有一次成功
        successes = 0
        for _ in range(20):
            result = attempt_breakthrough(state)
            if result["success"]:
                successes += 1
                # 驗證成功時的狀態變更
                changes = result["state_changes"]
                assert changes["tier"] == 1.3
                assert changes["cultivation_progress"] == 0
                assert "max_hp_change" in changes
                assert "max_mp_change" in changes
                break

        assert successes > 0, "20 次嘗試應該至少成功一次（95% 成功率）"

    def test_failure_changes(self):
        """測試失敗時的狀態變更"""
        state = {
            "tier": 6.0,  # 度劫期，10% 基礎成功率
            "cultivation_progress": 9999,
            "hp": 100,
            "max_hp": 100,
            "max_mp": 50,
            "karma": -100,  # 低氣運
            "breakthrough_attempts": 0,
        }

        # 多次嘗試，應該有失敗的情況
        failures = 0
        for _ in range(50):
            result = attempt_breakthrough(state)
            if not result["success"]:
                failures += 1
                # 驗證失敗時的狀態變更
                changes = result["state_changes"]
                assert "hp_change" in changes
                assert changes["hp_change"] < 0
                assert changes["cultivation_progress"] < state["cultivation_progress"]
                break

        assert failures > 0, "50 次嘗試應該至少失敗一次（5% 成功率）"


class TestCultivate:
    """測試修煉功能"""

    def test_mp_insufficient(self):
        """測試法力不足"""
        state = {
            "mp": 5,
            "cultivation_progress": 0,
            "tier": 1.0,
        }
        result = cultivate(state, "qingyun_foot")

        assert result["success"] is False
        assert "法力不足" in result["message"]
        assert result["progress_gained"] == 0

    def test_normal_cultivate(self):
        """測試正常修煉"""
        state = {
            "mp": 50,
            "cultivation_progress": 0,
            "tier": 1.0,
        }
        result = cultivate(state, "qingyun_foot")

        assert result["success"] is True
        assert result["mp_cost"] == CULTIVATE_MP_COST
        assert result["progress_gained"] == CULTIVATE_BASE_PROGRESS
        assert result["state_changes"]["mp_change"] == -CULTIVATE_MP_COST
        assert result["state_changes"]["cultivation_progress"] == CULTIVATE_BASE_PROGRESS

    def test_location_bonus(self):
        """測試地點修煉加成"""
        state = {
            "mp": 50,
            "cultivation_progress": 0,
            "tier": 1.0,
        }

        # 靈池 +50% 加成
        result = cultivate(state, "qingyun_pool")
        expected_progress = int(CULTIVATE_BASE_PROGRESS * LOCATION_CULTIVATION_BONUS["qingyun_pool"])
        assert result["progress_gained"] == expected_progress
        assert "地點加成" in result["message"]

    def test_progress_cap(self):
        """測試進度不超過所需值"""
        state = {
            "mp": 50,
            "cultivation_progress": 95,
            "tier": 1.0,
        }
        result = cultivate(state, "qingyun_foot")

        # 練氣期所需 100，95+10=105 應該被限制為 100
        assert result["state_changes"]["cultivation_progress"] == 100

    def test_breakthrough_ready_message(self):
        """測試修煉圓滿提示"""
        state = {
            "mp": 50,
            "cultivation_progress": 95,
            "tier": 1.0,
            "hp": 100,
            "max_hp": 100,
        }
        result = cultivate(state, "qingyun_foot")

        assert "可以嘗試突破" in result["message"]


class TestCultivationStatus:
    """測試修煉狀態摘要"""

    def test_status_structure(self):
        """測試狀態摘要結構"""
        state = {
            "tier": 1.5,
            "cultivation_progress": 50,
            "karma": 10,
            "breakthrough_attempts": 2,
            "hp": 100,
            "max_hp": 100,
        }
        status = get_cultivation_status(state)

        assert status["tier"] == 1.5
        assert status["tier_name"] == "練氣期中期"
        assert status["progress"] == 50
        assert status["required"] == 100
        assert status["progress_percent"] == 50
        assert status["can_breakthrough"] is False
        assert status["success_rate"] == 75.0  # 70 + 10*0.5
        assert status["attempts"] == 2


class TestTierConfig:
    """測試境界配置完整性"""

    def test_all_tiers_defined(self):
        """測試所有境界都有配置"""
        for tier in range(1, 7):
            assert tier in TIER_CONFIG
            config = TIER_CONFIG[tier]
            assert "name" in config
            assert "required_progress" in config
            assert "base_success_rate" in config
            assert "hp_bonus" in config
            assert "mp_bonus" in config

    def test_tier_progression(self):
        """測試境界難度遞增"""
        prev_required = 0
        prev_rate = 100

        for tier in range(1, 6):  # 1-5
            config = TIER_CONFIG[tier]
            # 所需進度應該遞增
            assert config["required_progress"] > prev_required
            # 成功率應該遞減
            assert config["base_success_rate"] < prev_rate

            prev_required = config["required_progress"]
            prev_rate = config["base_success_rate"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
