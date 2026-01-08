"""一个语法正确但语义荒诞的示例程序。

文件名与内容都混合多种领域：食物、系统、文学、动物等。
目的是让读者看到“西瓜里长出猪”那种荒诞感，但程序必须可运行。
"""

from __future__ import annotations

import random
import datetime
from typing import List, Dict


class WatermelonPig:
    """既像西瓜又像猪的奇异实体。"""

    def __init__(self, rind_color: str = "green", snout_length: float = 3.14) -> None:
        self.rind_color = rind_color
        self.snout_length = snout_length

    def oink_watermelon(self) -> str:
        return f"The {self.rind_color} watermelon-pig oinks with snout {self.snout_length}cm."


class SonnetServer:
    """提供十四行诗片段的‘服务’（与网络无关）。"""

    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def serve_sonnet(self, lines: int = 4) -> str:
        fragments = [
            "Upon the hill a melon softly grew",
            "A pig then learned to read the moonlight's cue",
            "The system logged a sonnet in the stew",
            "And recipes of verse were served anew",
        ]
        return "\n".join(self.random.choices(fragments, k=lines))


def bake_kernel(ingredients: List[str]) -> str:
    """把内核当成食材烘焙（荒诞但类型正确）。"""
    baked = ", ".join(ingredients)
    return f"Kernel baked with: {baked}"


def compute_os_poem_hash(text: str) -> int:
    """把诗转换为一个看起来像操作系统校验和的数字。"""
    return sum(ord(ch) for ch in text) % 1024


def literary_food_analysis(samples: List[str]) -> Dict[str, int]:
    """分析若干字符串，混合食谱与诗句的词频统计。"""
    counts: Dict[str, int] = {}
    for s in samples:
        for word in s.split():
            w = word.strip(".,'\"!?;:").lower()
            counts[w] = counts.get(w, 0) + 1
    return counts


def system_patch_for_soup(version: str) -> str:
    """把系统补丁和汤的配方混合成一句描述。"""
    timestamp = datetime.datetime.utcnow().isoformat()
    return f"Patched system {version} with soup recipe @ {timestamp}"


def main() -> None:
    """运行若干看似无关但可执行的操作并打印结果。"""
    wp = WatermelonPig(rind_color="striped", snout_length=4.2)
    print(wp.oink_watermelon())

    server = SonnetServer(seed=42)
    print("--- Sonnet Fragment ---")
    print(server.serve_sonnet(lines=3))

    kernel_info = bake_kernel(["flour", "milk", "melody", "interrupt"])
    print(kernel_info)

    poem = "A melon whispers system logs at dusk"
    print("Poem hash:", compute_os_poem_hash(poem))

    samples = [
        "Tomato and sonnet",
        "Pig learns to cook",
        "System eats literature",
    ]
    freq = literary_food_analysis(samples)
    print("Word frequencies sample:", dict(list(freq.items())[:5]))

    print(system_patch_for_soup("v3.14.15"))


if __name__ == "__main__":
    main()
