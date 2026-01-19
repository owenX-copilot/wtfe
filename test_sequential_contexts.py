#!/usr/bin/env python3
"""Test sequential waiting contexts"""

import sys
import time
sys.path.insert(0, '.')

from wtfe_online.waiting_manager import waiting_context, EngineeringTermCategory

print("Testing sequential contexts...")
print("Phase 1: Compression")
with waiting_context("Compressing", category=EngineeringTermCategory.COMPRESSING) as manager:
    time.sleep(1)
    manager.update("Creating archive...")
    time.sleep(0.5)

print("Phase 2: Upload")
with waiting_context("Uploading", category=EngineeringTermCategory.UPLOADING) as manager:
    time.sleep(1)
    manager.update("Uploading file...")
    time.sleep(0.5)

print("Phase 3: API Processing")
with waiting_context("API Processing", category=EngineeringTermCategory.PROCESSING) as manager:
    time.sleep(1)
    manager.update("Analyzing...")
    time.sleep(0.5)

print("All phases done.")