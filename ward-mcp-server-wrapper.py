#!/usr/bin/env python3
"""
Simple wrapper for Ward MCP Server
"""
import sys
import os

# Add src to path to import ward_security
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ward_security.mcp_server import main

if __name__ == "__main__":
    main()