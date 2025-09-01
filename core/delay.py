import time
import random


def random_delay(min_sec=1, max_sec=3):
    """
    在 [min_sec, max_sec] 区间内随机延时
    """
    delay = random.uniform(min_sec, max_sec)  # 生成随机浮点数
    print(f"[延时] {delay:.2f} 秒")
    time.sleep(delay)
