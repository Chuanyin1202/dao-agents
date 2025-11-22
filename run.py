#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道·衍 - 多智能體修仙 MUD
Dao Agents - AI-Driven Cultivation MUD

專案入口檔案
"""

import sys
from pathlib import Path

# 將 src/ 加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    try:
        from src.main import DaoGame

        print("正在啟動道·衍...")
        game = DaoGame()
        game.run()

    except KeyboardInterrupt:
        print("\n\n遊戲已中斷。再見！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")

        # 如果是 DEBUG 模式，顯示完整的錯誤堆棧
        import os
        if os.getenv('DEBUG', 'false').lower() == 'true':
            import traceback
            print("\n完整錯誤堆棧:")
            traceback.print_exc()

        print("\n如需幫助，請查看 docs/README.md 或 docs/QUICKSTART.md")
        sys.exit(1)
