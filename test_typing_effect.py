#!/usr/bin/env python3
"""
Test typing effect stability
"""
import sys
import time
sys.path.insert(0, '.')

from wtfe_online.waiting_manager import waiting_context, EngineeringTermCategory

print("Testing typing effect stability...")
print("This will simulate 10 seconds of waiting with different categories.")
print("Watch for smooth typing and backspace effects.\n")

# Test each category briefly
categories = [
    ("Compressing", EngineeringTermCategory.COMPRESSING),
    ("Uploading", EngineeringTermCategory.UPLOADING),
    ("Processing", EngineeringTermCategory.PROCESSING),
    ("Analyzing", EngineeringTermCategory.ANALYZING),
]

for title, category in categories:
    print(f"\n--- Testing {title} ---")
    with waiting_context(title, category=category) as manager:
        time.sleep(3)  # Short wait to see a few cycles

print("\n\nTest completed. Check for:")
print("1. Smooth typing (no missing characters)")
print("2. Complete backspace effect (no leftover characters)")
print("3. No random characters or 'A' appearing")
print("4. No spinner or engineering terms")
print("5. Clean line clearing between messages")