#!/usr/bin/env python3
"""Quick UI testing script - automated testing without manual clicking."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_quick_validation():
    """Run quick validation tests."""
    print("🚀 Kirin Web UI Quick Validation\n")

    try:
        from tests.web_ui.test_web_ui_integration import test_web_ui_quick_validation

        return test_web_ui_quick_validation()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_integration_tests():
    """Run full integration tests."""
    print("🧪 Running Full Integration Tests\n")

    try:
        import subprocess

        # Run pytest on the web UI tests
        result = subprocess.run(
            [
                "pixi",
                "run",
                "python",
                "-m",
                "pytest",
                "tests/web_ui/test_web_ui_integration.py",
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False


def run_workflow_test():
    """Run the complete user workflow test."""
    print("🧪 Running Complete User Workflow Test\n")

    try:
        from tests.web_ui.test_user_workflow import run_complete_workflow_test

        return run_complete_workflow_test()
    except Exception as e:
        print(f"❌ Error running workflow test: {e}")
        return False


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            success = run_integration_tests()
        elif sys.argv[1] == "--workflow":
            success = run_workflow_test()
        else:
            print("Usage: python test_ui.py [--full|--workflow]")
            sys.exit(1)
    else:
        success = run_quick_validation()

    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
