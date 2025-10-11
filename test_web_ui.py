#!/usr/bin/env python3
"""Test script to verify the Kirin Web UI works."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from kirin.web.config import BackendManager

    print("✅ Successfully imported Kirin Web UI components")

    # Test backend manager
    backend_mgr = BackendManager()
    backends = backend_mgr.list_backends()
    print(f"✅ Backend manager working - found {len(backends)} backends")

    # Test available types
    types = backend_mgr.get_available_types()
    print(f"✅ Available backend types: {[t['value'] for t in types]}")

    print("\n🎉 Kirin Web UI is ready to run!")
    print("To start the server, run:")
    print("  python run_web_ui.py")
    print("  or")
    print("  uvicorn kirin.web.app:app --reload --host 0.0.0.0 --port 8000")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
