#!/usr/bin/env python
"""
Test runner for the reorganized test structure
"""
import subprocess
import sys
from pathlib import Path


def run_tests_by_component(component=None):
    """Run tests for a specific component or all tests"""

    test_directories = {
        "ai": "tests/ai_service",
        "meeting": "tests/meeting_service",
        "voice": "tests/voice_service",
        "users": "tests/users",
        "utils": "tests/utils",
    }

    if component and component in test_directories:
        test_dir = test_directories[component]
        print(f"Running tests for {component} component from {test_dir}")

        # Get all test files in the directory
        test_files = list(Path(test_dir).glob("test_*.py"))

        if not test_files:
            print(f"No test files found in {test_dir}")
            return

        print(f"Found {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  - {test_file}")

        # Run each test file
        for test_file in test_files:
            print(f"\n{'='*50}")
            print(f"Running: {test_file}")
            print("=" * 50)

            try:
                result = subprocess.run(
                    [sys.executable, str(test_file)], capture_output=False, text=True
                )
                if result.returncode != 0:
                    print(f"❌ Test failed: {test_file}")
                else:
                    print(f"✅ Test passed: {test_file}")
            except Exception as e:
                print(f"❌ Error running {test_file}: {e}")

    elif component is None:
        print("Running all tests...")
        for comp_name, test_dir in test_directories.items():
            print(f"\n{'='*60}")
            print(f"RUNNING {comp_name.upper()} TESTS")
            print("=" * 60)
            run_tests_by_component(comp_name)

    else:
        print(f"Unknown component: {component}")
        print(f"Available components: {', '.join(test_directories.keys())}")


def list_available_tests():
    """List all available tests in the new structure"""
    print("Available tests in reorganized structure:")
    print("=" * 50)

    test_directories = [
        "tests/ai_service",
        "tests/meeting_service",
        "tests/voice_service",
        "tests/users",
        "tests/utils",
    ]

    total_tests = 0
    for test_dir in test_directories:
        test_files = list(Path(test_dir).glob("test_*.py"))
        total_tests += len(test_files)

        print(f"\n{test_dir}:")
        if test_files:
            for test_file in sorted(test_files):
                print(f"  - {test_file.name}")
        else:
            print("  (no test files)")

    print(f"\nTotal test files: {total_tests}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            list_available_tests()
        elif command in ["ai", "meeting", "voice", "users", "utils"]:
            run_tests_by_component(command)
        elif command == "all":
            run_tests_by_component(None)
        else:
            print("Usage:")
            print("  python run_tests.py list          - List all available tests")
            print("  python run_tests.py all           - Run all tests")
            print("  python run_tests.py ai            - Run AI service tests")
            print("  python run_tests.py meeting       - Run meeting service tests")
            print("  python run_tests.py voice         - Run voice service tests")
            print("  python run_tests.py users         - Run user tests")
            print("  python run_tests.py utils         - Run utility tests")
    else:
        list_available_tests()
