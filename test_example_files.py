#!/usr/bin/env python3
"""
Simple script to test all example files using the wtfe_file module.
This script uses proper imports and doesn't modify the original code.
"""

import os
import sys
import json
import glob

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the wtfe_file module properly
from wtfe_file import get_extractor


def test_single_file(filepath):
    """Test a single file and return results."""
    try:
        print(f"\nTesting: {filepath}")
        print("=" * 60)

        # Get extractor
        extractor = get_extractor(filepath)

        # Extract facts
        fact = extractor.extract()

        # Print basic info
        print(f"Language: {fact.language}")
        print(f"Filename: {fact.filename}")
        print(f"Confidence: {fact.confidence:.2f}")

        # Print roles
        if fact.roles:
            print(f"Roles: {[role.name for role in fact.roles]}")

        # Print structures summary
        print("\nStructures summary:")
        for key, value in fact.structures.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")

        # Print signals summary
        print("\nSignals summary:")
        for key, value in fact.signals.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_all_example_files():
    """Test all files in the example directory."""
    example_dir = os.path.join(os.path.dirname(__file__), "example")

    if not os.path.exists(example_dir):
        print(f"Example directory not found: {example_dir}")
        return

    # Get all files in example directory (excluding subdirectories)
    files = []
    for ext in ['*.py', '*.js', '*.ts', '*.java', '*.html', '*.json',
                '*.yaml', '*.yml', '*.md', '*.ipynb', 'Dockerfile', 'Makefile']:
        files.extend(glob.glob(os.path.join(example_dir, ext)))

    # Also look for specific filenames
    specific_files = ['docker-compose.yml', 'k8s_deployment.yaml']
    for filename in specific_files:
        filepath = os.path.join(example_dir, filename)
        if os.path.exists(filepath):
            files.append(filepath)

    # Remove duplicates and sort
    files = sorted(set(files))

    print(f"Found {len(files)} files to test in example directory")
    print("=" * 60)

    success_count = 0
    failure_count = 0

    for filepath in files:
        if test_single_file(filepath):
            success_count += 1
        else:
            failure_count += 1

    print("\n" + "=" * 60)
    print(f"Test Summary:")
    print(f"  Total files: {len(files)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failure_count}")
    print("=" * 60)

    return failure_count == 0


if __name__ == "__main__":
    print("Testing all example files with WTFE file analysis")
    print("=" * 60)

    success = test_all_example_files()

    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)