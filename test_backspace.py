#!/usr/bin/env python3
"""
Test backspace effect specifically
"""
import sys
import time
sys.path.insert(0, '.')

from wtfe_online.waiting_manager import WaitingManager, EngineeringTermCategory

print("Testing backspace effect...")
print("Will display 'Testing...' then backspace it completely.")
print("Watch for complete erasure.\n")

manager = WaitingManager("Test", EngineeringTermCategory.GENERAL)
manager.start()

# Use a single message to test
messages = ["Testing backspace effect..."]
manager.cycle_typing_messages(messages, interval=2.0)

# Let it run for 5 seconds to see multiple cycles
time.sleep(5)

manager.stop_typing()
manager.stop("Test complete")

print("\nIf you saw the message typed out, held, then completely erased, the test passes.")