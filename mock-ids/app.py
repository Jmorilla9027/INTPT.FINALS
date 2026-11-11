
from flask import Flask, render_template, jsonify, request

from backend.ids_engine import IDSEngine


# =================================
# FLASK CONFIGURATION
# =================================

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)


# =================================
# INITIALIZE IDS ENGINE
# =================================

ids = IDSEngine()


# =================================
# MAIN DASHBOARD
# =================================

@app.route("/")
def dashboard():

    return render_template("index.html")


# =================================
# START MONITORING
# =================================

@app.route("/api/start", methods=["POST"])
def start_ids():

    ids.start()

    return jsonify({
        "status": "success",
        "message": "IDS monitoring started"
    })


# =================================
# PAUSE MONITORING
# =================================

@app.route("/api/pause", methods=["POST"])
def pause_ids():

    ids.pause()

    return jsonify({
        "status": "success",
        "message": "IDS monitoring paused"
    })


# =================================
# STOP MONITORING
# =================================

@app.route("/api/stop", methods=["POST"])
def stop_ids():

    ids.stop()

    return jsonify({
        "status": "success",
        "message": "IDS monitoring stopped"
    })


# =================================
# GET DASHBOARD STATISTICS
# =================================

@app.route("/api/stats", methods=["GET"])
def statistics():

    return jsonify(
        ids.get_statistics()
    )


# =================================
# GET NETWORK EVENTS
# =================================

@app.route("/api/events", methods=["GET"])
def network_events():

    try:

        after_id = max(
            0,
            int(request.args.get("after", 0))
        )

    except (ValueError, TypeError):

        return jsonify({
            "error": "Invalid event ID"
        }), 400

    return jsonify({
        "events": ids.get_events(after_id)
    })


# =================================
# HEALTH CHECK
# =================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "online",
        "application": "Sentinel Mock IDS"
    })


# =================================
# START WEB SERVER
# =================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("       SENTINEL MOCK IDS v3.0")
    print("======================================")
    print()
    print("IDS Web Server is starting...")
    print()
    print("Dashboard:")
    print("http://127.0.0.1:5000")
    print()
    print("API:")
    print("http://127.0.0.1:5000/api/health")
    print()
    print("======================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True
    )
