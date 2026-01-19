#!/usr/bin/env python3
"""
Test script for waiting manager with typing effect
"""
import sys
import time
sys.path.insert(0, '.')

from wtfe_online.waiting_manager import (
    waiting_context,
    EngineeringTermCategory,
    simulate_typing_effect
)

print("Testing waiting manager with typing effect...")

# Test 1: Compressing category
print("\n1. Testing COMPRESSING category:")
with waiting_context("Compressing", category=EngineeringTermCategory.COMPRESSING) as manager:
    time.sleep(5)
    manager.update("Custom update")
    time.sleep(2)

# Test 2: Uploading category
print("\n2. Testing UPLOADING category:")
with waiting_context("Uploading", category=EngineeringTermCategory.UPLOADING) as manager:
    time.sleep(5)

# Test 3: Processing category (API)
print("\n3. Testing PROCESSING category:")
with waiting_context("API Processing", category=EngineeringTermCategory.PROCESSING) as manager:
    time.sleep(5)

# Test 4: General category
print("\n4. Testing GENERAL category:")
with waiting_context("Processing", category=EngineeringTermCategory.GENERAL) as manager:
    time.sleep(5)

print("\nAll tests completed!")