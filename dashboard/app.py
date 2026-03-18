from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import datetime

app = Flask(__name__)
# Enable CORS for standard routes
CORS(app)
# Enable CORS for WebSockets so the frontend can connect perfectly
socketio = SocketIO(app, cors_allowed_origins="*")

# State to hold latest metrics
latest_metrics = {
    "cpu": 0.0,
    "memory": 0.0,
    "latency": 0.0,
    "status": 200,
    "container_state": "running"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    """ The Healer AI Agent will POST data here every 500ms - 2s """
    global latest_metrics
    try:
        data = request.json
        if data:
            # Update state
            latest_metrics["cpu"] = data.get("cpu", latest_metrics["cpu"])
            latest_metrics["memory"] = data.get("memory", latest_metrics["memory"])
            latest_metrics["latency"] = data.get("latency", latest_metrics["latency"])
            latest_metrics["status"] = data.get("status", latest_metrics["status"])
            latest_metrics["container_state"] = data.get("container_state", latest_metrics["container_state"])
            
            # Immediately Broadcast the new metrics to all connected Browsers
            socketio.emit('metrics_update', latest_metrics)
            
            # If the Healer sent a specific log event (e.g. "Healing Started"), broadcast it
            event_log = data.get("log_msg")
            if event_log:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                socketio.emit('healer_event', {"time": timestamp, "msg": event_log})
                
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# When a user opens the dashboard, send them the current state instantly
@socketio.on('connect')
def handle_connect():
    socketio.emit('metrics_update', latest_metrics)
    socketio.emit('healer_event', {
        "time": datetime.datetime.now().strftime("%H:%M:%S"), 
        "msg": "[SYSTEM] Dashboard UI connected to Command Center. Ready."
    })

if __name__ == '__main__':
    # Using SocketIO run instead of app.run
    socketio.run(app, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
