import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run(
        "app.main_demo:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )