#!/usr/bin/env python3
"""
Waiting Manager Module

Provides elegant waiting effects for operations with uncertain duration.
Uses simple spinner with single-line text updates.
"""

import sys
import time
import random
import threading
from typing import Optional, List, Callable, Any
from contextlib import contextmanager
from enum import Enum


class EngineeringTermCategory(Enum):
    """Categories of engineering terms"""
    GENERAL = "general"
    CODING = "coding"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    UPLOADING = "uploading"
    COMPRESSING = "compressing"
    GENERATING = "generating"


class WaitingManager:
    """Waiting Manager Class with simple spinner"""

    # Engineering terms database - like Claude Code's vibe
    ENGINEERING_TERMS = {
        EngineeringTermCategory.GENERAL: [
            "vibing", "processing", "working", "thinking", "computing",
            "analyzing", "calculating", "optimizing", "synthesizing",
            "evaluating", "processing", "computing", "rendering",
            "compiling", "executing", "initializing", "loading",
            "preparing", "configuring", "setting up", "warming up",
            "syncing", "validating", "verifying", "checking",
            "monitoring", "observing", "scanning", "parsing",
            "indexing", "cataloging", "organizing", "structuring"
        ],
        EngineeringTermCategory.CODING: [
            "coding", "programming", "developing", "engineering",
            "architecting", "designing", "implementing", "debugging",
            "refactoring", "optimizing", "profiling", "testing",
            "documenting", "commenting", "formatting", "linting",
            "building", "compiling", "packaging", "deploying",
            "integrating", "merging", "branching", "committing",
            "pushing", "pulling", "cloning", "forking"
        ],
        EngineeringTermCategory.PROCESSING: [
            "processing", "computing", "calculating", "analyzing",
            "synthesizing", "transforming", "converting", "parsing",
            "serializing", "deserializing", "encoding", "decoding",
            "encrypting", "decrypting", "compressing", "decompressing",
            "filtering", "sorting", "searching", "matching",
            "comparing", "validating", "verifying", "authenticating",
            "authorizing", "logging", "tracking", "monitoring"
        ],
        EngineeringTermCategory.ANALYZING: [
            "analyzing", "scanning", "parsing", "indexing",
            "cataloging", "classifying", "categorizing", "tagging",
            "labeling", "annotating", "summarizing", "extracting",
            "abstracting", "condensing", "simplifying", "clarifying",
            "interpreting", "understanding", "comprehending",
            "evaluating", "assessing", "rating", "scoring",
            "ranking", "prioritizing", "filtering", "selecting"
        ],
        EngineeringTermCategory.UPLOADING: [
            "uploading", "transferring", "sending", "transmitting",
            "streaming", "pushing", "syncing", "backing up",
            "archiving", "storing", "saving", "caching",
            "buffering", "queuing", "scheduling", "dispatching",
            "routing", "forwarding", "redirecting", "proxy-ing",
            "load balancing", "scaling", "replicating", "mirroring"
        ],
        EngineeringTermCategory.COMPRESSING: [
            "compressing", "archiving", "packaging", "bundling",
            "zipping", "tarring", "gzipping", "bzipping",
            "minifying", "uglifying", "obfuscating", "encrypting",
            "encoding", "serializing", "streamlining", "optimizing",
            "deduplicating", "consolidating", "aggregating",
            "merging", "combining", "joining", "concatenating"
        ],
        EngineeringTermCategory.GENERATING: [
            "generating", "creating", "producing", "manufacturing",
            "fabricating", "constructing", "building", "assembling",
            "composing", "writing", "drafting", "editing",
            "revising", "polishing", "refining", "perfecting",
            "finalizing", "completing", "finishing", "wrapping up",
            "delivering", "presenting", "displaying", "showing"
        ]
    }

    # Action suffixes
    ACTION_SUFFIXES = [
        "data", "files", "content", "code", "project",
        "system", "network", "database", "cache", "memory",
        "process", "thread", "task", "job", "request",
        "response", "payload", "stream", "buffer", "queue",
        "log", "metric", "stat", "report", "document",
        "readme", "config", "settings", "environment", "context"
    ]

    # Spinner frames
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, title: str = "Processing", category: EngineeringTermCategory = None):
        """
        Initialize waiting manager

        Args:
            title: Waiting indicator title
            category: Engineering term category
        """
        self.title = title
        self.category = category or EngineeringTermCategory.GENERAL
        self._running = False
        self._spinner_thread = None
        self._current_message = ""
        self._spinner_index = 0
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _get_random_term(self) -> str:
        """Get a random engineering term"""
        terms = self.ENGINEERING_TERMS.get(self.category, self.ENGINEERING_TERMS[EngineeringTermCategory.GENERAL])
        return random.choice(terms)

    def _get_random_suffix(self) -> str:
        """Get a random action suffix"""
        return random.choice(self.ACTION_SUFFIXES)

    def _generate_engineering_message(self) -> str:
        """Generate a random engineering-style message"""
        term = self._get_random_term()
        suffix = self._get_random_suffix()

        # Sometimes add adjectives or adverbs
        adjectives = ["", "efficiently ", "quickly ", "carefully ", "thoroughly ", "systematically "]
        adverb = random.choice(adjectives)

        # Format variations
        formats = [
            f"{adverb}{term} {suffix}",
            f"{term} {suffix} {adverb}",
            f"{term.upper()} {suffix.upper()}",
            f"{term}... {suffix}...",
            f"{term}-{suffix}",
        ]

        return random.choice(formats)

    def _spinner_loop(self):
        """Spinner animation loop"""
        while not self._stop_event.is_set():
            with self._lock:
                spinner_char = self.SPINNER_FRAMES[self._spinner_index % len(self.SPINNER_FRAMES)]
                display_text = f"{spinner_char} {self.title}: {self._current_message}"
                sys.stdout.write('\r' + display_text + ' ' * 10)  # Clear extra characters
                sys.stdout.flush()
                self._spinner_index += 1
            time.sleep(0.1)

    def start(self, message: str = None, total: Optional[int] = None):
        """
        Start waiting indicator

        Args:
            message: Initial message
            total: Total steps (if known) - ignored for simple spinner
        """
        self._running = True
        self._stop_event.clear()
        self._current_message = message or self._generate_engineering_message()
        
        # Start spinner thread
        self._spinner_thread = threading.Thread(target=self._spinner_loop, daemon=True)
        self._spinner_thread.start()

    def update(self, message: str = None, progress: Optional[float] = None):
        """
        Update waiting status

        Args:
            message: New message
            progress: Progress (between 0.0 and 1.0) - ignored
        """
        if not self._running:
            return
        
        with self._lock:
            if message:
                self._current_message = message
            else:
                self._current_message = self._generate_engineering_message()

    def stop(self, message: str = "Done!"):
        """
        Stop waiting indicator

        Args:
            message: Completion message
        """
        self._running = False
        self._stop_event.set()
        if self._spinner_thread:
            self._spinner_thread.join(timeout=0.5)
        
        # Clear the line and show completion message
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.write(f"✓ {message}\n")
        sys.stdout.flush()

    def cycle_random_messages(self, interval: float = 1.5, count: Optional[int] = None):
        """
        Cycle through random engineering messages

        Args:
            interval: Message switch interval (seconds)
            count: Number of messages to cycle (None for infinite)
        """
        self._stop_cycling_event = threading.Event()
        self._cycling_thread = None

        def cycle():
            messages_generated = 0
            while not self._stop_cycling_event.is_set():
                if count is not None and messages_generated >= count:
                    break

                message = self._generate_engineering_message()
                self.update(message)
                messages_generated += 1
                # Use wait with timeout to allow immediate stop
                if self._stop_cycling_event.wait(timeout=interval):
                    break

        self._cycling_thread = threading.Thread(target=cycle, daemon=True)
        self._cycling_thread.start()

    def stop_cycling(self):
        """Stop message cycling"""
        if hasattr(self, '_stop_cycling_event'):
            self._stop_cycling_event.set()
        if self._cycling_thread:
            self._cycling_thread.join(timeout=0.5)


@contextmanager
def waiting_context(title: str = "Processing", message: str = None,
                   category: EngineeringTermCategory = None):
    """
    Context manager for elegant waiting indicators

    Args:
        title: Waiting indicator title
        message: Initial message
        category: Engineering term category

    Yields:
        WaitingManager: Waiting manager instance
    """
    manager = WaitingManager(title, category)
    manager.start(message)
    
    # Start cycling random messages for better visual feedback
    manager.cycle_random_messages(interval=1.5)

    try:
        yield manager
    finally:
        manager.stop_cycling()
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
    print("Testing Waiting Manager...")

    # Test 1: Basic waiting with random messages
    print("\nTest 1: Basic waiting with engineering terms")
    with waiting_context("Testing", category=EngineeringTermCategory.CODING) as manager:
        time.sleep(3)
        manager.update()  # Random message
        time.sleep(2)
        manager.update("Custom message override")
        time.sleep(1)

    # Test 2: Message cycling
    print("\nTest 2: Cycling through engineering terms")
    manager = WaitingManager("Cycling Test", EngineeringTermCategory.PROCESSING)
    manager.start("Starting cycle...")
    manager.cycle_random_messages(interval=1.0, count=8)
    time.sleep(8)
    manager.stop_cycling()
    manager.stop("Cycle complete")

    # Test 3: Different categories
    print("\nTest 3: Different engineering categories")
    categories = [
        ("Coding", EngineeringTermCategory.CODING),
        ("Analyzing", EngineeringTermCategory.ANALYZING),
        ("Generating", EngineeringTermCategory.GENERATING),
        ("Uploading", EngineeringTermCategory.UPLOADING),
    ]

    for title, category in categories:
        with waiting_context(title, category=category) as manager:
            time.sleep(2)
            manager.update()
            time.sleep(1)

    # Test 4: Typing effect
    print("\nTest 4: Typing effect")
    simulate_typing_effect("Generating README documentation... Please wait...")