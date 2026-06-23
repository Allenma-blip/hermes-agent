# 基准脚本：测量 import time + tracemalloc 峰值内存
import time
import tracemalloc
import importlib
import sys


def run():
    if "gateway.platforms" in sys.modules:
        del sys.modules["gateway.platforms"]
    tracemalloc.start()
    t0 = time.perf_counter()
    importlib.import_module("gateway.platforms")
    t1 = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"import gateway.platforms: {t1 - t0:.3f}s, peak={peak} bytes")


if __name__ == "__main__":
    run()
