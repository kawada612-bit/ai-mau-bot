
from flask import Flask
from threading import Thread
from src.core.logger import setup_logger

logger = setup_logger(__name__)

app = Flask('')

@app.route('/')
def home() -> str:
    return "I'm alive"

def run() -> None:
    # Disable flask banners
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host='0.0.0.0', port=8080)

def start_server() -> None:
    t = Thread(target=run, daemon=True)
    t.start()
    logger.info("🌍 Keep-Alive Server started on port 8080")
