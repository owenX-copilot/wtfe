"""示例模块：包含一个类、函数和简单的运行器。

这个文件是为演示目的创建的，包含一个 `Greeter` 类、一个简单的
`add` 函数和一个可直接运行的 `main()`。
"""

from __future__ import annotations

class Greeter:
    """简单问候类。"""

    def __init__(self, name: str = "World") -> None:
        self.name = name

    def greet(self) -> str:
        """返回问候语字符串。"""
        return f"Hello, {self.name}!"


def add(a: int, b: int) -> int:
    """返回两个整数之和。"""
    return a + b


def main() -> None:
    """示例运行入口，打印问候语和加法示例。"""
    greeter = Greeter("wtfe")
    print(greeter.greet())
    print("2 + 3 =", add(2, 3))


if __name__ == "__main__":
    main()
