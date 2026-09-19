import os
import sys

# Ensure CampusCare-AI directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from backend import create_app

app = create_app()

if __name__ == "__main__":
    print("\n=======================================================")
    print("  [*] CampusCare AI - Hackathon MVP Platform Running!  ")
    print("  Local URL: http://127.0.0.1:5000                     ")
    print("  Health API: http://127.0.0.1:5000/api/health         ")
    print("=======================================================\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
