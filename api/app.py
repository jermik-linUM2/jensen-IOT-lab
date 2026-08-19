from flask import Flask, jsonify, request, render_template
import os
import socket
import logging

from db import (
    device_exists,
    get_devices,
    get_measurements,
    get_latest_measurement,
    get_measurements_for_device,
    insert_measurement,
)
from validation import validate_measurement
from cache import get_latest_from_cache, set_latest_in_cache

app = Flask(__name__)

app.logger.setLevel(logging.INFO)

APP_VERSION = os.getenv("APP_VERSION", "v1")
POD_NAME = socket.gethostname()


@app.get("/")
def dashboard():
    return render_template("index.html", version=APP_VERSION, pod=POD_NAME)


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": APP_VERSION,
        "pod": POD_NAME,
    }), 200


@app.get("/devices")
def devices():
    return jsonify(get_devices()), 200


@app.get("/measurements")
def measurements():
    return jsonify(get_measurements()), 200


@app.get("/devices/<device_id>/latest")
def latest(device_id):

    if device_exists(device_id):
        cached_data = get_latest_from_cache(device_id)
        if cached_data is not None:
            app.logger.info(f"CACHE HIT för {device_id}")
            return jsonify(cached_data), 200
        
        app.logger.info(f"CACHE MISS för {device_id}")
        data = get_latest_measurement(device_id)
        if not data:
            return jsonify({"error": f"no measurement found for '{device_id}'"}), 404
        set_latest_in_cache(device_id, data)
        return jsonify(data), 200
    
    else:
        return jsonify({"error": f"device '{device_id}' does not exist"}), 404

    return jsonify({
        "message": "TODO: implementera latest measurement",
        "deviceId": device_id
    }), 501


@app.get("/devices/<device_id>/measurements")
def device_history(device_id):

    if device_exists(device_id):
        data = get_measurements_for_device(device_id)
        return jsonify(data), 200

    else:
        return jsonify({"error": f"device '{device_id}' does not exist"}), 404

    return jsonify({
        "message": "TODO: implementera device history",
        "deviceId": device_id
    }), 501


@app.post("/measurements")
def create_measurement():
    data = request.get_json(silent=True) or {}
    errors = validate_measurement(data)

    if errors:
        print(f"INVALID measurement from {data.get('deviceId', 'unknown')}: {errors}")
        return jsonify({"errors": errors}), 400

    device_id = data.get("deviceId")
    if device_exists(device_id):
        rv = insert_measurement(data)

        if rv:
            set_latest_in_cache(device_id, data)
            return jsonify({"message": "row succesfully inserted", "data": rv}), 201
        else:
            return jsonify({"error": "faild to insert row"}), 500

    else:
        return jsonify({"error": f"device '{device_id}' does not exist"}), 400


    print(f"VALID measurement received: {data}")
    return jsonify({"status": "accepted", "measurement": data}), 202


@app.get("/statistics")
def statistics():
    # ⭐ Utmaning:
    # Returnera antal devices, antal measurements, avg temp etc.
    return jsonify({"message": "Optional challenge"}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
