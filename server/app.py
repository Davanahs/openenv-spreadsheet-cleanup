import sys
import os

# Add the parent directory to the Python path so it can import our core code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
