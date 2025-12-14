# docs_site/tools/profile_case.py
import sys
from pathlib import Path

# 让 docs_site 的解释器能导入主项目源码（保持隔离，不安装主项目）
ROOT = Path(__file__).resolve().parents[2]  # repo root
sys.path.insert(0, str(ROOT / "src"))

def run_case():
    """
    这里放“可重复、非 GUI”的最小案例。
    你只需要保证它能 import ds_vis 并执行一段逻辑即可。
    """

    # 示例（你需要替换为真实可运行的入口）：
    # from ds_vis.some_module import some_function
    # for i in range(1000):
    #     some_function(i)

    import ds_vis  # 用于验证导入路径 OK
    # TODO: replace with a real scenario in your project
    return

if __name__ == "__main__":
    run_case()
