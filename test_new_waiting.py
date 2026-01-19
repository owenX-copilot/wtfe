#!/usr/bin/env python3
"""Test new waiting manager"""

import sys
import time
sys.path.insert(0, '.')

from wtfe_online.waiting_manager import waiting_context, EngineeringTermCategory

print("Testing new waiting manager...")
print("This should show a spinner with changing messages on a single line.")

with waiting_context("Testing", category=EngineeringTermCategory.PROCESSING) as manager:
    time.sleep(3)
    manager.update("Custom message")
    time.sleep(2)

print("Test completed.")