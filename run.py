import os
import sys

# Ensure CampusCare-AI directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from backend import create_app

app = create_app()

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    print("\n=======================================================")
    print("  [*] CampusCare AI - Production/Dev Server Running!  ")
    print(f"  Host: {host} | Port: {port}                         ")
    print(f"  Health API: http://{host}:{port}/api/health        ")
    print("=======================================================\n")
    app.run(host=host, port=port, debug=False)
