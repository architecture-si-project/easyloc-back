import os

from housing_app import create_app
from dotenv import load_dotenv


load_dotenv()

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = bool(os.environ.get("DEBUG", False))
    app.run(host="0.0.0.0", port=port, debug=debug)