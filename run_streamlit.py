import streamlit.web.cli as stcli
import os
import sys

if __name__ == "__main__":
    sys.argv = [
        "streamlit", "run", 
        os.path.join(os.path.dirname(__file__), "app", "ui", "streamlit_app.py"),
        "--server.port=8510",  # Changed from 8502 to 8510
        "--server.address=127.0.0.1"
    ]
    sys.exit(stcli.main())