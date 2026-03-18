from flask import Flask, jsonify, render_template
from flask_cors import CORS
import json
import time
import os
import threading

app = Flask(__name__)
CORS(app)

# Track memory leak globally
memory_hog = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/browse')
def browse():
    try:
        with open('data.json', 'r') as f:
            movies = json.load(f)
    except Exception as e:
        movies = []
    
    categories = {}
    for movie in movies:
        cat = movie.get('category', 'Others')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(movie)

    return render_template('browse.html', categories=categories, movies=movies)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/health_check')
def health_check():
    return 'OK', 200

@app.route('/stress_cpu')
def stress_cpu():
    # Blocks the main thread heavily to make the UI freeze/janky
    end_time = time.time() + 15 
    while time.time() < end_time:
        _ = [i * i for i in range(50000)]
    return jsonify({"status": "stressed"}), 200

@app.route('/stress_memory')
def stress_memory():
    global memory_hog
    try:
        memory_hog.append(' ' * 100 * 10**6) 
        return jsonify({"status": "stressed", "current_size_mb": len(memory_hog)*100}), 200
    except MemoryError:
        os._exit(1)

@app.route('/lag')
def lag():
    time.sleep(15)
    return jsonify({"status": "lagged"}), 200

@app.route('/kill')
def crash():
    def kill():
        time.sleep(0.5)
        os._exit(1)
    threading.Thread(target=kill).start()
    return jsonify({"status": "crashing"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
