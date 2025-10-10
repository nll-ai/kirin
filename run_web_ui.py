#!/usr/bin/env python3
"""Simple script to run the Kirin Web UI."""

import uvicorn
from kirin.web.app import app

if __name__ == "__main__":
    # Use random port to avoid conflicts
    import random

    port = random.randint(8001, 8999)

    print(f"🚀 Starting Kirin Web UI on port {port}")
    print(f"📱 Open your browser to: http://localhost:{port}")
    print("🛑 Press Ctrl+C to stop the server")

    uvicorn.run(app, host="0.0.0.0", port=port, reload=True, log_level="info")
