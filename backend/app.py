from flask import Flask, jsonify, render_template
import json, os

app = Flask(__name__)

# Get the project root
root = os.path.dirname(os.path.dirname(__file__))

def load_json(filename):
    path = os.path.join(root, "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Serve the frontend
@app.route("/")
def index():
    return render_template("index.html")

# API routes
@app.route("/jobs")
def get_jobs():
    return jsonify(load_json("jobs.json"))

@app.route("/companies")
def get_companies():
    return jsonify(load_json("companies.json"))

@app.route("/locations")
def get_locations():
    return jsonify(load_json("locations.json"))

if __name__ == "__main__":
    app.run(debug=True)
