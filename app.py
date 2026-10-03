#!/usr/bin/env python3
"""
Dev API Play House - Entrypoint Runner
"""
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.server import run_server

if __name__ == "__main__":
    if "--cli" in sys.argv:
        # Remove --cli from argv and delegate to headless CI runner
        sys.argv.remove("--cli")
        from backend.cli.runner import run_cli
        run_cli()
    else:
        from backend.server import run_server
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        run_server(port=port, host=host)
