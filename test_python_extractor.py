#!/usr/bin/env python3
"""
Test script for Python extractor functionality.
"""

import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wtfe_file.extractors.python import PythonExtractor


def test_python_extractor():
    """Test Python extractor with a simple Python file."""

    # Create a temporary Python file for testing
    python_code = '''
"""Test Python module for extractor testing."""

import os
import sys
from typing import List, Dict

# Global variables
API_KEY = "test_key"
config = {"debug": True}

class TestClass:
    """A test class."""

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}"

def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two numbers."""
    return a + b

def main():
    """Main entry point."""
    print("Hello from main!")
    obj = TestClass("World")
    print(obj.greet())
    print(f"Sum: {calculate_sum(5, 3)}")

if __name__ == "__main__":
    main()
'''

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_code)
        temp_file = f.name

    try:
        print(f"Testing Python extractor with file: {temp_file}")
        print("=" * 60)

        # Create extractor instance
        extractor = PythonExtractor(temp_file)

        # Extract facts
        fact = extractor.extract()

        # Print results
        print(f"Language: {fact.language}")
        print(f"Filename: {fact.filename}")
        print(f"Path: {fact.path}")
        print(f"Confidence: {fact.confidence:.2f}")

        print("\nRoles:")
        for role in fact.roles:
            print(f"  - {role}")

        print("\nStructures:")
        for key, value in fact.structures.items():
            print(f"  {key}: {value}")

        print("\nSignals:")
        for key, value in fact.signals.items():
            print(f"  {key}: {value}")

        # Verify expected results
        print("\n" + "=" * 60)
        print("Verification:")

        # Check structures
        expected_classes = ["TestClass"]
        expected_functions = ["__init__", "greet", "calculate_sum", "main"]

        if all(cls in fact.structures.get("classes", []) for cls in expected_classes):
            print("✓ Classes extracted correctly")
        else:
            print(f"✗ Classes mismatch. Expected: {expected_classes}, Got: {fact.structures.get('classes', [])}")

        if all(func in fact.structures.get("functions", []) for func in expected_functions):
            print("✓ Functions extracted correctly")
        else:
            print(f"✗ Functions mismatch. Expected: {expected_functions}, Got: {fact.structures.get('functions', [])}")

        # Check signals
        expected_imports = ["os", "sys", "typing"]
        if all(imp in fact.signals.get("imports", []) for imp in expected_imports):
            print("✓ Imports extracted correctly")
        else:
            print(f"✗ Imports mismatch. Expected: {expected_imports}, Got: {fact.signals.get('imports', [])}")

        if fact.signals.get("entry_point"):
            print("✓ Entry point detected correctly")
        else:
            print("✗ Entry point not detected")

        # Check roles
        if "ENTRY_POINT" in [role.name for role in fact.roles]:
            print("✓ ENTRY_POINT role assigned")
        else:
            print("✗ ENTRY_POINT role not assigned")

        print("\n" + "=" * 60)
        print("Python extractor test completed!")

    finally:
        # Clean up temporary file
        os.unlink(temp_file)


def test_can_handle():
    """Test can_handle method."""
    print("Testing can_handle method:")
    print("=" * 60)

    test_cases = [
        ("test.py", True),
        ("test.pyw", True),
        ("test.js", False),
        ("test.txt", False),
        ("/path/to/file.py", True),
        ("C:\\path\\to\\file.py", True),
    ]

    for filepath, expected in test_cases:
        result = PythonExtractor.can_handle(filepath)
        status = "✓" if result == expected else "✗"
        print(f"{status} {filepath:30} -> Expected: {expected}, Got: {result}")

    print("=" * 60)


if __name__ == "__main__":
    print("Testing Python Extractor")
    print("=" * 60)

    test_can_handle()
    print()
    test_python_extractor()