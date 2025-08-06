#!/usr/bin/env python3

import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting backend server on port 8000...")
    uvicorn.run("app.main_demo:app", host="127.0.0.1", port=8001, reload=True)