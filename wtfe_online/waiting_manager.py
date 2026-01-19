#!/usr/bin/env python3
"""
Waiting Manager Module

Provides elegant waiting effects for operations with uncertain duration.
Uses typing effect with backspace animation.
"""

import sys
import time
import threading
from typing import Optional, List
from contextlib import contextmanager
from enum import Enum


class EngineeringTermCategory(Enum):
    """Categories of engineering terms (kept for compatibility)"""
    GENERAL = "general"
    CODING = "coding"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    UPLOADING = "uploading"
    COMPRESSING = "compressing"
    GENERATING = "generating"


class WaitingManager:
    """Waiting Manager Class with typing effect only"""

    def __init__(self, title: str = "Processing", category: EngineeringTermCategory = None):
        """
        Initialize waiting manager

        Args:
            title: Waiting indicator title (not used in display)
            category: Engineering term category (used for message selection)
        """
        self.title = title
        self.category = category or EngineeringTermCategory.GENERAL
        self._running = False
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._typing_active = False
        self._typing_thread = None
        self._stop_typing_event = threading.Event()

    def start(self, message: str = None, total: Optional[int] = None):
        """
        Start waiting indicator

        Args:
            message: Initial message (ignored, typing effect will show its own messages)
            total: Total steps (if known) - ignored
        """
        self._running = True
        self._stop_event.clear()
        # No spinner thread needed

    def update(self, message: str = None, progress: Optional[float] = None):
        """
        Update waiting status (not used for typing effect)

        Args:
            message: New message (ignored)
            progress: Progress (between 0.0 and 1.0) - ignored
        """
        pass  # Typing effect manages its own messages

    def stop(self, message: str = "Done!"):
        """
        Stop waiting indicator

        Args:
            message: Completion message
        """
        self._running = False
        self._stop_event.set()
        
        # Stop typing effect if active
        self.stop_typing()
        
        # Clear the line and show completion message
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.write(f"✓ {message}\n")
        sys.stdout.flush()

    def cycle_typing_messages(self, messages: List[str], interval: float = 3.0):
        """
        Cycle through messages with typing effect including backspace

        Args:
            messages: List of messages to display
            interval: Time between message cycles (seconds)
        """
        self._stop_typing_event.clear()
        self._typing_active = True

        def typing_cycle():
            while not self._stop_typing_event.is_set():
                for msg in messages:
                    if self._stop_typing_event.is_set():
                        break
                    
                    # Clear line
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    sys.stdout.flush()
                    
                    # Type out message character by character
                    for i, char in enumerate(msg):
                        if self._stop_typing_event.is_set():
                            break
                        sys.stdout.write(char)
                        sys.stdout.flush()
                        time.sleep(0.03)  # Typing speed
                    
                    # Hold message for a short moment
                    if self._stop_typing_event.wait(timeout=0.5):
                        break
                    
                    # Backspace effect - delete character by character
                    for i in range(len(msg)):
                        if self._stop_typing_event.is_set():
                            break
                        sys.stdout.write('\b \b')  # Backspace and clear
                        sys.stdout.flush()
                        time.sleep(0.02)  # Backspace speed
                    
                    # Ensure line is completely cleared after backspace
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    sys.stdout.flush()
                    
                    # Wait before next message
                    if self._stop_typing_event.wait(timeout=interval):
                        break
            
            # Mark typing as inactive when loop ends
            self._typing_active = False
            # Clear line when typing stops
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            sys.stdout.flush()

        self._typing_thread = threading.Thread(target=typing_cycle, daemon=True)
        self._typing_thread.start()

    def stop_typing(self):
        """Stop typing effect"""
        self._stop_typing_event.set()
        if self._typing_thread:
            self._typing_thread.join(timeout=0.5)
        self._typing_active = False


@contextmanager
def waiting_context(title: str = "Processing", message: str = None,
                   category: EngineeringTermCategory = None):
    """
    Context manager for elegant waiting indicators

    Args:
        title: Waiting indicator title
        message: Initial message (ignored)
        category: Engineering term category

    Yields:
        WaitingManager: Waiting manager instance
    """
    manager = WaitingManager(title, category)
    manager.start(message)
    
    # Define comforting messages for each category - avoid misleading "即将完成"
    comforting_messages = {
        EngineeringTermCategory.PROCESSING: [
            "等待API回复中...",
            "正在处理您的请求...",
            "请稍候...",
            "处理中..."
        ],
        EngineeringTermCategory.COMPRESSING: [
            "正在压缩项目文件...",
            "打包中...",
            "请稍候...",
            "处理中..."
        ],
        EngineeringTermCategory.UPLOADING: [
            "正在上传文件...",
            "传输中...",
            "请稍候...",
            "处理中..."
        ],
        EngineeringTermCategory.ANALYZING: [
            "正在分析项目...",
            "解析中...",
            "请稍候...",
            "处理中..."
        ],
        EngineeringTermCategory.GENERATING: [
            "正在生成README...",
            "撰写中...",
            "请稍候...",
            "处理中..."
        ],
        EngineeringTermCategory.CODING: [
            "正在处理代码...",
            "编码中...",
            "请稍候...",
            "处理中..."
        ],
        EngineeringTermCategory.GENERAL: [
            "处理中...",
            "请稍候...",
            "等待中...",
            "进行中..."
        ]
    }
    
    # Use typing effect for all categories
    category = category or EngineeringTermCategory.GENERAL
    messages = comforting_messages.get(category, comforting_messages[EngineeringTermCategory.GENERAL])
    manager.cycle_typing_messages(messages, interval=3.0)

    try:
        yield manager
    finally:
        manager.stop_typing()
        manager.stop()


def simulate_typing_effect(text: str, delay: float = 0.03):
    """
    Simulate typing effect

    Args:
        text: Text to display
        delay: Delay per character (seconds)
    """
    for i, char in enumerate(text):
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


# Predefined waiting manager instances
analyze_manager = WaitingManager("Analyzing", EngineeringTermCategory.ANALYZING)
compress_manager = WaitingManager("Compressing", EngineeringTermCategory.COMPRESSING)
upload_manager = WaitingManager("Uploading", EngineeringTermCategory.UPLOADING)
api_manager = WaitingManager("API Processing", EngineeringTermCategory.PROCESSING)
generate_manager = WaitingManager("Generating", EngineeringTermCategory.GENERATING)


if __name__ == "__main__":
    # Test code
    print("Testing Waiting Manager with typing effect...")

    # Test 1: Compressing category
    print("\nTest 1: Compressing category")
    with waiting_context("Compressing", category=EngineeringTermCategory.COMPRESSING) as manager:
        time.sleep(5)

    # Test 2: Uploading category
    print("\nTest 2: Uploading category")
    with waiting_context("Uploading", category=EngineeringTermCategory.UPLOADING) as manager:
        time.sleep(5)

    # Test 3: Processing category (API)
    print("\nTest 3: Processing category")
    with waiting_context("API Processing", category=EngineeringTermCategory.PROCESSING) as manager:
        time.sleep(5)

    # Test 4: Direct typing effect
    print("\nTest 4: Direct typing effect")
    simulate_typing_effect("Generating README documentation... Please wait...")

    print("\nAll tests completed!")