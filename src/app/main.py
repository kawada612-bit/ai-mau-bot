
import uvicorn
from src.app.server import app

def main() -> None:
    # Run the application using Uvicorn
    # "src.app.server:app" refers to the 'app' object in src/app/server.py
    uvicorn.run("src.app.server:app", host="0.0.0.0", port=8080, reload=True)

if __name__ == "__main__":
    main()
