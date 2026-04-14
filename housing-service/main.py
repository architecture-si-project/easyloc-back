import os

from housing_app import create_app
from dotenv import load_dotenv
from flask_cors import CORS


load_dotenv()

app = create_app()
CORS(app)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_value = os.environ.get("DEBUG", os.environ.get("FLASK_DEBUG", "False"))
    debug = str(debug_value).strip().lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=port, debug=debug)