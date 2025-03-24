import uvicorn
from app.api.api import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)  # Add override=True

# Get configuration from environment variables
host = os.getenv("API_HOST", "127.0.0.1")
port = int(os.getenv("API_PORT", "8010"))  # Hardcoded default

if __name__ == "__main__":
    print(f"Starting API server at http://{host}:{port} (ENV: {os.getenv('API_PORT')})")
    uvicorn.run(
        "app.api.api:app",
        host=host,
        port=port,
        reload=False  # Disable auto-reload to prevent port conflicts
    )