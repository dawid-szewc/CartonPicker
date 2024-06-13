from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import argparse
import json
import subprocess

# Load configurations
with open("data/params.json") as file:
    g_params = json.load(file)

# Flask
app = Flask(__name__)
CORS(app)  # allow foreign origin


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/gray", methods=["PUT"])
def update_gray():
    with open("data/params.json") as file:
        params = json.load(file)
    params["gray"] = request.json
    g_params["gray"] = request.json

    with open("/home/pi/params.json", "w") as file:
        json.dump(params, file)
    return jsonify(request.json)


@app.route("/api/threshold", methods=["PUT"])
def update_threshold():
    with open("data/params.json") as file:
        params = json.load(file)
    params["threshold"] = request.json
    g_params["threshold"] = request.json

    with open("/home/pi/params.json", "w") as file:
        json.dump(params, file)
    return jsonify(request.json)


@app.route("/api/params", methods=["GET"])
def get_params():
    with open("data/params.json") as file:
        params = json.load(file)
    return jsonify(params)


@app.route("/api/cardboard_data", methods=["GET"])
def cardboardManager():
    with open("data/cardboard_data.json") as file:
        params = json.load(file)
    return jsonify(params)


@app.route("/api/action", methods=["POST"])
def do_action():
    action = request.json.get("action")
    if action == "restart":
        subprocess.run(["supervisorctl", "stop", "camera"])
        subprocess.run(["reboot"])
    elif action == "poweroff":
        subprocess.run(["supervisorctl", "stop", "camera"])
        subprocess.run(["poweroff"])
    elif action == "program":
        subprocess.run(["supervisorctl", "restart", "camera"])
    elif action == "update":
        subprocess.run(["git", "pull"])
        subprocess.run(["./runme.sh"])
    return jsonify(request.json)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i", "--ip", type=str, required=True, help="IP address of the device"
    )
    ap.add_argument(
        "-o",
        "--port",
        type=int,
        required=True,
        help="Ephemeral port number of the server (1024 to 65535)",
    )
    ap.add_argument("-r", "--runlevel", type=int, default=1, help="Runlevel")
    args = vars(ap.parse_args())
    app.run(
        host=args["ip"],
        port=args["port"],
        debug=True,
        threaded=True,
        use_reloader=False,
    )
