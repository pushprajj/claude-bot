#!/usr/bin/env python3

import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main_demo import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, reload=False)