from flask import Flask, render_template, jsonify
import json
import os
import subprocess
import threading

app = Flask(__name__)

# Get absolute path to the directory containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Data is two levels up or in the same folder depending on structure, let's look in the parent folder
LEADS_PATH = os.path.join(BASE_DIR, "..", "leads.json")
# If not found there, handle gracefully or check current dir
if not os.path.exists(LEADS_PATH):
    # Fallback to creating a dummy file if needed for the app to start
    LEADS_PATH = os.path.join(BASE_DIR, "leads.json")
    if not os.path.exists(LEADS_PATH):
        with open(LEADS_PATH, "w") as f:
            json.dump([], f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/discover", methods=["POST"])
def discover():
    def run_scout():
        try:
            # Execute the main.py script in the parent directory
            subprocess.run(["python", "../main.py"], check=True)
        except Exception as e:
            print(f"Scout execution failed: {e}")

    # Run discovery in a background thread to avoid blocking Flask
    thread = threading.Thread(target=run_scout)
    thread.start()
    return jsonify({"status": "Discovery started in background"}), 202


@app.route("/api/leads")
def get_leads():
    if os.path.exists(LEADS_PATH):
        try:
            with open(LEADS_PATH, "r") as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify([])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    print(f"Dashboard starting on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
